from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,  # Import aws_iam for ServicePrincipal
    Duration,
)
from constructs import Construct

class CleanerStack(Stack):
    def __init__(self, scope: Construct, id: str, storage_stack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Lambda Function for Cleaner
        self.cleaner_lambda = _lambda.Function(
            self, "CleanerLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="cleaner_handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'DYNAMODB_TABLE': storage_stack.table_t.table_name,
                'BUCKET_DST': storage_stack.bucket_dst.bucket_name,
                'SELF_INVOKE': 'true'  # Flag to enable self-invocation
            },
            timeout=Duration.seconds(10)  # Set a timeout greater than 5 seconds to allow for delay
        )

        # Grant permissions for Cleaner Lambda to interact with S3 and DynamoDB
        storage_stack.bucket_dst.grant_delete(self.cleaner_lambda)
        storage_stack.table_t.grant_read_write_data(self.cleaner_lambda)
        
        # Grant permission to allow self-invocation of the Lambda
        self.cleaner_lambda.add_permission(
            "AllowSelfInvoke",
            principal=iam.ServicePrincipal("lambda.amazonaws.com"),  # Correctly use ServicePrincipal from aws_iam
            action="lambda:InvokeFunction"
        )

        # Initial EventBridge rule to trigger the Cleaner Lambda every 1 minute
        rule = events.Rule(
            self, "CleanerInitialSchedule",
            schedule=events.Schedule.rate(Duration.minutes(1))
        )
        rule.add_target(targets.LambdaFunction(self.cleaner_lambda))
