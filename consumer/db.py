import logging
import os

import psycopg
from psycopg.sql import SQL, Identifier

from ns_event import EventType, NSEvent

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


def event_update(event: NSEvent) -> None:
    match event.event_type:
        case EventType.ENDO | EventType.ENDO_WITHDRAW:
            endorsements = get_endorsements(event.parameters[0])

            match event.event_type:
                case EventType.ENDO:
                    endorsements.append(event.nation)
                case EventType.ENDO_WITHDRAW:
                    endorsements.remove(event.nation)

            with psycopg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE nations SET endorsements = %s WHERE (name = %s)",
                        (endorsements, event.parameters[0]),
                    )

        case EventType.FOUNDING | EventType.FOUNDING_REFOUND:
            upsert_sql = """INSERT INTO nations (name, region, active)
            VALUES (%s, %s, TRUE)
            ON CONFLICT (name) DO UPDATE SET
            ( region, active ) = (EXCLUDED.region, TRUE);"""
            with psycopg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        upsert_sql,
                        (event.nation, event.parameters[0]),
                    )

        case EventType.MEMBER_APPLY:
            pass  # No action needed for MEMBER_APPLY

        case EventType.MEMBER_DELEGATE_SEIZED:
            with psycopg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE nations SET wa_delegate = FALSE WHERE (name = %s)",
                        (event.parameters[1],),
                    ).execute(
                        "UPDATE nations SET wa_delegate = TRUE WHERE (name = %s)",
                        (event.nation,),
                    )

        case _:
            match event.event_type:
                case EventType.MOVE:
                    payload = ("region", event.parameters[1])
                case EventType.CTE:
                    payload = ("active", False)
                case EventType.MEMBER_ADMIT:
                    payload = ("wa_member", True)
                case EventType.MEMBER_RESIGN:
                    payload = ("wa_member", False)
                case EventType.MEMBER_DELEGATE:
                    payload = ("wa_delegate", True)
                case EventType.MEMBER_DELEGATE_LOST:
                    payload = ("wa_delegate", False)

            with psycopg.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        SQL("UPDATE nations SET {} = %s WHERE (name = %s)").format(
                            Identifier(payload[0])
                        ),
                        (payload[1], event.nation),
                    )


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
