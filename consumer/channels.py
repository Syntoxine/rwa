import tomllib
import logging

import discord
import aiohttp

logger = logging.getLogger(__name__)

USERNAME = "RWA Feed"
AVATAR_URL = "https://files.dussud.org/NovaAohr/2560w1x1.png"

class Channel:
    def __init__(self, name: str, webhook_url: str, endotarting: bool = False, regions=None, buckets=None):
        self.name = name
        self.url = webhook_url
        self.endotarting = endotarting
        self.regions: list[str] = regions if regions is not None else []
        self.buckets: list[str] = buckets if buckets is not None else []

    @staticmethod
    def read_config() -> list['Channel']:
        with open("channels.toml", "rb") as f:
            config = tomllib.load(f)
        channels = []
        for channel, settings in config.items():
            if settings.get("webhook_url", None) is None:
                continue
            name = settings.get("name") if settings.get("name", None) is not None else channel

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

    async def send(self, content: str):
        async with aiohttp.ClientSession() as session:
            try:
                webhook = discord.Webhook.from_url(self.url, session=session)
                await webhook.send(content, username=f"{USERNAME} - {self.name}", avatar_url=AVATAR_URL)
            except Exception as e:
                logger.error(f"Error sending message in channel [{self.name}]: {e}")

def get_channels() -> list[Channel]:
    return Channel.read_config()