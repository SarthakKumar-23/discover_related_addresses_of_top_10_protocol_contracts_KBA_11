import os
import csv
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALCHEMY_API_KEY")

if not API_KEY:
    raise RuntimeError("ALCHEMY_API_KEY NOT FOUND IN .env")

RPC_URL = f"https://eth-mainnet.g.alchemy.com/v2/{API_KEY}"

INPUT_FILE = "data/input/top_10_addresses.csv"

OUTPUT_FILE = "data/output/top_10_related_addresses.csv"
SUMMARY_FILE = "data/output/layer1_growth_summary.csv"

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

CATEGORIES = [
    "external",
    "internal",
    "erc20",
    "erc721",
    "erc1155"
]

PAGE_SIZE = 100
MAX_PAGES_PER_DIRECTION = 2

os.makedirs("data/output", exist_ok=True)

def get_transfers(address, direction):

    if direction == "outgoing":
        address_filter = "fromAddress"
    else:
        address_filter = "toAddress"

    params = {
        address_filter: address,
        "category": CATEGORIES,
        "withMetadata": True,
        "maxCount": hex(PAGE_SIZE)
    }

    all_transfers = []

    page_number = 1

    while page_number <= MAX_PAGES_PER_DIRECTION:

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "alchemy_getAssetTransfers",
            "params": [params]
        }

        response = requests.post(
            RPC_URL,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise RuntimeError(data["error"])

        result = data["result"]

        transfers = result.get("transfers", [])

        print(
            f"    {direction} page {page_number}: "
            f"{len(transfers)} transfers"
        )

        all_transfers.extend(transfers)

        page_key = result.get("pageKey")

        if not page_key:
            break

        params["pageKey"] = page_key
        page_number += 1

        time.sleep(0.1)

    return all_transfers

def main():

    seeds = pd.read_csv(INPUT_FILE)

    seeds["address"] = (
        seeds["address"].str.lower().str.strip()
    )

    seed_addresses = seeds["address"].drop_duplicates().tolist()

    seed_info = (
        seeds.groupby("address").agg({
            "protocol": lambda x: ";".join(sorted(set(x))),
            "contract_name": lambda x: ";".join(sorted(set(x))),
            "role": lambda x: ";".join(sorted(set(x)))
        })
        .to_dict("index")
    )

    seed_set = set(seed_addresses)

    relationships = []

    print()
    print("STARTING LAYER 1 DISCOVERY")
    print("==========================")
    print("Seed contracts:", len(seed_addresses))
    print(
    f"    Maximum pages per direction: "
    f"{MAX_PAGES_PER_DIRECTION}"
    )
    print()

    for index, seed_address in enumerate(seed_addresses, start=1):

        info = seed_info[seed_address]

        print(
            f"[{index}/{len(seed_addresses)}]"
            f"{info["protocol"]} -"
            f"{info["contract_name"]}"
        )

        for query_direction in ["outgoing", "incoming"]:

            transfers = get_transfers(
                seed_address,
                query_direction
            )

            for transfer in transfers:

                from_address = (
                    transfer.get("from") or ""
                ).lower()

                to_address = (
                    transfer.get("to") or ""
                ).lower()

                if from_address == seed_address:

                    direction = "outgoing"
                    related_address = to_address

                elif to_address == seed_address:

                    direction = "incoming"
                    related_address = from_address

                else:
                    continue

                if related_address in [
                    "",
                    ZERO_ADDRESS,
                    seed_address
                ]:
                    continue

                relationships.append({
                    "protocol": info["protocol"],
                    "contract_name": info["contract_name"],
                    "seed_address": seed_address,
                    "related_address": related_address,
                    "direction": direction,
                    "relationship_type": transfer.get("category"),
                    "from_address": from_address,
                    "to_address": to_address,
                    "asset": transfer.get("asset"),
                    "value": transfer.get("value"),
                    "transaction_hash": transfer.get("hash"),
                    "block_number": transfer.get("blockNum")
                })

        print()

    if not relationships:

        print("No relationships found.")
        return

    df = pd.DataFrame(relationships)

    # Remove exact duplicate relationship records.
    df = df.drop_duplicates()

    # Mark whether the related address is itself a seed contract.
    df["is_seed_address"] = (
        df["related_address"].isin(seed_set)
    )

    # Save complete relationship evidence.

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # Calculate growth by protocol.
    summary_rows = []

    for protocol, group in df.groupby("protocol"):

        related = set(
            group.loc[
                ~group["is_seed_address"],
                "related_address"
            ]
        )

        summary_rows.append({
            "protocol": protocol,
            "seed_contracts": group["seed_address"].nunique(),
            "relationship_edges": len(group),
            "unique_related_addresses": len(related)
        })

    # Overall result.
    all_related = set(
        df.loc[
            ~df["is_seed_address"],
            "related_address"
        ]
    )

    summary_rows.append({
        "protocol": "ALL",
        "seed_contracts": len(seed_addresses),
        "relationship_edges": len(df),
        "unique_related_addresses": len(all_related)
    })

    summary = pd.DataFrame(summary_rows)

    summary.to_csv(
        SUMMARY_FILE,
        index=False
    )

    print()
    print("========================")
    print("LAYER 1 COMPLETE")
    print("========================")

    print(
        "Seed contracts:",
        len(seed_addresses)
    )

    print(
        "Relationship edges:",
        f"{len(df):,}"
    )

    print(
        "Unique Layer 1 addresses:",
        f"{len(all_related):,}"
    )

    print()
    print("Relationship file:")
    print(OUTPUT_FILE)

    print()
    print("Growth summary:")
    print(SUMMARY_FILE)

if __name__ == "__main__":
    main()