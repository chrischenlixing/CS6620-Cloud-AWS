from aws_cdk import App
from storage_stack import StorageStack
from replicator_stack import ReplicatorStack
from cleaner_stack import CleanerStack

app = App()

# Initialize StorageStack first without replicator_lambda initially
storage_stack = StorageStack(app, "StorageStack")

# Initialize ReplicatorStack with storage_stack
replicator_stack = ReplicatorStack(app, "ReplicatorStack", storage_stack=storage_stack)

# Now that replicator_lambda is created, add it to StorageStack for S3 event notifications
storage_stack.add_s3_event_notifications(replicator_stack.replicator_lambda)

# Initialize CleanerStack with storage_stack
cleaner_stack = CleanerStack(app, "CleanerStack", storage_stack=storage_stack)

app.synth()