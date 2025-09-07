import json
import boto3
import os
from botocore.exceptions import ClientError

S3_BUCKET = os.environ.get('S3_BUCKET', 'image-storage-bucket')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'image-metadata')
LOCALSTACK_ENDPOINT = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')

def get_clients():
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
        image_id = event['pathParameters']['image_id']
        if event.get('body'):
            body = json.loads(event['body'])
            requesting_user_id = body.get('user_id')
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'user_id is required in request body for authorization'
                })
            }
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
        
        if metadata['user_id'] != requesting_user_id:
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Unauthorized: You can only delete your own images'
                })
            }
        
        s3_key = metadata['s3_key']

        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        except ClientError as e:
            print(f"Warning: Failed to delete image from S3: {e}")
        
        table.delete_item(Key={'image_id': image_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Image deleted successfully',
                'image_id': image_id,
                'deleted_metadata': dict(metadata)
            })
        }
        
    except Exception as e:
        print(f"Error deleting image: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to delete image',
                'details': str(e)
            })
        }
