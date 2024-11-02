import boto3
import time
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('TableT')  # Replace with actual DynamoDB table name

def handler(event, context):
    for record in event['Records']:
        event_name = record['eventName']
        object_key = record['s3']['object']['key']
        bucket_src = record['s3']['bucket']['name']
        bucket_dst = 'BucketDst'  # Replace with actual Bucket Dst name
        current_timestamp = int(time.time())

        if "ObjectCreated" in event_name:
            # Generate a unique key for the copy in BucketDst
            copy_key = f"copy-{current_timestamp}-{object_key}"

            # Copy the object to BucketDst
            try:
                s3.copy_object(
                    Bucket=bucket_dst,
                    CopySource={'Bucket': bucket_src, 'Key': object_key},
                    Key=copy_key
                )
                print(f"Copied {object_key} to {bucket_dst} as {copy_key}")

                # Add the new copy to DynamoDB
                table.put_item(
                    Item={
                        'ObjectName': object_key,
                        'CopyTimestamp': str(current_timestamp),
                        'CopyLocation': copy_key,
                        'Status': 'active',
                        'LastModified': current_timestamp
                    }
                )

                # Check for existing copies and delete the oldest if necessary
                response = table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('ObjectName').eq(object_key),
                    ScanIndexForward=True  # Ensures results are sorted by CopyTimestamp ascending
                )

                copies = response.get('Items', [])
                if len(copies) > 1:  # If more than one copy, delete the oldest
                    oldest_copy = copies[0]  # The first item is the oldest due to ascending order
                    s3.delete_object(Bucket=bucket_dst, Key=oldest_copy['CopyLocation'])
                    print(f"Deleted oldest copy {oldest_copy['CopyLocation']} of {object_key}")

                    # Remove the oldest entry from DynamoDB
                    table.delete_item(
                        Key={
                            'ObjectName': object_key,
                            'CopyTimestamp': oldest_copy['CopyTimestamp']
                        }
                    )

            except ClientError as e:
                print(f"Error copying {object_key} to {bucket_dst}: {e}")

        elif "ObjectRemoved" in event_name:
            # Mark all copies of the deleted object as disowned in DynamoDB
            try:
                response = table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('ObjectName').eq(object_key)
                )

                for item in response.get('Items', []):
                    table.update_item(
                        Key={
                            'ObjectName': item['ObjectName'],
                            'CopyTimestamp': item['CopyTimestamp']
                        },
                        UpdateExpression="SET #s = :disowned, LastModified = :timestamp",
                        ExpressionAttributeNames={'#s': 'Status'},
                        ExpressionAttributeValues={
                            ':disowned': 'disowned',
                            ':timestamp': current_timestamp
                        }
                    )
                    print(f"Marked {item['CopyLocation']} as disowned for {object_key}")

            except ClientError as e:
                print(f"Error marking items for {object_key} as disowned: {e}")