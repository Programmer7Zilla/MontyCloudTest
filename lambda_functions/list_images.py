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
            items = []
        
        filtered_items = []
        
        for item in items:
            include_item = True
            if user_id and include_item:
                if item.get('user_id') != user_id:
                    include_item = False
            if tags_filter and include_item:
                search_tags = [tag.strip().lower() for tag in tags_filter.split(',')]
                item_tags = [tag.lower() for tag in item.get('tags', [])]
                if not any(tag in item_tags for tag in search_tags):
                    include_item = False
            if (date_from or date_to) and include_item:
                item_date = item.get('created_at', '')
                if date_from and item_date < date_from:
                    include_item = False
                if date_to and item_date > date_to:
                    include_item = False
            if title_search and include_item:
                item_title = item.get('title', '').lower()
                if title_search.lower() not in item_title:
                    include_item = False
            if include_item:
                filtered_items.append(item)
        filtered_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        response_data = {
            'images': filtered_items,
            'count': len(filtered_items),
            'filters_applied': {
                'user_id': user_id,
                'tags': tags_filter,
                'date_from': date_from,
                'date_to': date_to,
                'title_search': title_search
            }
        }
        
        print(f"Returning {len(filtered_items)} images")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data, cls=DecimalEncoder)
        }
        
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
