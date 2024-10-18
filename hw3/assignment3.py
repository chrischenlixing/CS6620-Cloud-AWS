import boto3
from botocore.exceptions import ClientError
import time

# Initialize boto3 clients
s3_client = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
dynamodb_resource = boto3.resource('dynamodb')

# 1. Create S3 Bucket
def create_s3_bucket(bucket_name):
    try:
        response = s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': boto3.session.Session().region_name
            }
        )
        print(f"S3 bucket '{bucket_name}' created successfully.")
    except ClientError as e:
        print(f"Error creating bucket: {e}")

# 2. Create DynamoDB Table
def create_dynamodb_table(table_name):
    try:
        table = dynamodb_resource.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'BucketName',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'Timestamp',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'BucketName',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'Timestamp',
                    'AttributeType': 'N'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        # Wait until the table exists.
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"DynamoDB table '{table_name}' created successfully.")
    except ClientError as e:
        print(f"Error creating DynamoDB table: {e}")

def main():
    bucket_name = 'lixingchenassignment3'
    table_name = 'S3_object_size_history'

    # Create S3 bucket
    create_s3_bucket(bucket_name)

    # Create DynamoDB table
    create_dynamodb_table(table_name)

if __name__ == "__main__":
    main()