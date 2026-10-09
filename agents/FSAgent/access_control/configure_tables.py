import logging
import time

from ..tools.db_connection import get_connection

logger = logging.getLogger("fsagent")

REFRESH_INTERVAL_SECONDS = 24 * 60 * 60

_cache = {
    "data": None,
    "all_clients": None,
    "checked_at": None,
    "write_counters": None,
}


def _fetch_write_counters(cur):
    cur.execute(
        """
        SELECT relname, n_tup_ins, n_tup_upd, n_tup_del
        FROM pg_stat_user_tables
        WHERE relname IN ('financial_clientportfoliomapping', 'authentication_alloweduser')
        """
    )
    rows = cur.fetchall()
    return tuple(sorted(rows)) if rows else None


def _fetch_full_access_emails(cur):
    cur.execute(
        """
        SELECT email FROM "authentication_alloweduser" WHERE user_type = 'admin'
        """
    )
    return [row[0] for row in cur.fetchall()]


def _fetch_email_client_access(cur):
    cur.execute(
        """
        SELECT "Client Name", "Portfolio Lead Email", "Client Partner Email", "Operational Group"
        FROM "financial_clientportfoliomapping"
        WHERE "Client Name" IS NOT NULL AND ("Portfolio Lead Email" IS NOT NULL OR "Client Partner Email" IS NOT NULL)
        """
    )
    clients_by_email = {}
    operational_group_by_client = {}
    all_clients = set()
    for client_name, portfolio_lead_email, client_partner_email, operational_group in cur.fetchall():
        all_clients.add(client_name)
        operational_group_by_client[client_name] = operational_group
        for email in (portfolio_lead_email, client_partner_email):
            if email:
                clients_by_email.setdefault(email, set()).add(client_name)

    access = {
        email: [{client: operational_group_by_client.get(client)} for client in sorted(clients)]
        for email, clients in clients_by_email.items()
    }
    full_access_emails = _fetch_full_access_emails(cur)
    access.update({email: ["ALL CLIENTS NO RESTRICTIONS"] for email in full_access_emails})
    return access, all_clients


def _refresh_if_needed():
    now = time.time()
    if (
        _cache["data"] is not None
        and _cache["checked_at"] is not None
        and now - _cache["checked_at"] < REFRESH_INTERVAL_SECONDS
    ):
        return

    cur = get_connection().cursor()
    write_counters = _fetch_write_counters(cur)
    _cache["checked_at"] = now

    if _cache["data"] is not None and write_counters == _cache["write_counters"]:
        logger.info("access control tables unchanged, skipping rebuild")
        return

    _cache["data"], _cache["all_clients"] = _fetch_email_client_access(cur)
    _cache["write_counters"] = write_counters
    logger.info(
        "access control tables refreshed, %d emails mapped",
        len(_cache["data"]),
    )


def get_email_client_access():
    _refresh_if_needed()
    return _cache["data"]


def get_all_clients():
    _refresh_if_needed()
    return _cache["all_clients"]


# EMAIL_CLIENT_ACCESS = {
#     **{email: ["ALL CLIENTS NO RESTRICTIONS"] for email in ALL_CLIENTS_NO_RESTRICTIONS_EMAILS},
#     "aditya.g@mediamint.com": [
#         "Attain", "BlockThrough", "Browsi", "Forbes", "Nativo", "Paramount", "Scribd",
#         "TIME", "TimeOut (US)", "TimeOut (US/UK)", "TribuneMedia-Nexstar",
#     ],
#     "anshu.kumar@mediamint.com": [
#         "Chewy", "Diamond Sports Group", "Entravision Communications", "Microsoft",
#         "Rithum", "Samsung India", "Samsung USA",
#     ],
#     "barish.bose@mediamint.com": [
#         "Bonneville", "Miller Advertising", "Wpromote",
#     ],
#     "emmanuel.devanand@mediamint.com": [
#         "Directv", "DoorDash", "Fanatics Inc.", "Nexxen", "eAccountable",
#     ],
#     "maria.chris@mediamint.com": [
#         "Business Insider", "Criteo", "DAX US", "Hashtag Paid", "Madhive", "Mercurius",
#         "MiQ", "Nextdoor", "Roblox", "The Financial Times", "The Washington Post",
#         "WTWH Media",
#     ],
#     "minakshi.behera@mediamint.com": [
#         "Good Karma Brands",
#     ],
#     "paul.neumann@mediamint.com": [
#         "Disney",
#     ],
#     "prudhvi.pramod@mediamint.com": [
#         "Bonneville", "Cox Communication", "Miller Advertising", "Niantic",
#         "Pinterest", "Townsquare Interactive", "Townsquare Media", "Wpromote",
#     ],
#     "rajat.sahgal@mediamint.com": [
#         "Amazon", "Expedia", "Inmar", "Uni Express", "Vevo",
#     ],
#     "ramesh.dacha@mediamint.com": [
#         "Anoki", "Audacy", "Audience Town", "Axonet", "Captify", "Chicory", "Chubbies",
#         "CosBar", "DanAds", "Gameloft", "Gopuff", "GumGum", "Hootsuite",
#         "Jewelers of America", "Marathon Data", "Match2One", "Netsertive", "Reach PLC",
#         "Ribeye", "Rockbot", "Sports Innovation", "Star Observer", "StitcherAds",
#         "StreamVantage", "Swiftly", "TLDR Media", "The Advertising Council",
#         "The Kite Factory", "Thirdwave Systems", "Waymark", "WestPoint",
#     ],
#     "riten.bhatia@mediamint.com": [
#         "BridgeCorp", "Carlton One", "Directv", "DoorDash", "Fanatics Inc.",
#         "Good Karma Brands", "Magnite", "Mozilla", "NextRoll", "Nexxen", "Spotify",
#         "eAccountable",
#     ],
#     "sarah.rose@mediamint.com": [
#         "AdLib Media", "AmpAgency", "Anchor Trading", "Apartment SEO", "Bitly",
#         "Business Insider", "Common Good", "Cox Automotive", "Criteo",
#         "CyberRisk Alliance", "DAX US", "Dealer", "Dish Purchasing Corporation",
#         "Goodway Group", "Hashtag Labs", "Hashtag Paid", "Hero Digital", "Hopper",
#         "Infillion/ Gimbal", "Jamloop", "LG Ads", "MLB", "Madhive", "Majesty Ventures",
#         "MediaPlus", "Mercurius", "MiQ", "Netflix", "New York Times", "Nextdoor",
#         "Northstar Travel", "Roblox", "Samba TV", "Seedtag", "Strategus", "TVIQ",
#         "Techy Scouts", "The Athletic", "The Financial Times", "The Washington Post",
#         "Viant", "VideoAmp", "WPP Media", "WTWH Media", "Warner Music Group", "Xaxis",
#         "inMarket",
#     ],
#     "vishwaa.narasiman@mediamint.com": [
#         "Dish Purchasing Corporation", "Infillion/ Gimbal", "MLB", "TVIQ", "VideoAmp",
#     ],
# }


