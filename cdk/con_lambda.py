from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import Duration
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct


class PythonLambdaWithoutLayer(Construct):

    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        self._function_name = f"lmd_{id}_cdk"

        self.fn = lambda_.Function(
            self, self._function_name,
            code=lambda_.Code.from_asset(f"src/{id}"),
            handler="lambda_function.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            timeout=Duration.seconds(60),
            environment=self.node.try_get_context(f"env_fn_{id}"),
            memory_size=256,
        )

        loggroup_name = f"/aws/lambda/{self.fn.function_name}"
        logs.LogGroup(
            self, f"{id}-loggroup",
            log_group_name=loggroup_name,
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
