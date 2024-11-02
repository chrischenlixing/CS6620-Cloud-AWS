import boto3
import os
import time

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
bucket_scr = os.environ['SOURCE_BUCKET_NAME']
bucket_dst = os.environ['DESTINATION_BUCKET_NAME']
table = dynamodb.Table(table_name)

def handler(event, context):
    for record in event['Records']:
        event_name = record['eventName']
        object_key = record['s3']['object']['key']
        
        if event_name.startswith('ObjectCreated'):
            # Generate a unique key for the copy in the destination bucket
            copy_key = f"{object_key}-{int(time.time())}"
            s3.copy_object(
                Bucket=bucket_dst,
                CopySource={'Bucket': record['s3']['bucket']['name'], 'Key': object_key},
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
        
        elif event_name.startswith('ObjectRemoved'):
            # Mark object as disowned (requires both ObjectName and CopyTimestamp if CopyTimestamp is part of the key)
            response = table.update_item(
                Key={'ObjectName': object_key, 'CopyTimestamp': int(time.time())},  # Ensure correct partition and sort key
                UpdateExpression="SET Disowned = :val, LastUpdated = :time",
                ExpressionAttributeValues={
                    ':val': 1,  # 1 indicates "disowned"
                    ':time': int(time.time())  # Record the time of update
                }
            )