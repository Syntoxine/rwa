import tomllib
import logging

import discord
import aiohttp

import db
from ns_event import EventType

logger = logging.getLogger(__name__)

USERNAME = "RWA Feed"
AVATAR_URL = "https://files.dussud.org/NovaAohr/2560w1x1.png"


class Channel:
    def __init__(
        self,
        name: str,
        webhook_url: str,
        endotarting: bool = False,
        regions=None,
        buckets=None,
    ):
        self.name = name
        self.url = webhook_url
        self.endotarting = endotarting
        self.regions: list[str] = regions if regions is not None else []
        self.buckets: list[str] = buckets if buckets is not None else []

    @staticmethod
    def read_config() -> list["Channel"]:
        with open("channels.toml", "rb") as f:
            config = tomllib.load(f)
        channels = []
        for channel, settings in config.items():
            if settings.get("webhook_url", None) is None:
                continue
            name = (
                settings.get("name")
                if settings.get("name", None) is not None
                else channel
            )

            channels.append(
                Channel(
                    name=name,
                    webhook_url=settings.get("webhook_url"),
                    endotarting=settings.get("endotarting", False),
                    regions=settings.get("regions", None),
                    buckets=settings.get("buckets", None),
                )
            )
        return channels

    def match(self, event) -> bool:
        """Check if the event matches the channel's filters"""
        bucket = event.event_type.get_bucket()
        region = db.get_region(event.nation)
        region2 = event.parameters[0] if event.event_type == EventType.MOVE else None
        if region in self.regions or region2 in self.regions or not self.regions:
            if self.endotarting:
                if region in self.regions and (
                    (
                        event.event_type == EventType.MOVE
                        and db.get_wa_status(event.nation)
                    )
                    or (event.event_type == EventType.MEMBER_ADMIT)
                ):
                    return True
                return False
            elif bucket in self.buckets or not self.buckets:
                return True
        return False

    async def send(self, content: str):
        """Send the content to the channel's webhook URL"""
        if len(content) > 2000:
            raise ValueError(
                "Content exceeds Discord message length limit of 2000 characters."
            )
        async with aiohttp.ClientSession() as session:
            try:
                webhook = discord.Webhook.from_url(self.url, session=session)
                await webhook.send(
                    content, username=f"{USERNAME} - {self.name}", avatar_url=AVATAR_URL
                )
            except Exception as e:
                logger.error(f"Error sending message in channel [{self.name}]: {e}")


def get_channels() -> list[Channel]:
    return Channel.read_config()
