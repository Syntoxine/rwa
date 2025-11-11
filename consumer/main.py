import asyncio
import logging
import logging.handlers

import db
from ns_event import NSEvent, EventType
from channels import Channel, get_channels
from consumer import consume

fmt = "[{asctime}] [{levelname:<8}] {name} - {message}"
dt_fmt = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(format=fmt, datefmt=dt_fmt, style="{", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("consumer").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

handler = logging.handlers.RotatingFileHandler(
    filename="../logs/consumer.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)

formatter = logging.Formatter(fmt, dt_fmt, style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)
logging.getLogger().addHandler(handler)

channels = get_channels()
logger.info(
    f"Loaded {len(channels)} channel{'s' if len(channels) > 1 else ''} from config: {[channel.name for channel in channels]}"
)


def match(event: NSEvent, channel: Channel) -> bool:
    bucket = event.event_type.get_bucket()
    region = db.get_region(event.nation)
    region2 = event.parameters[0] if event.event_type == EventType.MOVE else None
    if region in channel.regions or region2 in channel.regions or not channel.regions:
        if channel.endotarting:
            if (
                (
                    event.event_type == EventType.MOVE
                    and not db.get_wa_status(event.nation)
                )
                or event.event_type != EventType.MEMBER_ADMIT
                or region not in channel.regions
            ):
                return False
            return True
        elif bucket in channel.buckets or not channel.buckets:
            return True
    return False


async def main():
    logger.info("Listening for events...")
    for event in consume():
        for channel in filter(lambda c: c.match(event), channels):
            await channel.send(str(event))


if __name__ == "__main__":
    asyncio.run(main())
