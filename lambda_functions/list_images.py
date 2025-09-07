import json
import boto3
import os
from decimal import Decimal

DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'image-metadata')
LOCALSTACK_ENDPOINT = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')

def get_dynamodb():
    return boto3.resource(
        'dynamodb',
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name='us-east-1'
    )

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        
        dynamodb = get_dynamodb()
        table = dynamodb.Table(DYNAMODB_TABLE)
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id')
        tags_filter = query_params.get('tags')  
        date_from = query_params.get('date_from') 
        date_to = query_params.get('date_to') 
        title_search = query_params.get('title') 
        limit = int(query_params.get('limit', 50))  
        
        print(f"Query params: user_id={user_id}, tags={tags_filter}, limit={limit}")
        
        try:
            response = table.scan(Limit=limit)
            items = response.get('Items', [])
            print(f"Found {len(items)} items in table")
        except Exception as e:
            print(f"Error scanning table: {e}")
        
    except Exception as e:
        print(f"Error listing images: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to list images',
                'details': str(e)
            })
        }
