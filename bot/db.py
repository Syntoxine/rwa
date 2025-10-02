import logging
import os

from supabase import Client, create_client

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL is None or SUPABASE_KEY is None:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY must be set in environment variables."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_region(nation: str) -> str | None:
    try:
        response = (
            supabase.table("nations").select("region").eq("name", nation).execute()
        )
        if response.data:
            return response.data[0]["region"]
    except Exception as e:
        logger.error(f"Error fetching region for nation {nation}: {e}")


def get_wa_status(nation: str) -> bool | None:
    try:
        nation_query = (
            supabase.table("nations").select("wa_member").eq("name", nation).execute()
        )
        if nation_query.data:
            return nation_query.data[0]["wa_member"]
    except Exception as e:
        logger.error(f"Error fetching WA status for nation {nation}: {e}")
        return False


def get_endorsable_nations(nation: str) -> list[str] | None:
    try:
        response = (
            supabase.table("nations")
            .select("name")
            .not_.eq("name", nation)
            .eq("region", get_region(nation))
            .eq("wa_member", True)
            .not_.contains("endorsements", [nation])
            .execute()
        )
        if response.data:
            return list(map(lambda x: x["name"], response.data))
    except Exception as e:
        logger.error(f"Error fetching endorsable nations for {nation}: {e}")
