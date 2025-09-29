import gzip
import logging
import os
import time
import xml.etree.ElementTree as ET
from itertools import batched

import requests
from postgrest import ReturnMethod
from supabase import Client, create_client

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 8192

DATA_URL = "https://nationstates.net/pages/nations.xml.gz"
UA = os.getenv("NS_USER_AGENT")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL is None or SUPABASE_KEY is None:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def to_snake_case(s: str) -> str:
    return s.lower().replace(" ", "_")


def main():
    initial_time = time.time()

    #### DOWNLOAD DUMP ####
    start_time = time.time()
    logger.info("Downloading dump...")

    response = requests.get(DATA_URL, headers={"User-Agent": UA}, stream=True)
    response.raise_for_status()

    with open("nations_temp.xml.gz", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    logger.info(f"Dump download complete. ({time.time() - start_time:.2f}s)")

    #### EXTRACT AND PARSE DUMP ####
    start_time = time.time()
    logger.info("Parsing dump...")

    nations: list[dict[str, str | bool | list[str]]] = []
    with gzip.open("nations_temp.xml.gz", "rt", encoding="utf-8") as f:
        context = ET.iterparse(f, events=("start", "end"))
        context = iter(context)
        event, root = next(context)

        current_nation = {}

        for event, elem in context:
            if event == "end":
                if elem.tag == "NATION":
                    nations.append(
                        {
                            "name": to_snake_case(current_nation["name"]),
                            "fullname": current_nation["fullname"],
                            "region": to_snake_case(current_nation["region"]),
                            "wa_member": current_nation["wa_member"],
                            "endorsements": current_nation["endorsements"],
                            "flag": current_nation["flag"],
                        }
                    )
                    current_nation = {}
                    elem.clear()

                elif elem.tag in [
                    "NAME",
                    "FULLNAME",
                    "UNSTATUS",
                    "ENDORSEMENTS",
                    "REGION",
                    "FLAG",
                ]:
                    if elem.tag == "UNSTATUS":
                        current_nation["wa_member"] = (
                            True if elem.text == "WA Member" else False
                        )
                    elif elem.tag == "ENDORSEMENTS":
                        current_nation["endorsements"] = (
                            list(map(to_snake_case, elem.text.split(",")))
                            if elem.text
                            else []
                        )
                    else:
                        current_nation[elem.tag.lower()] = (
                            elem.text if elem.text else ""
                        )

        root.clear()
    logger.info(f"Parsed {len(nations)} nations. ({time.time() - start_time:.2f}s)")

    #### UPDATE DATABASE ####
    logger.info("Updating database...")
    try:
        start_time = time.time()
        for i, batch in enumerate(batched(nations, BATCH_SIZE), 1):
            logger.info(f"Batch {i}/{len(nations) // BATCH_SIZE + 1}")
            response = (
                supabase.table("nations")
                .upsert(batch, returning=ReturnMethod.minimal) # type: ignore (batch is a tuple which is fine, but list is expected)
                .execute()
            )
        logger.info(
            f"Successfully updated public.nations with {len(nations)} nations ({len(nations) // BATCH_SIZE + 1} batches) in {time.time() - start_time:.2f} seconds."
        )
    except Exception as e:
        logger.error(f"Error updating database: {e}")

    # Clean up temp file
    os.remove("nations_temp.xml.gz")

    logger.info(f"All done! ({time.time() - initial_time:.2f}s)")


if __name__ == "__main__":
    main()
