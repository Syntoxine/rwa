import logging
import logging.handlers
import os

import discord
from discord import app_commands
from discord.ext import commands
from discord.interactions import InteractionMessage

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

MY_GUILD = discord.Object(int(os.getenv("DEV_GUILD", 0)))


class Arwa(commands.Bot):
    async def setup_hook(self):
        # Sync the command tree with the guild if in dev mode, else globally
        if MY_GUILD.id != 0:
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
    callback_response = await interaction.response.defer()
    if callback_response is not None:
        interaction_message: InteractionMessage = callback_response.resource # type: ignore
    else:
        return
    
    nation = to_snake_case(nation)
    if not db.get_wa_status(nation):
        await interaction_message.edit(
            content=f"{to_title_case(nation)} is not a WA member, and can't endorse anyone!"
        )
        return
    
    endorsable_nations = db.get_endorsable_nations(nation)
    if not endorsable_nations:
        await interaction_message.edit(
            content=f"{to_title_case(nation)} has endorsed everyone it could in its region!"
        )
    else:
        nations = [f"{get_md_nation_link(n)}#composebutton" for n in endorsable_nations]
        prefix = f"{to_title_case(nation)} has not endorsed the following nations:"
        if len(nations) > 12:
            content = f"{prefix} {', '.join(nations[:12])}, and {len(nations) - 12} more nations ommitted for brevity."
        else:
            content = f"{prefix} {', '.join(nations)}."
        await interaction_message.edit(
            content=content
        )


arwa.run(DISCORD_TOKEN)
