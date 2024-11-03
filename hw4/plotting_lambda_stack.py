from aws_cdk import Stack, Duration
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import LambdaRestApi
from constructs import Construct
from dynamodb_stack import DynamoDBStack
from s3_stack import S3Stack

class PlottingLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, dynamodb_stack: DynamoDBStack, s3_stack: S3Stack, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Plotting Lambda
        self.plotting_lambda = Function(
            self, "PlottingLambda",
            runtime=Runtime.PYTHON_3_8,
            handler="plotting.lambda_handler",
            timeout=Duration.seconds(300), 
            code=Code.from_asset("lambda"), 
            environment={
                'DYNAMODB_TABLE_NAME': dynamodb_stack.table.table_name,
                'PLOT_BUCKET_NAME': s3_stack.plottedBucket.bucket_name,
                'BUCKET_NAME': s3_stack.bucket_name
            }
        )

        # Grant S3 and DynamoDB permissions
        s3_stack.bucket.grant_read_write(self.plotting_lambda)
        s3_stack.plottedBucket.grant_read_write(self.plotting_lambda)
        dynamodb_stack.table.grant_read_write_data(self.plotting_lambda)

        # API Gateway for Plotting Lambda
        api = LambdaRestApi(
            self, "PlottingApi",
            handler=self.plotting_lambda,
            proxy=False,
            description="API for invoking the Plotting Lambda"
        )

        # Define a resource and method for the API
        plotting_resource = api.root.add_resource("plot")
        plotting_resource.add_method("POST")  # Define HTTP method(s) allowed

        # Export the API URL to reference in the Driver Lambda Stack
        self.api_url = api.url