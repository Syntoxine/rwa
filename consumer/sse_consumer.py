import json
import logging
import os
from collections.abc import Generator

from ld_eventsource import SSEClient
from ld_eventsource.config import ConnectStrategy

import db
from ns_event import NSEvent

logger = logging.getLogger(__name__)

API_URL = "https://www.nationstates.net/api/move+founding+cte+member+endo"
USER_AGENT = os.getenv("NS_USER_AGENT")


def consume() -> Generator[NSEvent]:
    sse_client = SSEClient(
        connect=ConnectStrategy.http(url=API_URL, headers={"User-Agent": USER_AGENT})
    )

    for event in sse_client.events:
        ns_event = NSEvent(json.loads(event.data)["str"])
        logger.info(ns_event)
        db.event_update(ns_event)

        yield ns_event
