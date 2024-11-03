from aws_cdk import Stack, Duration, aws_events as events, aws_events_targets as targets
from aws_cdk.aws_lambda import Function, Runtime, Code
from constructs import Construct
from dynamodb_stack import DynamoDBStack
from s3_stack import S3Stack

class SizeTrackingLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, dynamodb_stack: DynamoDBStack, s3_stack: S3Stack, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Size Tracking Lambda
        self.size_tracking_lambda = Function(
            self, "SizeTrackingLambda",
            runtime=Runtime.PYTHON_3_8,
            handler="size.lambda_handler",
            timeout=Duration.seconds(300), 
            code=Code.from_asset("lambda"), 
            environment={
                'DYNAMODB_TABLE_NAME': dynamodb_stack.table.table_name,
                'BUCKET_NAME': s3_stack.bucket_name
            }
        )

        # Grant S3 and DynamoDB permissions
        s3_stack.bucket.grant_read_write(self.size_tracking_lambda)
        s3_stack.plottedBucket.grant_read_write(self.size_tracking_lambda)
        dynamodb_stack.table.grant_read_write_data(self.size_tracking_lambda)

        # Define EventBridge rule to trigger Lambda on S3 PUT and DELETE events
        s3_event_rule = events.Rule(
            self, "S3EventRule",
            event_pattern={
                "source": ["aws.s3"],
                "detail_type": ["Object Created", "Object Removed"],
                "resources": [s3_stack.bucket.bucket_arn]
            }
        )

        # Add the Size Tracking Lambda function as a target for the EventBridge rule
        s3_event_rule.add_target(targets.LambdaFunction(self.size_tracking_lambda))