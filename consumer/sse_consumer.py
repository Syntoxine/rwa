import json
import logging
import os
from collections.abc import Generator

from ld_eventsource import SSEClient
from ld_eventsource.config import ConnectStrategy
from supabase import Client, create_client

import db
from ns_event import NSEvent

logger = logging.getLogger(__name__)

API_URL = "https://www.nationstates.net/api/move+founding+cte+member+endo"
USER_AGENT = os.getenv("NS_USER_AGENT")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL is None or SUPABASE_KEY is None:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY must be set in environment variables."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def consume(update_db: bool = False) -> Generator[NSEvent]:
    sse_client = SSEClient(
        connect=ConnectStrategy.http(url=API_URL, headers={"User-Agent": USER_AGENT})
    )

    for event in sse_client.events:
        ns_event = NSEvent(json.loads(event.data)["str"])
        logger.info(ns_event)
        if update_db:
            db.event_update(ns_event)

        yield ns_event
