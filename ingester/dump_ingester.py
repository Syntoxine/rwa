import logging
import logging.handlers
import os
import time
from datetime import datetime, timezone

import sans
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
logging.getLogger().addHandler(handler)

USER_AGENT = os.getenv("NS_USER_AGENT")

if USER_AGENT is None:
    raise ValueError("NS_USER_AGENT environment variable not set")

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
    sans.set_agent(USER_AGENT) # type: ignore

    #### EXTRACT AND PARSE DUMP ####
    start_time = time.time()
    logger.info("Parsing dump...")

    dump_time = datetime.now(timezone.utc).replace(
        hour=5, minute=30, second=0, microsecond=0
    )

    nations: list[dict[str, str | bool | list[str] | datetime]] = []
    with sans.stream("GET", sans.NationsDump()) as response:
        for nation in response.iter_xml():
            sans.indent(nation)

            current_nation = {}
            for child in nation:
                match child.tag:
                    case "UNSTATUS":
                        match child.text:
                            case "WA Delegate":
                                current_nation["wa_delegate"] = True
                                current_nation["wa_member"] = True
                            case "WA Member":
                                current_nation["wa_member"] = True
                            case _:
                                current_nation["wa_delegate"] = False
                                current_nation["wa_member"] = False
                    case "ENDORSEMENTS":
                        current_nation["endorsements"] = (
                            list(map(to_snake_case, child.text.split(",")))
                            if child.text
                            else []
                        )
                    case "NAME" | "FULLNAME" | "REGION" | "FLAG":
                        current_nation[child.tag.lower()] = (
                            child.text if child.text else ""
                        )

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

    logger.info(f"Parsed {len(nations)} nations. ({time.time() - start_time:.2f}s)")

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
