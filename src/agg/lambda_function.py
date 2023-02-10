from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel("INFO")
client_iot = boto3.client("iot-data")
client_dynamodb = boto3.client("dynamodb")
dynamodb = boto3.resource("dynamodb")
client_id_table = dynamodb.Table(os.environ["CLIENT_ID_TABLE_NAME"])
viewers_table = dynamodb.Table(os.environ["VIEWERS_TABLE_NAME"])


def put_client_id(client_id: str, topic: str) -> None:
    client_id_table.put_item(
        Item={
            "client_id": client_id,
            "topic": topic,
        }
    )


def put_viewers(topic: str, viewers: int) -> None:
    viewers_table.put_item(
        Item={
            "viewers": viewers,
            "topic": topic,
        }
    )


def delete_client_id(client_id: str, topic: str) -> None:
    client_id_table.delete_item(
        Key={
            "client_id": client_id,
            "topic": topic,
        }
    )


def has_client_id(client_id: str, topic: str) -> bool:
    try:
        client_dynamodb.get_item(
            TableName=os.environ["CLIENT_ID_TABLE_NAME"],
            Key={
                "client_id": {
                    "S": client_id,
                },
                "topic": {
                    "S": topic,
                }
            }
        )
        return True
    except client_dynamodb.exceptions.ResourceNotFoundException:
        return False


def get_topics(client_id: str) -> list[str]:
    items = client_id_table.query(
        KeyConditionExpression=Key("client_id").eq(client_id)
    )["Items"]
    return [item["topic"] for item in items]


def get_viewers() -> dict[str, int]:
    param: dict[str, Any] = {}
    items: list[dict[str, Any]] = []
    while True:
        responce = viewers_table.scan(**param)
        items += responce["Items"]
        if responce.get("LastEvaluatedKey"):
            param["ExclusiveStartKey"] = responce["LastEvaluatedKey"]
        else:
            break
    return {item["topic"]: item["viewers"] for item in items}


def publish_viewers(topic: str, viewers: int) -> None:
    payload = {
        "type": "viewers",
        "viewers": viewers,
    }
    client_iot.publish(
        topic=topic,
        payload=json.dumps(payload),
    )


def count(item: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    if item["eventType"] == "subscribed":
        for topic in item["topics"]:
            if has_client_id(item["clientId"], topic):
                result[topic] = result.get(topic, 0) + 1
                put_client_id(item["clientId"], topic)
            else:
                pass
    if item["eventType"] == "disconnected":
        for topic in get_topics(item["clientId"]):
            result[topic] = result.get(topic, 0) - 1
            delete_client_id(item["clientId"], topic)
    return result


def service(event: dict[str, Any]) -> None:
    result = get_viewers()
    for record in event["Records"]:
        item = json.loads(record["body"])
        for k, v in count(item).items():
            result[k] = result.get(k, 0) + v
    for topic, viewers in result.items():
        put_viewers(topic, viewers)
        publish_viewers(topic, int(viewers))


def lambda_handler(event: dict[str, Any], context: dict[str, Any]) -> int:
    logger.info(json.dumps(event, indent=2))
    try:
        service(event)
        return 200
    except Exception:
        logger.exception("想定外エラー")
        return 500
