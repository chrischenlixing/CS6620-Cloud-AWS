from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_s3_notifications as s3n,
)
from constructs import Construct

class StorageStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # S3 Buckets
        self.bucket_src = s3.Bucket(self, "BucketSrc")
        self.bucket_dst = s3.Bucket(self, "BucketDst")

        # DynamoDB Table
        self.table_t = dynamodb.Table(
            self, "TableT",
            partition_key=dynamodb.Attribute(name="ObjectName", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="Timestamp", type=dynamodb.AttributeType.NUMBER),
            time_to_live_attribute="TTL"
        )

    def add_s3_event_notifications(self, replicator_lambda):
        # Only add event notifications if replicator_lambda is provided
        if replicator_lambda:
            self.bucket_src.add_event_notification(
                s3.EventType.OBJECT_CREATED,
                s3n.LambdaDestination(replicator_lambda)
            )
            self.bucket_src.add_event_notification(
                s3.EventType.OBJECT_REMOVED,
                s3n.LambdaDestination(replicator_lambda)
            )