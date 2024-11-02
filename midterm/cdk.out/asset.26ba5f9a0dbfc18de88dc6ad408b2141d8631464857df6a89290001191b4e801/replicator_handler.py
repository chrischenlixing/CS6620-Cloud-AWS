import os
import boto3
import urllib.parse
import time
from boto3.dynamodb.conditions import Key

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

BUCKET_SRC = os.environ['BUCKET_SRC']
BUCKET_DST = os.environ['BUCKET_DST']
TABLE_NAME = os.environ['TABLE_NAME']

table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    # Process the S3 event
    for record in event['Records']:
        event_name = record['eventName']
        src_bucket = record['s3']['bucket']['name']
        src_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        
        if event_name.startswith('ObjectCreated:'):
            # Handle PUT event
            process_put_event(src_key)
        elif event_name.startswith('ObjectRemoved:'):
            # Handle DELETE event
            process_delete_event(src_key)

def process_put_event(src_key):
    # Query for existing copies of the object
    response = table.query(
        KeyConditionExpression=Key('OriginalObjectKey').eq(src_key),
        ScanIndexForward=True  # Sort ascending by CopyCreationTimestamp
    )
    items = response.get('Items', [])
    
    # If there are existing copies, delete the oldest one
    if items:
        oldest_item = items[0]
        copy_object_key = oldest_item['CopyObjectKey']
        # Delete the oldest copy from BucketDst
        s3.delete_object(Bucket=BUCKET_DST, Key=copy_object_key)
        # Delete the item from DynamoDB
        table.delete_item(
            Key={
                'OriginalObjectKey': src_key,
                'CopyCreationTimestamp': oldest_item['CopyCreationTimestamp']
            }
        )

    # Create a new copy of the object
    timestamp = int(time.time() * 1000)
    copy_object_key = f"{src_key}-{timestamp}"
    s3.copy_object(
        Bucket=BUCKET_DST,
        CopySource={'Bucket': BUCKET_SRC, 'Key': src_key},
        Key=copy_object_key
    )

    # Add new item to DynamoDB
    table.put_item(
        Item={
            'OriginalObjectKey': src_key,
            'CopyCreationTimestamp': timestamp,
            'CopyObjectKey': copy_object_key,
            'Disowned': 'N',
            'DisownTimestamp': 0  # Placeholder value
        }
    )

def process_delete_event(src_key):
    # Update items in DynamoDB to mark them as disowned
    response = table.query(
        KeyConditionExpression=Key('OriginalObjectKey').eq(src_key)
    )
    items = response.get('Items', [])
    for item in items:
        table.update_item(
            Key={
                'OriginalObjectKey': item['OriginalObjectKey'],
                'CopyCreationTimestamp': item['CopyCreationTimestamp']
            },
            UpdateExpression="SET Disowned = :d, DisownTimestamp = :t",
            ExpressionAttributeValues={
                ':d': 'Y',
                ':t': int(time.time())
            }
        )