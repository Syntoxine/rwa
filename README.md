# Real-time World Assembly
---
This tool uses the NationStates SSE API to construct a realtime snapshot of current nations' WA Status and more.
## Features
- Daily dump ingestion
- Accurately tracks the following buckets from the happenings api: `move`, `founding`, `cte`, `member`, `endo`
- Ability to post events from any of these buckets to 1 or more discord webhooks.
## Guide
The background db used is hosted by Supabase. I have encountered many issues with postgres and have tried to not use it, but any one willing to fix my code is welcome. As such, you will need to create a Supabase project to use this.
The followings environment variables must be defined. To do this, create a `.env` file in the same directory as the `compose.yaml` file containing the following variables:
| *Variable*      | *Description*                                                                   |
| --------------- | ------------------------------------------------------------------------------- |
| `NS_USER_AGENT` | A user agent string that will be used for requests to the NationStates API      |
| `SUPABASE_URL`  | Supabase project URL                                                            |
| `SUPABASE_KEY`  | Supabase service API key                                                        |
| `UPDATE_DB`     | Either `"true"` or `"false"`, whether events should update the database or not. |
## TODO
- Implement personalized db queries through a discord bot