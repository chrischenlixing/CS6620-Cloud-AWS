from aws_cdk import App
from storage_stack import StorageStack
from replicator_stack import ReplicatorStack
from cleaner_stack import CleanerStack

app = App()

# Instantiate StorageStack
storage_stack = StorageStack(app, 'StorageStack')

# Instantiate ReplicatorStack (as a reference holder)
replicator_stack = ReplicatorStack(app, 'ReplicatorStack')
replicator_stack.add_dependency(storage_stack)

# Instantiate CleanerStack
cleaner_stack = CleanerStack(app, 'CleanerStack',
    destination_bucket=storage_stack.bucket_dst,
    table=storage_stack.table_t
)
cleaner_stack.add_dependency(storage_stack)

app.synth()