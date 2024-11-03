from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
)
from constructs import Construct

class DynamoDBStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Define DynamoDB table with partition and sort key
        self.table = dynamodb.Table(
            self, "S3ObjectSize",
            partition_key=dynamodb.Attribute(
                name="BucketName",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="Timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            read_capacity=5,
            write_capacity=5
        )

        