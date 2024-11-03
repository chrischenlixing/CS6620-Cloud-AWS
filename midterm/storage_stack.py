from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    CfnOutput,
    aws_s3_notifications as s3n,
    Duration,
)
from constructs import Construct

class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Define the source and destination buckets
        self.bucket_src = s3.Bucket(self, "SourceBucket")
        self.bucket_dst = s3.Bucket(self, "DestinationBucket")
        
        # Define the DynamoDB table
        self.table_t = dynamodb.Table(
            self, "BackupTable",
            partition_key=dynamodb.Attribute(name="ObjectName", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="CopyTimestamp", type=dynamodb.AttributeType.NUMBER)
        )
        
        # Add a secondary index
        self.table_t.add_global_secondary_index(
            index_name="DisownedIndex",
            partition_key=dynamodb.Attribute(name="Disowned", type=dynamodb.AttributeType.NUMBER),
            sort_key=dynamodb.Attribute(name="LastUpdated", type=dynamodb.AttributeType.NUMBER)
        )
        
        # Define the Replicator Lambda function
        self.replicator_lambda = lambda_.Function(
            self, 'ReplicatorLambda',
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler='replicator_handler.handler',
            code=lambda_.Code.from_asset('lambda'),
            timeout=Duration.seconds(300), 
            environment={
                'SOURCE_BUCKET_NAME': self.bucket_src.bucket_name,
                'DESTINATION_BUCKET_NAME': self.bucket_dst.bucket_name,
                'TABLE_NAME': self.table_t.table_name,
            }
        )
        
        # Grant permissions and set up notifications
        self.bucket_dst.grant_write(self.replicator_lambda)
        self.table_t.grant_read_write_data(self.replicator_lambda)
        self.bucket_src.grant_read(self.replicator_lambda)

        self.replicator_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=['s3:GetObject', 's3:ListBucket', 's3:PutObject', 's3:DeleteObject','s3:HeadObject'],
                resources=[self.bucket_src.bucket_arn, f"{self.bucket_src.bucket_arn}/*"]
            )
        )
        
        notification = s3n.LambdaDestination(self.replicator_lambda)
        self.bucket_src.add_event_notification(s3.EventType.OBJECT_CREATED, notification)
        self.bucket_src.add_event_notification(s3.EventType.OBJECT_REMOVED, notification)
        
        # Export the resources for use in other stacks
        CfnOutput(self, 'SourceBucketArn', value=self.bucket_src.bucket_arn, export_name='SourceBucketArn')
        CfnOutput(self, 'ReplicatorLambdaArn', value=self.replicator_lambda.function_arn, export_name='ReplicatorLambdaArn')