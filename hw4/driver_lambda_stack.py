from aws_cdk import Stack, Duration
from aws_cdk.aws_lambda import Function, Runtime, Code
from constructs import Construct
from s3_stack import S3Stack
from plotting_lambda_stack import PlottingLambdaStack

class DriverLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, s3_stack: S3Stack, plotting_lambda_stack: PlottingLambdaStack, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Driver Lambda
        self.driver_lambda = Function(
            self, "DriverLambda",
            runtime=Runtime.PYTHON_3_8,
            handler="driver.lambda_handler",
            timeout=Duration.seconds(300), 
            code=Code.from_asset("lambda"),
            environment={
                'BUCKET_NAME': s3_stack.bucket_name,
                'PLOTTING_API_URL': plotting_lambda_stack.api_url  # Pass Plotting API URL as environment variable
            }
        )

        # Grant S3 permissions
        s3_stack.bucket.grant_read_write(self.driver_lambda)
        s3_stack.plottedBucket.grant_read_write(self.driver_lambda)