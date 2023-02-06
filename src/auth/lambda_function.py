from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any

logger = logging.getLogger()
logger.setLevel("INFO")


def role_allow(topic_name: str) -> dict[str, Any]:
    return {
        "isAuthenticated": True,
        "principalId": "hoge",  # 今回は適当な値を入れる
        "policyDocuments": [
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "iot:Connect",
                        "Resource": f"arn:aws:iot:{os.environ['AWS_REGION']}:{os.environ['ACCOUNT_ID']}:client/{os.environ['CLIENT_ID_PREFIX']}*",
                    },
                    {
                        "Effect": "Allow",
                        "Action": "iot:Subscribe",
                        "Resource": f"arn:aws:iot:{os.environ['AWS_REGION']}:{os.environ['ACCOUNT_ID']}:topicfilter/{topic_name}",
                    },
                    {
                        "Effect": "Allow",
                        "Action": "iot:Receive",
                        "Resource": f"arn:aws:iot:{os.environ['AWS_REGION']}:{os.environ['ACCOUNT_ID']}:topic/{topic_name}",
                    },
                ]
            },
        ],
        "disconnectAfterInSeconds": int(os.environ["DISCONNECT_AFTER_IN_SECONDS"]),
        "refreshAfterInSeconds": int(os.environ["REFRESH_AFTER_IN_SECONDS"]),
    }


def role_deny() -> dict[str, Any]:
    return {
        "isAuthenticated": True,
        "principalId": "test",
        "policyDocuments": [
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Deny",
                        "Action": "*",
                        "Resource": "*",
                    },
                ]
            },
        ],
        "disconnectAfterInSeconds": int(os.environ["DISCONNECT_AFTER_IN_SECONDS"]),
        "refreshAfterInSeconds": int(os.environ["REFRESH_AFTER_IN_SECONDS"]),
    }


def service(topic_name: str, password: str) -> dict[str, Any]:
    if password == os.environ["PASSWORD"]:
        return role_allow(topic_name)
    else:
        return role_deny()


def lambda_handler(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    logger.info(json.dumps(event, indent=2))
    result = None
    mqtt = event["protocolData"]["mqtt"]
    try:
        result = service(
            topic_name=mqtt["username"],
            password=base64.b64decode(mqtt["password"]).decode(),
        )
    except Exception:
        logger.exception("想定外エラー")
        result = role_deny()
    logger.info(json.dumps(result, indent=2))
    return result
