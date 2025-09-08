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

        user_id = body.get('user_id')
        title = body.get('title', '')
        description = body.get('description', '')
        tags = body.get('tags', [])
        image_data = body.get('image_data') 
        filename = body.get('filename')
        
        if not all([user_id, image_data, filename]):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required fields: user_id, image_data, filename'
                })
            }
        
        image_id = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1].lower()
        content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        if file_extension not in allowed_extensions:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'File type not allowed. Allowed types: {list(allowed_extensions)}'
                })
            }
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid base64 image data'
                })
            }
        if len(image_bytes) > 10 * 1024 * 1024:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'File size exceeds 10MB limit'
                })
            }
        s3_key = f"images/{user_id}/{image_id}{file_extension}"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=image_bytes,
            ContentType=content_type,
            Metadata={
                'user_id': user_id,
                'title': title,
                'description': description
            }
        )
        timestamp = datetime.utcnow().isoformat()
        
        metadata_item = {
            'image_id': image_id,
            'user_id': user_id,
            's3_key': s3_key,
            'filename': filename,
            'title': title,
            'description': description,
            'tags': tags,
            'content_type': content_type,
            'file_size': len(image_bytes),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        table.put_item(Item=metadata_item)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Image uploaded successfully',
                'image_id': image_id,
                'metadata': metadata_item
            })
        }
        
    except ClientError as e:
        print(f"AWS Client Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to upload image',
                'details': str(e)
            })
        }
    
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
