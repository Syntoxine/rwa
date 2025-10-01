import logging
import os

from supabase import Client, create_client

from ns_event import EventType, NSEvent

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL is None or SUPABASE_KEY is None:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY must be set in environment variables."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def event_update(event: NSEvent) -> None:
    try:
        match event.event_type:
            case EventType.ENDO | EventType.ENDO_WITHDRAW:
                endorsements_query = (
                    supabase.table("nations")
                    .select("name, endorsements")
                    .eq("name", event.parameters[0])
                    .execute()
                )
                try:
                    endorsements = endorsements_query.data[0]["endorsements"] or []
                except Exception as e:
                    logger.error(
                        f"Error fetching endorsements for nation {event.parameters[0]}: {e}"
                    )
                    endorsements = []

                match event.event_type:
                    case EventType.ENDO:
                        endorsements.append(event.nation)
                        payload = {"endorsements": endorsements}
                    case EventType.ENDO_WITHDRAW:
                        endorsements.remove(event.nation)
                        payload = {"endorsements": endorsements}

                supabase.table("nations").update(payload).eq(
                    "name", event.parameters[0]
                ).execute()

            case EventType.FOUNDING | EventType.FOUNDING_REFOUND:
                supabase.table("nations").upsert(
                    {
                        "name": event.nation,
                        "region": event.parameters[0],
                        "active": True,
                    }
                ).execute()

            case EventType.MEMBER_APPLY:
                pass  # No action needed for MEMBER_APPLY

            case EventType.MEMBER_DELEGATE_SEIZED:
                supabase.table("nations").update({"wa_delegate": True}).eq(
                    "name", event.nation
                ).execute()
                supabase.table("nations").update({"wa_delegate": False}).eq(
                    "name", event.parameters[1]
                ).execute()

            case _:
                match event.event_type:
                    case EventType.MOVE:
                        payload = {"region": event.parameters[1]}
                    case EventType.CTE:
                        payload = {"active": False}
                    case EventType.MEMBER_ADMIT:
                        payload = {"wa_member": True}
                    case EventType.MEMBER_RESIGN:
                        payload = {"wa_member": False}
                    case EventType.MEMBER_DELEGATE:
                        payload = {"wa_delegate": True}
                    case EventType.MEMBER_DELEGATE_LOST:
                        payload = {"wa_delegate": False}

                supabase.table("nations").update(payload).eq(
                    "name", event.nation
                ).execute()
    except Exception as e:
        logger.error(f"Error updating {event}: {e}")

def get_region(nation: str) -> str | None:
    try:
        nation_query = (
            supabase.table("nations").select("region").eq("name", nation).execute()
        )
        if nation_query.data:
            return nation_query.data[0]["region"]
    except Exception as e:
        logger.error(f"Error fetching region for nation {nation}: {e}")