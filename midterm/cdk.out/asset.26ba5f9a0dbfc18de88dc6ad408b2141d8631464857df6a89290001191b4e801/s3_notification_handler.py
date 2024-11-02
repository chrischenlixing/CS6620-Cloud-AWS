import boto3
import json
import cfnresponse

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

def handler(event, context):
    print("Received event:", json.dumps(event))
    request_type = event['RequestType']
    props = event['ResourceProperties']
    bucket_name = props['BucketName']
    function_arn = props['FunctionArn']

    try:
        if request_type == 'Create' or request_type == 'Update':
            # Add permission for S3 to invoke the Lambda function
            lambda_client.add_permission(
                FunctionName=function_arn,
                StatementId='AllowS3Invoke',
                Action='lambda:InvokeFunction',
                Principal='s3.amazonaws.com',
                SourceArn=f'arn:aws:s3:::{bucket_name}',
            )

            # Set up the notification configuration
            s3.put_bucket_notification_configuration(
                Bucket=bucket_name,
                NotificationConfiguration={
                    'LambdaFunctionConfigurations': [
                        {
                            'LambdaFunctionArn': function_arn,
                            'Events': [
                                's3:ObjectCreated:*',
                                's3:ObjectRemoved:*'
                            ]
                        }
                    ]
                }
            )
        elif request_type == 'Delete':
            # Remove the notification configuration
            s3.put_bucket_notification_configuration(
                Bucket=bucket_name,
                NotificationConfiguration={}
            )

            # Remove the Lambda permission
            lambda_client.remove_permission(
                FunctionName=function_arn,
                StatementId='AllowS3Invoke',
            )
        else:
            print(f"Unknown request type: {request_type}")
        
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        print(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {})
