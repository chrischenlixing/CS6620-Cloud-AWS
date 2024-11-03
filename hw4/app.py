import aws_cdk as cdk
from s3_stack import S3Stack
from dynamodb_stack import DynamoDBStack
from plotting_lambda_stack import PlottingLambdaStack
from size_tracking_lambda_stack import SizeTrackingLambdaStack
from driver_lambda_stack import DriverLambdaStack

app = cdk.App()

# Instantiate S3 and DynamoDB stacks first, as they are dependencies for the Lambda stacks
s3_stack = S3Stack(app, "S3Stack")
dynamodb_stack = DynamoDBStack(app, "DynamoDBStack")

# Instantiate Lambda stacks and pass in the necessary dependencies
plotting_lambda_stack = PlottingLambdaStack(app, "PlottingLambdaStack", dynamodb_stack=dynamodb_stack, s3_stack=s3_stack)
size_tracking_lambda_stack = SizeTrackingLambdaStack(app, "SizeTrackingLambdaStack", dynamodb_stack=dynamodb_stack, s3_stack=s3_stack)
driver_lambda_stack = DriverLambdaStack(app, "DriverLambdaStack", s3_stack=s3_stack,plotting_lambda_stack=plotting_lambda_stack)

app.synth()