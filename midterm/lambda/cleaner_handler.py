import os
import boto3
import time
from boto3.dynamodb.conditions import Key

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

BUCKET_DST = os.environ['BUCKET_DST']
TABLE_NAME = os.environ['TABLE_NAME']
DISOWNED_INDEX = 'DisownedIndex'

table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    # Calculate the cutoff time (current time - 10 seconds)
    cutoff_time = int(time.time()) - 10

    # Query the GSI for items where Disowned='Y' and DisownTimestamp <= cutoff_time
    response = table.query(
        IndexName=DISOWNED_INDEX,
        KeyConditionExpression=Key('Disowned').eq('Y') & Key('DisownTimestamp').lte(cutoff_time)
    )

    items = response.get('Items', [])
    for item in items:
        # Delete the copy from BucketDst
        copy_object_key = item['CopyObjectKey']
        s3.delete_object(Bucket=BUCKET_DST, Key=copy_object_key)

        # Delete the item from DynamoDB
        table.delete_item(
            Key={
                'OriginalObjectKey': item['OriginalObjectKey'],
                'CopyCreationTimestamp': item['CopyCreationTimestamp']
            }
        )