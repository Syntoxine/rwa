import logging
import logging.handlers
import os

import discord
from discord import app_commands
from discord.ext import commands

import db

logger = logging.getLogger("discord")
handler = logging.handlers.RotatingFileHandler(
    filename="../logs/bot.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)

dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name} - {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def to_snake_case(name: str) -> str:
    return name.lower().replace(" ", "_")


def to_title_case(name: str) -> str:
    return name.title().replace("_", " ")


def get_md_nation_link(name: str) -> str:
    return f"[{to_title_case(name)}](https://nationstates.net/nation={to_snake_case(name)})"


def get_md_region_link(name: str) -> str:
    return f"[{to_title_case(name)}](https://nationstates.net/region={to_snake_case(name)})"


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", None)
if DISCORD_TOKEN is None:
    logger.critical("DISCORD_TOKEN environment variable not set, exiting")
    raise ValueError("DISCORD_TOKEN environment variable not set")

description = """Real-time World Assembly - a project by Nova Aohr

For inquiries, message @syntoxine
[Github](https://github.com/Syntoxine/rwa)
[Nova Aohr on NationStates](https://nationstates.net/nation=nova_aohr)"""

intents = discord.Intents.default()
intents.message_content = True

MY_GUILD = discord.Object(1033103537271488542)


class Arwa(commands.Bot):
    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


arwa = Arwa(command_prefix=":", intents=intents, description=description)


@arwa.event
async def on_ready():
    assert arwa.user is not None
    logger.info(f"Logged in as {arwa.user} (ID: {arwa.user.id})")


@arwa.tree.command()
@app_commands.describe(nation="The name of your nation")
async def tart(interaction: discord.Interaction, nation: str):
    """Use this command to get a list of nations your nation can endorse in your region."""
    await interaction.response.defer()
    
    nation = to_snake_case(nation)
    if not db.get_wa_status(nation):
        await interaction.response.send_message(
            f"{to_title_case(nation)} is not a WA member, and can't endorse anyone!"
        )
        return
    endorsable_nations = db.get_endorsable_nations(nation)
    if not endorsable_nations:
        await interaction.response.send_message(
            f"{to_title_case(nation)} has endorsed everyone it could in its region!"
        )
    else:
        await interaction.response.send_message(
            f"{to_title_case(nation)} has not endorsed the following nations: {', '.join(get_md_nation_link(n) for n in endorsable_nations)}"
        )


arwa.run(DISCORD_TOKEN)
