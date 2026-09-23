import json
import logging
import os

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"), override=True)
os.environ["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"].strip()

from .configure_tables import get_all_clients
import litellm

logger = logging.getLogger("fsagent")

UNIQUE_CLIENTS = sorted(get_all_clients())

_GENERATED_ALIASES_PATH = os.path.join(os.path.dirname(__file__), "generated_client_aliases.json")


def _load_generated_aliases():
    if os.path.exists(_GENERATED_ALIASES_PATH):
        with open(_GENERATED_ALIASES_PATH, "r") as f:
            return json.load(f)
    return {}


def _save_generated_aliases(aliases):
    with open(_GENERATED_ALIASES_PATH, "w") as f:
        json.dump(aliases, f, indent=2, sort_keys=True)

CLIENT_ALIAS = {
    "AdLib Media": "SilentFalcon",
    "Amazon": "AzureBaker",
    "AmpAgency": "GraniteBridge",
    "Anchor Trading": "SwiftOtter",
    "Anoki": "CrimsonTailor",
    "Apartment SEO": "CopperLantern",
    "Attain": "CleverBadger",
    "Audacy": "AmberMiner",
    "Audience Town": "VelvetHarbor",
    "Axonet": "BoldLynx",
    "Bitly": "VioletPilot",
    "BlockThrough": "MarbleSummit",
    "Bonneville": "QuietHeron",
    "BridgeCorp": "ScarletFarmer",
    "Browsi": "CedarComet",
    "Business Insider": "MightyBison",
    "Captify": "CobaltMason",
    "Carlton One": "WillowBeacon",
    "Chewy": "NimbleCobra",
    "Chicory": "EmeraldCobbler",
    "Chubbies": "MapleCompass",
    "Common Good": "FierceRaven",
    "CosBar": "IvorySailor",
    "Cox Automotive": "BirchSextant",
    "Cox Communication": "GentleFox",
    "Criteo": "SlateHunter",
    "CyberRisk Alliance": "AspenRudder",
    "DAX US": "SlyHawk",
    "DanAds": "LavenderSmith",
    "Dealer": "JuniperMast",
    "Diamond Sports Group": "RapidBeaver",
    "Directv": "IndigoWeaver",
    "Dish Purchasing Corporation": "CactusKeel",
    "Disney": "LuckyMongoose",
    "DoorDash": "MaroonCarpenter",
    "Entravision Communications": "PrairieHull",
    "Expedia": "WildTiger",
    "Fanatics Inc.": "TealChef",
    "Forbes": "TundraDeck",
    "Gameloft": "SharpPuma",
    "Good Karma Brands": "CoralPlumber",
    "Goodway Group": "DeltaBow",
    "Gopuff": "CalmOwl",
    "GumGum": "UmberGardener",
    "Hashtag Labs": "RidgeStern",
    "Hashtag Paid": "LoyalMarlin",
    "Hero Digital": "OnyxScribe",
    "Hootsuite": "ValleyAnchor",
    "Hopper": "CuriousGazelle",
    "Infillion/ Gimbal": "SiennaDiver",
    "Inmar": "MeadowTurret",
    "Jamloop": "VividFerret",
    "Jewelers of America": "CyanTrader",
    "LG Ads": "GlacierRampart",
    "MLB": "StormyJackal",
    "Madhive": "MagentaRanger",
    "Magnite": "VolcanoBastion",
    "Majesty Ventures": "SturdyIbis",
    "Marathon Data": "BeigeClerk",
    "Match2One": "ReefCitadel",
    "MediaPlus": "CunningStallion",
    "Mercurius": "OchreWarden",
    "MiQ": "LagoonFortress",
    "Microsoft": "PlayfulViper",
    "Miller Advertising": "RubyButcher",
    "Mozilla": "CoveOutpost",
    "Nativo": "RadiantEgret",
    "Netflix": "BronzeFisher",
    "Netsertive": "FjordLighthouse",
    "New York Times": "FrostyWombat",
    "NextRoll": "SilverHerder",
    "Nextdoor": "MesaPinnacle",
    "Nexxen": "BlazingKestrel",
    "Niantic": "CharcoalVintner",
    "Northstar Travel": "ButteSpire",
    "Paramount": "HiddenDolphin",
    "Pinterest": "PewterBroker",
    "Reach PLC": "PlateauGrotto",
    "Ribeye": "GoldenMantis",
    "Rithum": "TurquoisePainter",
    "Roblox": "SavannaCavern",
    "Rockbot": "FeralCoyote",
    "Samba TV": "SaffronArcher",
    "Samsung India": "OasisHollow",
    "Samsung USA": "JollyWeasel",
    "Scribd": "MauveSurveyor",
    "Seedtag": "DuneThicket",
    "Sports Innovation": "WaryOsprey",
    "Spotify": "RustCartographer",
    "Star Observer": "MarshBramble",
    "StitcherAds": "TranquilCougar",
    "Strategus": "AmethystMiller",
    "StreamVantage": "CanyonNebula",
    "Swiftly": "BriskAntelope",
    "TIME": "SepiaTinker",
    "TLDR Media": "EmberQuartz",
    "TVIQ": "RestlessPeregrine",
    "Techy Scouts": "ChartreuseFletcher",
    "The Advertising Council": "ThunderHorizon",
    "The Athletic": "VigilantNarwhal",
    "The Financial Times": "PeriwinkleCooper",
    "The Kite Factory": "MeteorOrbit",
    "The Washington Post": "SolemnTapir",
    "Thirdwave Systems": "VermilionFalconer",
    "TimeOut (US)": "FrostPalisade",
    "TimeOut (US/UK)": "ZealousSalamander",
    "Townsquare Interactive": "ChestnutFerryman",
    "Townsquare Media": "AuroraVale",
    "TribuneMedia-Nexstar": "SteadyWolverine",
    "Uni Express": "BurgundyShepherd",
    "Vevo": "CinderVault",
    "Viant": "MerryOcelot",
    "VideoAmp": "TangerineForager",
    "WPP Media": "BasaltCairn",
    "WTWH Media": "GrimCaribou",
    "Warner Music Group": "ObsidianTrapper",
    "Waymark": "LichenFord",
    "WestPoint": "RowdyBobcat",
    "Wpromote": "AlabasterForester",
    "Xaxis": "TalusReach",
    "eAccountable": "PlacidErmine",
    "inMarket": "MarigoldCartwright",
}

