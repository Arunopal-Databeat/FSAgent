import json
import re
from urllib.parse import parse_qs

import jwt
from starlette.responses import JSONResponse

# Access JWTs come from the dashboard backend (shared JWT_SECRET). Expired must
# be a 401: the frontend only refreshes its token and retries on 401.

_USER_IN_PATH = re.compile(r"/users/([^/]+)")
_BODY_PATHS = ("/run", "/run_sse")  # user id is in the JSON body here


class JWTAuthMiddleware:
    def __init__(self, app, secret):
        self.app, self.secret = app, secret

    async def __call__(self, scope, receive, send):
        is_http = scope["type"] == "http"
        if scope["type"] not in ("http", "websocket") or (
            is_http and (scope["method"] == "OPTIONS" or scope["path"] == "/health")
        ):
            return await self.app(scope, receive, send)

        async def reject(status, detail):
            if not is_http:
                return await send({"type": "websocket.close", "code": 1008})
            headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
            await JSONResponse({"detail": detail}, status, headers)(scope, receive, send)

        auth = dict(scope["headers"]).get(b"authorization", b"").decode()
        try:
            claims = jwt.decode(
                auth.removeprefix("Bearer "), self.secret, algorithms=["HS256"],
                options={"require": ["exp", "email"]},
            )
        except jwt.ExpiredSignatureError:
            return await reject(401, "Token has expired.")
        except jwt.InvalidTokenError:
            return await reject(401, "Invalid token.")
        if claims.get("type") != "access":  # a refresh token must not open the API
            return await reject(401, "Invalid token.")

        # Every user id the request names (path, query, body) must be the token's owner.
        query = parse_qs(scope["query_string"].decode())
        ids = _USER_IN_PATH.findall(scope["path"]) + query.get("userId", []) + query.get("user_id", [])
        if is_http and scope["method"] == "POST" and scope["path"] in _BODY_PATHS:
            body = b""
            while True:
                message = await receive()
                body += message.get("body", b"")
                if not message.get("more_body"):
                    break
            try:
                data = json.loads(body)
            except ValueError:
                data = {}
            ids += [str(data[k]) for k in ("userId", "user_id") if isinstance(data, dict) and k in data]
            real_receive, chunks = receive, iter([{"type": "http.request", "body": body}])

            async def receive():  # hand the body we consumed on to the endpoint
                return next(chunks, None) or await real_receive()

        if any(i.lower() != claims["email"].lower() for i in ids):
            return await reject(403, "Token does not match the requested user.")
        await self.app(scope, receive, send)
