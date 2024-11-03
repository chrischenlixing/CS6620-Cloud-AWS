from aws_cdk import Stack
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_lambda import Function
from constructs import Construct
import aws_cdk.aws_s3 as s3

class S3Stack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # S3 bucket definition
        self.bucket = Bucket(self, "Assignment4Bucket")

        self.plottedBucket = Bucket(self, "plottedBucket")

        self.bucket_name = self.bucket.bucket_name
        self.plotted_bucket_name = self.plottedBucket.bucket_name
