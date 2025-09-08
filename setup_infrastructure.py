#!/usr/bin/env python3
import boto3
import json
import time
import os
import zipfile
import shutil
from botocore.exceptions import ClientError

LOCALSTACK_ENDPOINT = "http://localhost:4566"
AWS_REGION = "us-east-1"
S3_BUCKET_NAME = "image-storage-bucket"
DYNAMODB_TABLE_NAME = "image-metadata"
LAMBDA_FUNCTIONS = [
    {
        'name': 'upload-image',
        'file': 'lambda_functions/upload_image.py',
        'handler': 'upload_image.lambda_handler',
        'description': 'Upload image with metadata'
    },
    {
        'name': 'list-images',
        'file': 'lambda_functions/list_images.py',
        'handler': 'list_images.lambda_handler',
        'description': 'List images with filtering'
    },
    {
        'name': 'view-image',
        'file': 'lambda_functions/view_image.py',
        'handler': 'view_image.lambda_handler',
        'description': 'View/download image'
    },
    {
        'name': 'delete-image',
        'file': 'lambda_functions/delete_image.py',
        'handler': 'delete_image.lambda_handler',
        'description': 'Delete image'
    }
]

def get_clients():
    common_config = {
        'endpoint_url': LOCALSTACK_ENDPOINT,
        'aws_access_key_id': 'test',
        'aws_secret_access_key': 'test',
        'region_name': AWS_REGION
    }
    
    return {
        's3': boto3.client('s3', **common_config),
        'dynamodb': boto3.client('dynamodb', **common_config),
        'lambda': boto3.client('lambda', **common_config),
        'apigateway': boto3.client('apigateway', **common_config),
        'iam': boto3.client('iam', **common_config)
    }

