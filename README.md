# Real-time World Assembly
This tool uses the NationStates SSE API to construct a realtime snapshot of current nations' WA Status and more.
## Features
- Daily dump ingestion
- Accurately tracks the following buckets from the happenings api: `move`, `founding`, `cte`, `member`, `endo`
- Ability to post events from any of these buckets to 1 or more discord webhooks.
## Guide
### Setup
The background db used is hosted by Supabase. I have encountered many issues with postgres and have tried to not use it, but any one willing to fix my code is welcome. As such, you will need to create a Supabase project to use this.
The followings environment variables must be defined. To do this, create a `.env` file in the same directory as the `compose.yaml` file containing the following variables:
| *Variable*      | *Description*                                                                   |
| --------------- | ------------------------------------------------------------------------------- |
| `NS_USER_AGENT` | A user agent string that will be used for requests to the NationStates API      |
| `SUPABASE_URL`  | Supabase project URL                                                            |
| `SUPABASE_KEY`  | Supabase service API key                                                        |
| `UPDATE_DB`     | Either `"true"` or `"false"`, whether events should update the database or not. |

To get the consumer running, run `docker compose up -d consumer`. To populate your database, you can ingest the daily dump, which updates at around 5:30 AM UTC each day, with `docker compose up ingester`.
### Webhooks
To configure channels to which to post events to, create a `channels.toml` file.
```toml
[Example]
name = "Example Channel"
webhook_url = "https://discord.com/api/webhooks/<number>/<token>"
regions = ["the_south_pacific"]
buckets = ["move", "founding", "cte", "member", "endo"]
```
You can add as many different channels as you like, the only required property is the `webhook_url`. The `regions` and `buckets` function as filters, only events from a region in `regions` or a bucket in `buckets` will be sent to the channel.
## TODO
- Implement personalized db queries through a discord bot