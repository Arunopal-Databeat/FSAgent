import os
import threading

import psycopg2

DB_CONNECTION_MODE = os.environ.get("DB_CONNECTION_MODE", "ssh_tunnel")

DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

_KEEPALIVE_KWARGS = dict(
    keepalives=1,
    keepalives_idle=30,
    keepalives_interval=10,
    keepalives_count=5,
)

_tunnel = None
_connection = None
_lock = threading.Lock()


def _get_direct_connection():
    global _connection
    if _connection is None or _connection.closed:
        _connection = psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10,
            **_KEEPALIVE_KWARGS,
        )
    return _connection


def _get_tunneled_connection():
    global _tunnel, _connection
    from sshtunnel import SSHTunnelForwarder

    if _tunnel is None or not _tunnel.is_active:
        _tunnel = SSHTunnelForwarder(
            (os.environ["DB_SSH_HOST"], int(os.environ["DB_SSH_PORT"])),
            ssh_username=os.environ["DB_SSH_USERNAME"],
            ssh_pkey=os.environ["DB_SSH_PKEY"],
            remote_bind_address=("localhost", int(os.environ["DB_REMOTE_PORT"])),
        )
        _tunnel.start()
        _connection = None

    if _connection is None or _connection.closed:
        _connection = psycopg2.connect(
            host="localhost",
            port=_tunnel.local_bind_port,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10,
            **_KEEPALIVE_KWARGS,
        )
    return _connection


def get_connection():
    if _connection is not None and not _connection.closed:
        return _connection
    with _lock:
        if DB_CONNECTION_MODE == "direct":
            return _get_direct_connection()
        return _get_tunneled_connection()
