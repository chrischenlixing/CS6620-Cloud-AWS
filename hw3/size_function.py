import boto3
from datetime import datetime

# Initialize clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bucket_name = 'lixingchenassignment3'
table_name = 'S3_object_size_history'

def calculate_bucket_size():
    # Get the list of objects in the bucket
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    total_size = 0
    object_count = 0
    
    if 'Contents' in response:
        # Calculate the total size and count the objects
        for obj in response['Contents']:
            total_size += obj['Size']
            object_count += 1
    
    return total_size, object_count

def write_size_to_dynamodb(total_size, object_count):
    table = dynamodb.Table(table_name)
    timestamp = int(datetime.utcnow().timestamp())
    timestamp_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Write data to DynamoDB
    table.put_item(
        Item={
            'BucketName': bucket_name,
            'Timestamp': timestamp,
            'TimestampStr': timestamp_str,
            'TotalSize': total_size,
            'ObjectCount': object_count
        }
    )
