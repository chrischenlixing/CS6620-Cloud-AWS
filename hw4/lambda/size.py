from aws_cdk import Stack, Duration
from aws_cdk.aws_s3 import Bucket, EventType
from aws_cdk.aws_s3_notifications import LambdaDestination
from aws_cdk.aws_dynamodb import Table, Attribute, AttributeType, BillingMode
from aws_cdk.aws_lambda import Function, Runtime, Code
from constructs import Construct

class SizeTrackingLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create S3 Bucket
        self.bucket = Bucket(self, "Assignment3Bucket")
        # Create DynamoDB Table
        self.table = Table(self, "TrackingTable",
            partition_key=Attribute(name="BucketName", type=AttributeType.STRING),
            sort_key=Attribute(name="Timestamp", type=AttributeType.NUMBER),
            billing_mode=BillingMode.PAY_PER_REQUEST
        )
        # Create Size Tracking Lambda
        self.size_tracking_lambda = Function(
            self, "SizeTrackingLambda",
            runtime=Runtime.PYTHON_3_8,
            handler="size.lambda_handler",
            timeout=Duration.seconds(300),
            code=Code.from_asset("lambda"),
            environment={
                'DYNAMODB_TABLE_NAME': self.table.table_name,
                'BUCKET_NAME': self.bucket.bucket_name
            }
        )

        # Grant Lambda permissions to access S3 and DynamoDB
        self.bucket.grant_read_write(self.size_tracking_lambda)
        self.table.grant_read_write_data(self.size_tracking_lambda)

        # Add S3 bucket event notifications to trigger the Size Tracking Lambda
        self.bucket.add_event_notification(
            EventType.OBJECT_CREATED,
            LambdaDestination(self.size_tracking_lambda)
        )
        self.bucket.add_event_notification(
            EventType.OBJECT_REMOVED,
            LambdaDestination(self.size_tracking_lambda)
        )