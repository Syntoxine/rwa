import json
import logging
import os
from enum import Enum

from ld_eventsource import SSEClient
from ld_eventsource.config import ConnectStrategy
from supabase import Client, create_client

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

API_URL = "https://www.nationstates.net/api/move+founding+cte+member+endo"
USER_AGENT = os.getenv("NS_USER_AGENT")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL is None or SUPABASE_KEY is None:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY must be set in environment variables."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class EventType(Enum):
    # EJECT = "was ejected from"
    # EJECT_BANNED = "was ejected and banned"
    MOVE = "relocated from"
    FOUNDING = "was founded"
    FOUNDING_REFOUND = "was refounded"
    CTE = "ceased to"
    MEMBER_APPLY = "applied to"
    MEMBER_ADMIT = "was admitted"
    MEMBER_RESIGN = "resigned from"
    MEMBER_DELEGATE = "became WA"
    MEMBER_DELEGATE_SEIZED = "seized"
    MEMBER_DELEGATE_LOST = "lost WA"
    ENDO = "endorsed"
    ENDO_WITHDRAW = "withdrew its"

    @staticmethod
    def get_event_type(event_str: str):
        parts = event_str.split()
        for event_type in EventType:
            if " ".join(parts[1:]).startswith(event_type.value):
                return event_type
        raise ValueError(f"Unknown event type in string: {event_str}")


PARAMETER_POSITIONS: dict[EventType, tuple[int, ...]] = {
    # EventType.EJECT: (4, 6),
    # EventType.EJECT_BANNED: (6, 8),
    EventType.MOVE: (3, 5),
    EventType.FOUNDING: (4,),
    EventType.FOUNDING_REFOUND: (4,),
    EventType.CTE: (5,),
    EventType.MEMBER_APPLY: (),
    EventType.MEMBER_ADMIT: (),
    EventType.MEMBER_RESIGN: (),
    EventType.MEMBER_DELEGATE: (5,),
    EventType.MEMBER_DELEGATE_SEIZED: (5, 9),
    EventType.MEMBER_DELEGATE_LOST: (6,),
    EventType.ENDO: (2,),
    EventType.ENDO_WITHDRAW: (5,),
}


class NSEvent:
    def __init__(self, event_str: str):
        parts = event_str.split()
        self.nation = parts[0][2:-2]
        self.event_type = EventType.get_event_type(event_str)
        self.parameters = [
            parts[i][2:-2] for i in PARAMETER_POSITIONS.get(self.event_type, ())
        ]

    def __repr__(self) -> str:
        return f"<NSEvent nation='{self.nation}' event_type={self.event_type}{f' parameters={self.parameters}' if self.parameters else ''}>"

    def update(self) -> None:
        try:
            match self.event_type:
                case EventType.ENDO | EventType.ENDO_WITHDRAW:
                    endorsements_query = (
                        supabase.table("nations")
                        .select("name, endorsements")
                        .eq("name", self.parameters[0])
                        .execute()
                    )
                    try:
                        endorsements = endorsements_query.data[0]["endorsements"] or []
                    except Exception as e:
                        logger.error(
                            f"Error fetching endorsements for nation {self.parameters[0]}: {e}"
                        )
                        endorsements = []

                    match self.event_type:
                        case EventType.ENDO:
                            endorsements.append(self.nation)
                            payload = {"endorsements": endorsements}
                        case EventType.ENDO_WITHDRAW:
                            endorsements.remove(self.nation)
                            payload = {"endorsements": endorsements}

                    supabase.table("nations").update(payload).eq(
                        "name", self.parameters[0]
                    ).execute()

                case EventType.FOUNDING | EventType.FOUNDING_REFOUND:
                    supabase.table("nations").insert(
                        {"name": self.nation, "region": self.parameters[0]}
                    ).execute()

                case EventType.MEMBER_APPLY:
                    pass  # No action needed for MEMBER_APPLY

                case EventType.MEMBER_DELEGATE_SEIZED:
                    supabase.table("nations").update({"wa_delegate": True}).eq(
                        "name", self.nation
                    ).execute()
                    supabase.table("nations").update({"wa_delegate": False}).eq(
                        "name", self.parameters[1]
                    ).execute()

                case _:
                    match self.event_type:
                        case EventType.MOVE:
                            payload = {"region": self.parameters[1]}
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
                        "name", self.nation
                    ).execute()
        except Exception as e:
            logger.error(f"Error updating {self}: {e}")


def consume() -> None:
    sse_client = SSEClient(
        connect=ConnectStrategy.http(url=API_URL, headers={"User-Agent": USER_AGENT})
    )

    for event in sse_client.events:
        ns_event = NSEvent(json.loads(event.data)["str"])
        logger.info(ns_event)
        ns_event.update()


if __name__ == "__main__":
    consume()
