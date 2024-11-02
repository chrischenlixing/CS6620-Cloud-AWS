import boto3
import os
import time

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
bucket_dst = os.environ['DESTINATION_BUCKET_NAME']
table = dynamodb.Table(table_name)

def handler(event, context):
    # Run 12 times to simulate a 5-second interval over a 1-minute duration
    for _ in range(12):
        current_time = int(time.time())
        cutoff_time = current_time - 10
        
        # Query items that have been disowned for longer than 10 seconds
        response = table.query(
            IndexName='DisownedIndex',
            KeyConditionExpression="Disowned = :val AND LastUpdated < :cutoff",
            ExpressionAttributeValues={':val': 1, ':cutoff': cutoff_time}
        )
        
        # Delete qualifying items from S3 and DynamoDB
        for item in response['Items']:
            s3.delete_object(Bucket=bucket_dst, Key=item['CopyKey'])
            # Remove the item from DynamoDB table
            table.delete_item(Key={'ObjectName': item['ObjectName'], 'CopyTimestamp': item['CopyTimestamp']})
        
        # Pause for 5 seconds before the next iteration
        time.sleep(5)