import argparse
import asyncio
import json
import sys

import httpx

from app.core.config import Settings
from app.evaluation.schemas import Query
from app.main import build_engine


async def run():
    parser = argparse.ArgumentParser(description="Internal JSONL evaluation interface")
    parser.add_argument("--question")
    parser.add_argument("--url")
    args = parser.parse_args()
    async with httpx.AsyncClient(trust_env=False) as client:
        engine = build_engine(Settings(), client)
        records = [{"question": args.question, "starting_url": args.url}] if args.question else (json.loads(line) for line in sys.stdin if line.strip())
        for record in records:
            answer = await engine.answer(Query.model_validate(record))
            print(answer.model_dump_json())


if __name__ == "__main__":
    asyncio.run(run())
