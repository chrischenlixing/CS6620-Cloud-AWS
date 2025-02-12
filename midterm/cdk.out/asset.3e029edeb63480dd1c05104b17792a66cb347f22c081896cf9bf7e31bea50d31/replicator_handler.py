import boto3
import os
import time
from urllib.parse import quote

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
        object_key = record['s3']['object']['key']
        
        if event_name.startswith('ObjectCreated'):
            # Generate a unique key for the copy in the destination bucket
            copy_key = f"{object_key}-{int(time.time())}"
            encoded_object_key = quote(object_key)  # URL encode the object key
            copy_source = {'Bucket': record['s3']['bucket']['name'], 'Key': encoded_object_key}
            
            print(f"Copying {object_key} to {copy_key}")
            
            try:
                # Attempt to copy the object
                s3.copy_object(
                    Bucket=bucket_dst,
                    CopySource=copy_source,
                    Key=copy_key
                )
                
                # Insert a new item into DynamoDB with the copied object details
                table.put_item(Item={
                    'ObjectName': object_key,
                    'CopyTimestamp': int(time.time()),  # Use the current time as the timestamp
                    'CopyKey': copy_key,
                    'Disowned': 0,  # Indicates the copy is "owned"
                    'LastUpdated': int(time.time())
                })
            
            except s3.exceptions.NoSuchKey as e:
                print(f"NoSuchKey error: {e}. The specified key {object_key} does not exist in {record['s3']['bucket']['name']}.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

        elif event_name.startswith('ObjectRemoved'):
            # Query all items with ObjectName to update their Disowned status
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
                        ':val': 1,  # 1 indicates "disowned"
                        ':time': int(time.time())  # Record the time of update
                    }
                )