from __future__ import annotations

import json
import logging
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel("INFO")
client = boto3.client("iot-data")


def lambda_handler(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    logger.info(json.dumps(event, indent=2))
    try:
        client.publish(
            topic=event["pathParameters"]["topic"],
            payload=event["body"],
        )
        return {
            "statusCode": 200,
        }
    except Exception:
        logger.exception("想定外エラー")
        return {
            "statusCode": 500,
        }