def create_s3_bucket(s3_client):
    try:
        print(f"Creating S3 bucket: {S3_BUCKET_NAME}")
        s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/images/*"
                }
            ]
        }
        
        s3_client.put_bucket_policy(
            Bucket=S3_BUCKET_NAME,
            Policy=json.dumps(bucket_policy)
        )
        
        print(f"✓ S3 bucket '{S3_BUCKET_NAME}' created successfully")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyExists':
            print(f"✓ S3 bucket '{S3_BUCKET_NAME}' already exists")
        else:
            raise

def create_dynamodb_table(dynamodb_client):
    try:
        print(f"Creating DynamoDB table: {DYNAMODB_TABLE_NAME}")
        
        table_definition = {
            'TableName': DYNAMODB_TABLE_NAME,
            'KeySchema': [
                {
                    'AttributeName': 'image_id',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'image_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'user-id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_at',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            'BillingMode': 'PROVISIONED',
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
        
        dynamodb_client.create_table(**table_definition)
        print(f"✓ DynamoDB table '{DYNAMODB_TABLE_NAME}' created successfully")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"✓ DynamoDB table '{DYNAMODB_TABLE_NAME}' already exists")
        else:
            raise

def create_lambda_execution_role(iam_client):
    """Create IAM role for Lambda execution"""
    role_name = "lambda-execution-role"
    
    try:
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        print(f"Creating IAM role: {role_name}")
        iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description="Execution role for Lambda functions"
        )
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        custom_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:{AWS_REGION}:000000000000:table/{DYNAMODB_TABLE_NAME}",
                        f"arn:aws:dynamodb:{AWS_REGION}:000000000000:table/{DYNAMODB_TABLE_NAME}/index/*"
                    ]
                }
            ]
        }
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="CustomLambdaPolicy",
            PolicyDocument=json.dumps(custom_policy)
        )
        print(f"✓ IAM role '{role_name}' created successfully")
        return f"arn:aws:iam::000000000000:role/{role_name}"
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"✓ IAM role '{role_name}' already exists")
            return f"arn:aws:iam::000000000000:role/{role_name}"
        else:
            raise

def create_lambda_deployment_package(function_file):
    temp_dir = "/tmp/lambda_package"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    shutil.copy(function_file, temp_dir)
    zip_file = f"/tmp/{os.path.basename(function_file)}.zip"
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    shutil.rmtree(temp_dir)
    
    return zip_file

def create_lambda_functions(lambda_client, role_arn):
    """Create Lambda functions"""
    function_arns = {}
    
    for func_config in LAMBDA_FUNCTIONS:
        try:
            print(f"Creating Lambda function: {func_config['name']}")
            zip_file = create_lambda_deployment_package(func_config['file'])
            with open(zip_file, 'rb') as f:
                zip_content = f.read()
            response = lambda_client.create_function(
                FunctionName=func_config['name'],
                Runtime='python3.9',
                Role=role_arn,
                Handler=func_config['handler'],
                Code={'ZipFile': zip_content},
                Description=func_config['description'],
                Timeout=30,
                MemorySize=512,
                Environment={
                    'Variables': {
                        'S3_BUCKET': S3_BUCKET_NAME,
                        'DYNAMODB_TABLE': DYNAMODB_TABLE_NAME,
                        'LOCALSTACK_ENDPOINT': LOCALSTACK_ENDPOINT
                    }
                }
            )
            
            function_arns[func_config['name']] = response['FunctionArn']
            print(f"✓ Lambda function '{func_config['name']}' created successfully")
            os.remove(zip_file)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print(f"✓ Lambda function '{func_config['name']}' already exists")
                # Get existing function ARN
                response = lambda_client.get_function(FunctionName=func_config['name'])
                function_arns[func_config['name']] = response['Configuration']['FunctionArn']
            else:
                raise
    
    return function_arns

def create_api_gateway(apigateway_client, lambda_client, function_arns):
    """Create API Gateway with Lambda integrations"""
    try:
        print("Creating API Gateway")
        api_response = apigateway_client.create_rest_api(
            name='image-service-api',
            description='Image upload and management service API'
        )
        api_id = api_response['id']
        resources_response = apigateway_client.get_resources(restApiId=api_id)
        root_resource_id = None
        for resource in resources_response['items']:
            if resource['path'] == '/':
                root_resource_id = resource['id']
                break
        images_resource = apigateway_client.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart='images'
        )
        images_resource_id = images_resource['id']
        image_id_resource = apigateway_client.create_resource(
            restApiId=api_id,
            parentId=images_resource_id,
            pathPart='{image_id}'
        )
        image_id_resource_id = image_id_resource['id']
        methods = [
            {
                'resource_id': images_resource_id,
                'method': 'POST',
                'function_name': 'upload-image',
                'description': 'Upload a new image'
            },
            {
                'resource_id': images_resource_id,
                'method': 'GET',
                'function_name': 'list-images',
                'description': 'List images with filtering'
            },
            {
                'resource_id': image_id_resource_id,
                'method': 'GET',
                'function_name': 'view-image',
                'description': 'View or download image'
            },
            {
                'resource_id': image_id_resource_id,
                'method': 'DELETE',
                'function_name': 'delete-image',
                'description': 'Delete image'
            }
        ]
        
        for method_config in methods:
            apigateway_client.put_method(
                restApiId=api_id,
                resourceId=method_config['resource_id'],
                httpMethod=method_config['method'],
                authorizationType='NONE'
            )
            function_arn = function_arns[method_config['function_name']]
            integration_uri = f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{function_arn}/invocations"         
            apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=method_config['resource_id'],
                httpMethod=method_config['method'],
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=integration_uri
            )
            try:
                lambda_client.add_permission(
                    FunctionName=method_config['function_name'],
                    StatementId=f"api-gateway-{method_config['method']}-{method_config['resource_id']}",
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f"arn:aws:execute-api:{AWS_REGION}:000000000000:{api_id}/*/*"
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceConflictException':
                    raise
        deployment = apigateway_client.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Development stage'
        )
        
        api_url = f"{LOCALSTACK_ENDPOINT}/restapis/{api_id}/dev/_user_request_"
        print(f"✓ API Gateway created successfully")
        print(f"API URL: {api_url}")
        
        return api_id, api_url
        
    except ClientError as e:
        print(f"Error creating API Gateway: {e}")
        raise

def main():
    """Main setup function"""
    print("Setting up AWS infrastructure in LocalStack...")
    print("=" * 50)
    clients = get_clients()
    
    try:
        create_s3_bucket(clients['s3'])
        create_dynamodb_table(clients['dynamodb'])
        time.sleep(2)
        role_arn = create_lambda_execution_role(clients['iam'])
        time.sleep(2)
        function_arns = create_lambda_functions(clients['lambda'], role_arn)
        api_id, api_url = create_api_gateway(clients['apigateway'], clients['lambda'], function_arns)
        print("\n" + "=" * 50)
        print("✓ Setup completed successfully!")
        print("\nAPI Endpoints:")
        print(f"POST   {api_url}/images          - Upload image")
        print(f"GET    {api_url}/images          - List images")
        print(f"GET    {api_url}/images/{{id}}     - View/download image")
        print(f"DELETE {api_url}/images/{{id}}     - Delete image")
        print("\nResources created:")
        print(f"- S3 Bucket: {S3_BUCKET_NAME}")
        print(f"- DynamoDB Table: {DYNAMODB_TABLE_NAME}")
        print(f"- Lambda Functions: {', '.join(function_arns.keys())}")
        print(f"- API Gateway: {api_id}")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        raise

if __name__ == "__main__":
    main()
