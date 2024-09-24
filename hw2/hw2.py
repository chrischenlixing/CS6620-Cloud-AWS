import boto3
import json
from botocore.client import ClientError

iam_client = boto3.client('iam')
s3_client = boto3.client('s3')
sts_client = boto3.client('sts')

def get_account_id():
    return sts_client.get_caller_identity()['Account']

def create_iam_roles(role_name, policy_arn, trust_user_arn=None):
    try:
        role = iam_client.get_role(RoleName=role_name)
        print(f"Role {role_name} already exists. Skipping creation.")
        return role['Role']['Arn']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"Creating role {role_name}")
            if trust_user_arn:
                assume_role_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": trust_user_arn},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
            else:
                assume_role_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "ec2.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }

            role = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy)
            )

            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            return role['Role']['Arn']
        else:
            raise e

def attach_policy_to_roles():
    account_id = get_account_id()
    user_arn = f"arn:aws:iam::{account_id}:user/chrischenlixing"
    
    create_iam_roles('Dev', 'arn:aws:iam::aws:policy/AmazonS3FullAccess', trust_user_arn=user_arn)
    
    create_iam_roles('User', 'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess', trust_user_arn=user_arn)

def create_iam_user(username):
    account_id = get_account_id() 
    try:
        user = iam_client.get_user(UserName=username)
        print(f"IAM User {username} already exists. Skipping creation.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            user = iam_client.create_user(UserName=username)
            print(f'IAM User {username} created successfully')

    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect":"Allow",
                "Action":"sts:AssumeRole",
                "Resource":"*"
            }
        ]
    }

    try:
        iam_client.put_user_policy(
            UserName=username,
            PolicyName='AssumeUserRolePolicy',
            PolicyDocument=json.dumps(assume_role_policy)
        )
        print(f'Policy AssumeUserRolePolicy attached to user {username}')
    except ClientError as e:
        print(f'Failed to attach policy: {e}')
        raise e

def upload_files_to_bucket(dev_s3_client, bucket_name):
    dev_s3_client.put_object(
        Bucket=bucket_name,
        Key='assignment1.txt',
        Body='Empty Assignment 1'
    )
    print('assignment1.txt uploaded successfully')

    dev_s3_client.put_object(
        Bucket=bucket_name,
        Key='assignment2.txt',
        Body='Empty Assignment 2'
    )
    print('assignment2.txt uploaded successfully')

    with open('recording1.jpg', 'rb') as img_file:
        dev_s3_client.put_object(
            Bucket=bucket_name,
            Key='recording1.jpg',
            Body=img_file
        )
    print('recording1.jpg uploaded successfully')

def assume_dev_role_and_create_s3_resources():
    account_id = get_account_id() 

    dev_role_arn = f"arn:aws:iam::{account_id}:role/Dev"

    assumed_role = sts_client.assume_role(
        RoleArn=dev_role_arn,
        RoleSessionName="AssumeDevRoleSession"
    )
 
    credentials = assumed_role['Credentials']
    dev_s3_client = boto3.client(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name='us-west-2'
    )
    bucket_name = 'lecture1233'

    # Handle bucket creation with existence check
    try:
        dev_s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'us-west-2'})
        print(f'S3 bucket {bucket_name} created successfully')
    except ClientError as e:
        if e.response['Error']['Code'] in ['BucketAlreadyExists', 'BucketAlreadyOwnedByYou']:
            print(f"S3 bucket {bucket_name} already exists. Skipping creation.")
        else:
            raise e

    upload_files_to_bucket(dev_s3_client, bucket_name)

def assume_user_role_and_calculate_objects_size():
    account_id = get_account_id() 

    user_role_arn = f"arn:aws:iam::{account_id}:role/User"

    assumed_role = sts_client.assume_role(
        RoleArn=user_role_arn,
        RoleSessionName="AssumeUserRoleSession"
    )

    credentials = assumed_role['Credentials']
    user_s3_client = boto3.client(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name='us-west-2'
    )
    bucket_name = 'lecture1233'

    objects = user_s3_client.list_objects_v2(Bucket=bucket_name)
    total_size = 0
    for obj in objects['Contents']:
        total_size += obj['Size']

    print(f"Total size of objects in {bucket_name}: {total_size} bytes")

def assume_dev_role_and_delete_objects():
    account_id = get_account_id()

    dev_role_arn = f"arn:aws:iam::{account_id}:role/Dev"

    assumed_role = sts_client.assume_role(
        RoleArn=dev_role_arn,
        RoleSessionName="AssumeDevRoleSession"
    )

    credentials = assumed_role['Credentials']
    dev_s3_client = boto3.client(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name='us-west-2'
    )
    bucket_name = 'lecture1233'
    try:
        objects = dev_s3_client.list_objects_v2(Bucket=bucket_name)
        for obj in objects['Contents']:
            dev_s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
            print(f"Object {obj['Key']} deleted successfully")
    except ClientError as e:
        print(f"Failed to delete objects: {e}")
        raise e
    
if __name__ == '__main__':
    attach_policy_to_roles()
    create_iam_user('chrischenlixing')
    assume_dev_role_and_create_s3_resources()
    assume_user_role_and_calculate_objects_size()
    assume_dev_role_and_delete_objects()