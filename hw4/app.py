from aws_cdk import App
from size_tracking_lambda_stack import SizeTrackingLambdaStack
from plotting_lambda_stack import PlottingLambdaStack
from api_stack import ApiGatewayStack
from driver_lambda_stack import DriverLambdaStack

app = App()

# Create StorageAndTrackingStack to set up S3 and DynamoDB resources with Size Tracking Lambda
size_tracking_lambda_stack = SizeTrackingLambdaStack(app, "SizeTrackingStack")

# Create PlottingLambdaStack, setting up the Plotting Lambda function
plotting_lambda_stack = PlottingLambdaStack(app, "PlottingLambdaStack",
                                            dynamodb_table=size_tracking_lambda_stack.table,
                                            s3_bucket=size_tracking_lambda_stack.bucket)

# Create ApiGatewayStack and integrate it with the Plotting Lambda function
api_gateway_stack = ApiGatewayStack(app, "ApiGatewayStack", plotting_lambda=plotting_lambda_stack.plotting_lambda)

# Create DriverLambdaStack and pass in the API URL and API ID for invocation
driver_lambda_stack = DriverLambdaStack(app, "DriverLambdaStack", 
                                        s3_bucket=size_tracking_lambda_stack.bucket, 
                                        plotting_api_url=api_gateway_stack.api_url,
                                        plotting_api_id=api_gateway_stack.api_id)

app.synth()