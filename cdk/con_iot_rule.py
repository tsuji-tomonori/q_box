from __future__ import annotations

from aws_cdk import aws_iam as iam
from aws_cdk import aws_iot as iot
from aws_cdk import aws_sqs as sqs
from constructs import Construct


class IotRuleToSqs(Construct):

    def __init__(self, scope: Construct, id: str, event_name: str, queue: sqs.Queue) -> None:
        super().__init__(scope, id)

        iot_rule_role = iam.Role(
            self,
            f"iot_rule_to_sqs_{id}_role",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com")
        )
        queue.grant_send_messages(iot_rule_role)

        iot.CfnTopicRule(
            self,
            f"iot_rule_to_sqs_{id}_iot_rule",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=f"select * from \'{event_name}\'",
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        sqs=iot.CfnTopicRule.SqsActionProperty(
                            queue_url=queue.queue_url,
                            role_arn=iot_rule_role.role_arn,
                            use_base64=False,
                        )
                    )
                ]
            )
        )
