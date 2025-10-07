import logging
import os
from collections.abc import Generator

import sans

import db
from ns_event import NSEvent

logger = logging.getLogger(__name__)

USER_AGENT = os.getenv("NS_USER_AGENT")


def consume() -> Generator[NSEvent]:

    for event in sans.serversent_events(None, "move", "founding", "cte", "member", "endo"):
        ns_event = NSEvent(event["str"])
        logger.info(ns_event)
        db.event_update(ns_event)

        yield ns_event
