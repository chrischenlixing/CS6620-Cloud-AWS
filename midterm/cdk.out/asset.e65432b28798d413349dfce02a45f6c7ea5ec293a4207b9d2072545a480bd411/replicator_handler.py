import boto3
import os
import time
from urllib.parse import unquote_plus
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
bucket_src = os.environ['SOURCE_BUCKET_NAME']
bucket_dst = os.environ['DESTINATION_BUCKET_NAME']
table = dynamodb.Table(table_name)

def handler(event, context):
    print("Event received:", event)
    for record in event['Records']:
        event_name = record['eventName']
        object_key = unquote_plus(record['s3']['object']['key'])
        
        if event_name.startswith('ObjectCreated'):
            copy_key = f"{object_key}-copy"
            copy_source = {'Bucket': record['s3']['bucket']['name'], 'Key': object_key}
            
            print(f"Attempting to copy {object_key} to {copy_key}")
            
            # Check if there is an existing record in DynamoDB for this copy
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('ObjectName').eq(object_key)
            )
            existing_items = [
                item for item in response.get('Items', [])
                if item.get('CopyKey') == copy_key
            ]
            
            if existing_items:
                # Delete existing object in the destination bucket
                try:
                    s3.delete_object(Bucket=bucket_dst, Key=copy_key)
                    print(f"Deleted existing object {copy_key} from destination bucket")
                except ClientError as e:
                    print(f"Error deleting existing object: {e}")
                    raise

                # Delete items from DynamoDB
                for item in existing_items:
                    try:
                        table.delete_item(
                            Key={
                                'ObjectName': item['ObjectName'],
                                'CopyTimestamp': item['CopyTimestamp']
                            }
                        )
                        print(f"Deleted existing item from DynamoDB for {copy_key}")
                    except ClientError as e:
                        print(f"Error deleting item from DynamoDB: {e}")
                        raise

            # Retry mechanism
            max_retries = 3
            retry_delay = 2  # seconds
            for attempt in range(max_retries):
                try:
                    # Copy the object to the destination bucket
                    s3.copy_object(
                        Bucket=bucket_dst,
                        CopySource=copy_source,
                        Key=copy_key
                    )
                    
                    # Insert a new item into DynamoDB
                    table.put_item(Item={
                        'ObjectName': object_key,
                        'CopyTimestamp': int(time.time()),
                        'CopyKey': copy_key,
                        'Disowned': 0,
                        'LastUpdated': int(time.time())
                    })
                    
                    print(f"Copy succeeded on attempt {attempt + 1}")
                    break  # Exit the retry loop on success

                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        print(f"NoSuchKey error on attempt {attempt + 1}: {e}")
                        time.sleep(retry_delay)  # Wait before retrying
                    else:
                        print(f"An unexpected ClientError occurred: {e}")
                        break  # Stop retrying on other exceptions
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    break  # Stop retrying on other exceptions

        elif event_name.startswith('ObjectRemoved'):
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('ObjectName').eq(object_key)
            )
            items = response.get('Items', [])
            
            for item in items:
                table.update_item(
                    Key={
                        'ObjectName': item['ObjectName'],
                        'CopyTimestamp': item['CopyTimestamp']
                    },
                    UpdateExpression="SET Disowned = :val, LastUpdated = :time",
                    ExpressionAttributeValues={
                        ':val': 1,
                        ':time': int(time.time())
                    }
                )