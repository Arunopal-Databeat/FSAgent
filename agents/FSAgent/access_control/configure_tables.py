import logging
import time

from ..tools.db_connection import get_connection

logger = logging.getLogger("fsagent")

REFRESH_INTERVAL_SECONDS = 24 * 60 * 60

ALL_CLIENTS_NO_RESTRICTIONS_EMAILS = [
    "aditya@databeat.io",
    "hamrazudheen.hakkim@databeat.io",
    "user",
    "arunopal.dutta@databeat.io",
    "ashok.ganapam@mediamint.com",
    "sanjay.baliga@mediamint.com",
    "paul.neumann@mediamint.com",
    "rajeev@mediamint.com",
    "aashay@mediamint.com",
    "ashok@databeat.io",
    "ramesh.dacha@mediamint.com",
    "neelima@mediamint.com",
    "ilan@taktical.co",
    "pratyush@databeat.io",
    "derek@taktical.co",
    "ilan.nass@mediamint.com",
    "derek.rubinstein@mediamint.com",
    "anshu.kumar@mediamint.com",
    "jason@mediamint.com",
    "sivamani.koppisetti@mediamint.com",
    "mindie.kaplan@mediamint.com",
    "michael.mayer@mediamint.com",
    "jitendra.satpute@mediamint.com",
    "thakur.singh@mediamint.com",
    "sumit.sharma@databeat.io",
]

_cache = {
    "data": None,
    "all_clients": None,
    "checked_at": None,
    "write_counters": None,
}


def _fetch_write_counters(cur):
    cur.execute(
        """
        SELECT n_tup_ins, n_tup_upd, n_tup_del
        FROM pg_stat_user_tables
        WHERE relname = 'financial_clientportfoliomapping'
        """
    )
    row = cur.fetchone()
    return tuple(row) if row else None


def _fetch_email_client_access(cur):
    cur.execute(
        """
        SELECT "Client Name", "Portfolio Lead Email", "Client Partner Email"
        FROM "financial_clientportfoliomapping"
        WHERE "Client Name" IS NOT NULL AND ("Portfolio Lead Email" IS NOT NULL OR "Client Partner Email" IS NOT NULL)
        """
    )
    clients_by_email = {}
    all_clients = set()
    for client_name, portfolio_lead_email, client_partner_email in cur.fetchall():
        all_clients.add(client_name)
        for email in (portfolio_lead_email, client_partner_email):
            if email:
                clients_by_email.setdefault(email, set()).add(client_name)

    access = {email: sorted(clients) for email, clients in clients_by_email.items()}
    access.update({email: ["ALL CLIENTS NO RESTRICTIONS"] for email in ALL_CLIENTS_NO_RESTRICTIONS_EMAILS})
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
        logger.info("financial_clientportfoliomapping unchanged, skipping rebuild")
        return

    _cache["data"], _cache["all_clients"] = _fetch_email_client_access(cur)
    _cache["write_counters"] = write_counters
    logger.info(
        "financial_clientportfoliomapping refreshed, %d emails mapped",
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


