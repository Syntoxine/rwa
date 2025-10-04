import gzip
import logging
import logging.handlers
import os
import time
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

import requests
import psycopg

fmt = "[{asctime}] [{levelname:<8}] {name} - {message}"
dt_fmt = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(format=fmt, datefmt=dt_fmt, style="{", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

handler = logging.handlers.RotatingFileHandler(
    filename="../logs/ingester.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)

dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(fmt, dt_fmt, style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)

DATA_URL = "https://nationstates.net/pages/nations.xml.gz"
USER_AGENT = os.getenv("NS_USER_AGENT")

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

DB_CONFIG = {
    "host": "db",
    "port": 5432,
    "dbname": POSTGRES_DB,
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
}


def to_snake_case(s: str) -> str:
    return s.lower().replace(" ", "_")


def main():
    initial_time = time.time()

    #### DOWNLOAD DUMP ####
    start_time = time.time()
    logger.info("Downloading dump...")

    response = requests.get(DATA_URL, headers={"User-Agent": USER_AGENT}, stream=True)
    response.raise_for_status()

    with open("nations_temp.xml.gz", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    logger.info(f"Dump download complete. ({time.time() - start_time:.2f}s)")

    #### EXTRACT AND PARSE DUMP ####
    start_time = time.time()
    logger.info("Parsing dump...")

    dump_time = datetime.now(timezone.utc).replace(hour=5, minute=30, second=0, microsecond=0)
    nations: list[dict[str, str | bool | list[str] | datetime]] = []
    with gzip.open("nations_temp.xml.gz", "rt", encoding="utf-8") as f:
        context = ET.iterparse(f, events=("start", "end"))
        context = iter(context)
        event, root = next(context)

        current_nation = {}

        for event, elem in context:
            if event == "end":
                if elem.tag == "NATION":
                    nations.append(
                        {
                            "name": to_snake_case(current_nation["name"]),
                            "fullname": current_nation["fullname"],
                            "region": to_snake_case(current_nation["region"]),
                            "wa_member": current_nation["wa_member"],
                            "endorsements": current_nation["endorsements"],
                            "flag": current_nation["flag"],
                            "timestamp": dump_time,
                        }
                    )
                    current_nation = {}
                    elem.clear()

                elif elem.tag in [
                    "NAME",
                    "FULLNAME",
                    "UNSTATUS",
                    "ENDORSEMENTS",
                    "REGION",
                    "FLAG",
                ]:
                    if elem.tag == "UNSTATUS":
                        match elem.text:
                            case "WA Delegate":
                                current_nation["wa_delegate"] = True
                                current_nation["wa_member"] = True
                            case "WA Member":
                                current_nation["wa_member"] = True
                            case _:
                                current_nation["wa_delegate"] = False
                                current_nation["wa_member"] = False
                    elif elem.tag == "ENDORSEMENTS":
                        current_nation["endorsements"] = (
                            list(map(to_snake_case, elem.text.split(",")))
                            if elem.text
                            else []
                        )
                    else:
                        current_nation[elem.tag.lower()] = (
                            elem.text if elem.text else ""
                        )

        root.clear()
    logger.info(f"Parsed {len(nations)} nations. ({time.time() - start_time:.2f}s)")

    # Clean up temp file
    os.remove("nations_temp.xml.gz")

    #### UPDATE DATABASE ####
    logger.info("Updating database...")
    start_time = time.time()

    query = """INSERT INTO nations (name, fullname, region, wa_member, endorsements, flag, updated_at)
                    VALUES (%(name)s, %(fullname)s, %(region)s, %(wa_member)s, %(endorsements)s, %(flag)s, %(timestamp)s)
                    ON CONFLICT (name) DO UPDATE 
                    SET fullname     = EXCLUDED.fullname, 
                        region       = EXCLUDED.region,
                        wa_member    = EXCLUDED.wa_member,
                        endorsements = EXCLUDED.endorsements,
                        flag         = EXCLUDED.flag
                    WHERE nations.updated_at < EXCLUDED.updated_at"""

    try:
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    query,
                    nations,
                )
        logger.info(
            f"Successfully updated nations table with {len(nations)} nations in {time.time() - start_time:.2f} seconds."
        )
    except Exception as e:
        logger.error(f"Error updating database: {e}")

    logger.info(f"All done! ({time.time() - initial_time:.2f}s)")


if __name__ == "__main__":
    main()
