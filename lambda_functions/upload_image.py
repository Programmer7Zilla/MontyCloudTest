import json
import boto3
import base64
import uuid
import os
from datetime import datetime
from botocore.exceptions import ClientError
import mimetypes

S3_BUCKET = os.environ.get('S3_BUCKET', 'image-storage-bucket')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'image-metadata')
LOCALSTACK_ENDPOINT = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')

def get_clients():
    """Initialize AWS clients"""
    s3_client = boto3.client(
        's3',
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name='us-east-1'
    )
    
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name='us-east-1'
    )
    
    return s3_client, dynamodb

def lambda_handler(event, context):
    try:
        s3_client, dynamodb = get_clients()
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(event['body'])
        else:
            body = json.loads(event['body'])
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }
