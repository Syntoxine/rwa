import asyncio
import logging
import logging.handlers

from channels import get_channels
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
logging.getLogger().addHandler(handler)

channels = get_channels()
if channels:
    logger.info(
        f"Loaded {len(channels)} channel{'s' if len(channels) > 1 else ''} from config: {[channel.name for channel in channels]}"
    )
else:
    logger.info("No channels loaded.")


async def main():
    logger.info("Listening for events...")
    for event in consume():
        for channel in filter(lambda c: c.match(event), channels):
            await channel.send(str(event))


if __name__ == "__main__":
    asyncio.run(main())
