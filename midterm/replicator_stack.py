from aws_cdk import Stack, Fn, CfnOutput
from constructs import Construct

class ReplicatorStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Import references from StorageStack
        source_bucket_arn = Fn.import_value('SourceBucketArn')
        replicator_lambda_arn = Fn.import_value('ReplicatorLambdaArn')
        
        # Optionally output the imported ARNs in ReplicatorStack for visibility
        CfnOutput(self, 'ReplicatorLambdaImportedArn', value=replicator_lambda_arn, export_name='ReplicatorLambdaImportedArn')