_generated_aliases = _load_generated_aliases()
CLIENT_ALIAS.update(_generated_aliases)

STALE_ALIASES = sorted(set(CLIENT_ALIAS) - set(UNIQUE_CLIENTS) - {"ALL CLIENTS NO RESTRICTIONS"})
for client in STALE_ALIASES:
    del CLIENT_ALIAS[client]
    _generated_aliases.pop(client, None)

if STALE_ALIASES:
    logger.info(f"STALE_ALIASES removed : {STALE_ALIASES}")
    _save_generated_aliases(_generated_aliases)

MISSING_CLIENTS = sorted(set(UNIQUE_CLIENTS) - set(CLIENT_ALIAS))
MISSING_CLIENTS = sorted(set(MISSING_CLIENTS) - {"ALL CLIENTS NO RESTRICTIONS"})

logger.info(f"MISSING_CLIENTS : {MISSING_CLIENTS}")


def _generate_alias(MISSING_CLIENTS):
    if not MISSING_CLIENTS:
        logger.info("No missing clients")
        return None
    else:
        prompt = (
            f"Generate a unique two-word code name alias for each item in this list : {MISSING_CLIENTS} similar to this : {CLIENT_ALIAS}"
            "Use varied styles across the list: Adjective+Animal, Colour+Job, and unrelated Two-word code names"
            f"Keep each alias exactly two words, no reused word across entries, and no obvious link to the original name. The generated aliases should not match the ones in {CLIENT_ALIAS}"
            "Output one line per client in this exact format: ClientName|ALIAS"
        )
        response = litellm.completion(
            model="anthropic/claude-sonnet-5",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response["choices"][0]["message"]["content"].strip()

        generated = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or "|" not in line:
                continue
            client, alias = line.split("|", 1)
            generated[client.strip()] = alias.strip()

        CLIENT_ALIAS.update(generated)
        _generated_aliases.update(generated)
        _save_generated_aliases(_generated_aliases)
        logger.info(f"New client aliases: {generated}")
        return generated

generated_aliases = _generate_alias(MISSING_CLIENTS)