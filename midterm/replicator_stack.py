from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from constructs import Construct

class ReplicatorStack(Stack):
    def __init__(self, scope: Construct, id: str, storage_stack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Lambda Function for Replicator
        self.replicator_lambda = _lambda.Function(
            self, "ReplicatorLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="replicator_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'DYNAMODB_TABLE_NAME': storage_stack.table_t.table_name,
                'BUCKET_SRC_ARN': storage_stack.bucket_src.bucket_arn,
                'BUCKET_DST_ARN': storage_stack.bucket_dst.bucket_arn
            }
        )

        # Grant permissions for Replicator Lambda
        self.replicator_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{storage_stack.bucket_src.bucket_arn}/*"]
            )
        )

        self.replicator_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"{storage_stack.bucket_dst.bucket_arn}/*"]
            )
        )

        self.replicator_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:GetItem"],
                resources=[storage_stack.table_t.table_arn]
            )
        )
