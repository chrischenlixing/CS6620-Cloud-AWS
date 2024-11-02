import boto3
import os
import time

# Initialize resources
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Environment variables
table_name = os.environ['TABLE_NAME']
destination_bucket = os.environ['DESTINATION_BUCKET_NAME']

# DynamoDB table
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
        
        # Process each item
        for item in response['Items']:
            object_name = item['ObjectName']
            copy_timestamp = item['CopyTimestamp']
            copy_key = item['CopyKey']
            
            try:
                # Delete the item from DynamoDB
                table.delete_item(Key={'ObjectName': object_name, 'CopyTimestamp': copy_timestamp})
                
                # Delete the corresponding object from S3
                s3.delete_object(Bucket=destination_bucket, Key=copy_key)
                print(f"Deleted object {object_name} with copy key {copy_key} from {destination_bucket} and DynamoDB.")
            
            except Exception as e:
                print(f"Error processing item {item}: {e}")
        
        # Pause for 5 seconds before the next iteration
        time.sleep(5) 