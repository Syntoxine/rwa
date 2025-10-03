import logging
import os

import psycopg

logger = logging.getLogger(__name__)

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


def get_region(nation: str) -> str | None:
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT region FROM nations WHERE (name = %s)", (nation,))
            region = cur.fetchone()
            if region is not None:
                return region[0]
    return None


def get_wa_status(nation: str) -> bool:
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT wa_member FROM nations WHERE (name = %s)", (nation,))
            wa_member = cur.fetchone()
            if wa_member is not None:
                return wa_member[0]
    return False

def get_endorsements(nation: str) -> list[str]:
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT endorsements FROM nations WHERE (name = %s)", (nation,))
            endorsements = cur.fetchone()
            if endorsements is not None:
                return endorsements[0]
    return []


def get_endorsable_nations(nation: str) -> list[str]:
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT name FROM nations
                WHERE name != %s
                AND region = %s
                AND wa_member = TRUE
                AND %s != ALL(endorsements)""",
                (nation, get_region(nation), nation),
            )
            return [row[0] for row in cur.fetchall()]
