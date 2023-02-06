from __future__ import annotations

from typing import Any

import aws_cdk as cdk
import boto3
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import Stack
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_iam as iam
from aws_cdk import aws_iot as iot
from aws_cdk import aws_lambda_event_sources as event_sources
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as deployment
from aws_cdk import aws_sqs as sqs
from constructs import Construct

from cdk.con_iot_rule import IotRuleToSqs
from cdk.con_lambda import PythonLambdaWithoutLayer


class QBoxStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda
        publisher = PythonLambdaWithoutLayer(self, "publish")
        auth = PythonLambdaWithoutLayer(self, "auth")
        agg = PythonLambdaWithoutLayer(self, "agg")

        # 環境変数
        auth.fn.add_environment("ACCOUNT_ID", cdk.Aws.ACCOUNT_ID)
        auth.fn.add_environment("REGION", cdk.Aws.REGION)

        # API-GW
        publish_api = apigateway.LambdaRestApi(
            self,
            "publish_api",
            handler=publisher.fn,
            proxy=False,
        )
        message = publish_api.root.add_resource("message")
        message_topic = message.add_resource("{topic}")
        message_topic.add_method("POST")

        # Sqs
        queue = sqs.Queue(
            self,
            "queue",
            visibility_timeout=cdk.Duration.minutes(60),
        )
        agg_event = event_sources.SqsEventSource(queue, max_concurrency=2)
        agg.fn.add_event_source(agg_event)

        # DynamoDB
        client_id_table = dynamodb.Table(
            self,
            "clinet_id_table",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            partition_key=dynamodb.Attribute(
                name="client_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="topic",
                type=dynamodb.AttributeType.STRING,
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        client_id_table.grant_read_write_data(agg.fn.role)  # type: ignore
        agg.fn.add_environment(
            "CLIENT_ID_TABLE_NAME",
            client_id_table.table_name
        )
        viewers_table = dynamodb.Table(
            self,
            "viewers_table",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            partition_key=dynamodb.Attribute(
                name="topic",
                type=dynamodb.AttributeType.STRING,
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        viewers_table.grant_read_write_data(agg.fn.role)  # type: ignore
        agg.fn.add_environment(
            "VIEWERS_TABLE_NAME",
            viewers_table.table_name
        )

        # IAM
        publish_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "iot:Publish",
            ],
            resources=[
                f"arn:aws:iot:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:topic/*",
            ],
        )
        publisher.fn.add_to_role_policy(statement=publish_policy_statement)
        agg.fn.add_to_role_policy(statement=publish_policy_statement)

        # IoT Core
        iot_auth = iot.CfnAuthorizer(
            self,
            "iot_auth",
            authorizer_function_arn=auth.fn.function_arn,
            enable_caching_for_http=False,
            signing_disabled=True,
            status="ACTIVE",
        )

        # IoT Coreが認証用のLambdaを呼び出す際に使用
        auth.fn.add_permission(
            "iot_auth",
            action="lambda:InvokeFunction",
            principal=iam.ServicePrincipal(
                service="iot.amazonaws.com",
                conditions={
                    "ArnLike": {
                        "aws:SourceArn": iot_auth.attr_arn,
                    }
                }
            ),
        )

        # IoT Rule
        IotRuleToSqs(
            self,
            "subscribed",
            event_name="$aws/events/subscriptions/subscribed/#",
            queue=queue,
        )
        IotRuleToSqs(
            self,
            "disconnected",
            event_name="$aws/events/presence/disconnected/#",
            queue=queue,
        )

        # Static Web
        static_bucket = s3.Bucket(
            self,
            "bucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        static_distribution = cloudfront.Distribution(
            self,
            "cloudfront_distribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(static_bucket),
            )
        )

        deployment.BucketDeployment(
            self,
            "deploy",
            sources=[deployment.Source.asset("src/static")],
            destination_bucket=static_bucket,
            distribution=static_distribution,
            distribution_paths=["/*"],
        )

        # output
        cdk.CfnOutput(
            self,
            "static_web_url",
            value=f"https://{static_distribution.domain_name}",
        )
        client = boto3.client('iot')
        endpoint_address = client.describe_endpoint()["endpointAddress"]
        cdk.CfnOutput(
            self,
            "websocket_url",
            value=f"wss://{endpoint_address}:443?x-amz-customauthorizer-name={iot_auth.authorizer_name}",
        )
        cdk.CfnOutput(
            self,
            "call_api_setup_command",
            value=f"export {publish_api.url}message",
            description="call_api.py Setup commands"
        )
