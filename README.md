# Real-time World Assembly
This tool uses the NationStates SSE API to construct a realtime snapshot of current nations' WA Status and more.
## Features
- Daily dump ingestion
- Accurately tracks the following buckets from the happenings api: `move`, `founding`, `cte`, `member`, `endo`
- Ability to post events from any of these buckets to 1 or more discord webhooks.
- Discord bot, with endotarting functionality (`/tart nation: <name>`)
## Guide
### Setup
The followings environment variables must be defined. To do this, create a `.env` file in the same directory as the `compose.yaml` file containing the following variables:
| *Variable*          | *Description*                                                                   |
| ------------------- | ------------------------------------------------------------------------------- |
| `NS_USER_AGENT`     | A user agent string that will be used for requests to the NationStates API      |
| `DISCORD_TOKEN`     | Discord App Token                                                               |
| `UPDATE_DB`         | Either `"true"` or `"false"`, whether events should update the database or not. |
| `POSTGRES_DB`       | PostgreSQL database name                                                        |
| `POSTGRES_USER`     | PostgreSQL user name                                                            |
| `POSTGRES_PASSWORD` | PostgreSQL user password                                                        |

To get the consumer running, run `docker compose up -d consumer`. To populate your database, you can ingest the daily dump, which updates at around 5:30 AM UTC each day, with `docker compose up ingester`. To use the bot, run `docker compose up -d bot`, and enter `/tart nation: <name>` to see which nations you need to endorse. (Slash commands need up to an hour to propagate across servers)
### Discord Webhooks
To configure channels to which to post events to, create a `channels.toml` file.
```toml
[Example]
name = "Example Channel"
webhook_url = "https://discord.com/api/webhooks/<number>/<token>"
regions = ["the_south_pacific"]
buckets = ["move", "founding", "cte", "member", "endo"]

[Example 2]
name = "Example Endotarting Channel"
webhook_url = "https://discord.com/api/webhooks/<number>/<token>"
endotarting = true
regions = ["the_south_pacific"]
```
You can add as many different channels as you like, the only required property is the `webhook_url`. The `regions` and `buckets` function as filters, only events from a region in `regions` or a bucket in `buckets` will be sent to the channel. Adding the `endotarting=true` property will make the channel an endotarting channel, where only events that result in there being someone new to endorse will be shown.
## TODO
- Implement personalized db queries through a discord bot