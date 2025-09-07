import json
import boto3
import base64
import os
from botocore.exceptions import ClientError

# Configuration
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
    """
    Lambda handler for viewing/downloading images
    Supports two modes:
    1. metadata_only=true - returns only metadata
    2. metadata_only=false/not provided - returns metadata + base64 encoded image
    """
    try:
        # Initialize clients
        s3_client, dynamodb = get_clients()
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        # Extract image_id from path parameters
        image_id = event['pathParameters']['image_id']
        
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        metadata_only = query_params.get('metadata_only', 'false').lower() == 'true'
        download = query_params.get('download', 'false').lower() == 'true'
        
        # Get image metadata from DynamoDB
        response = table.get_item(Key={'image_id': image_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Image not found'
                })
            }
        
        metadata = response['Item']
        s3_key = metadata['s3_key']
        
        # If only metadata is requested
        if metadata_only:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'metadata': dict(metadata)
                })
            }
        
        # Get image from S3
        try:
            s3_response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
            image_data = s3_response['Body'].read()
            content_type = s3_response['ContentType']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Image file not found in storage'
                    })
                }
            raise
        
        # If download is requested, return binary data
        if download:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': content_type,
                    'Content-Disposition': f'attachment; filename="{metadata["filename"]}"',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': base64.b64encode(image_data).decode('utf-8'),
                'isBase64Encoded': True
            }
        
        # Return metadata with base64 encoded image for viewing
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        response_data = {
            'metadata': dict(metadata),
            'image_data': image_base64,
            'content_type': content_type
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"Error retrieving image: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve image',
                'details': str(e)
            })
        }
