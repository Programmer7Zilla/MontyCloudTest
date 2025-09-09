#!/usr/bin/env python3
"""
Test script for the Image Service API
"""
import requests
import base64
import json
import time
from pathlib import Path

API_BASE_URL = "http://localhost:4566/restapis/{api_id}/dev/_user_request_"
TEST_USER_ID = "user123"

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def create_test_image():
    from PIL import Image
    import io
    
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return base64.b64encode(img_bytes.getvalue()).decode('utf-8')

def test_upload_image(api_url):
    image_data = create_test_image()
    
    payload = {
        "user_id": TEST_USER_ID,
        "title": "Test Image",
        "description": "This is a test image",
        "tags": ["test", "demo", "red"],
        "image_data": image_data,
        "filename": "test_image.png"
    }
    
    response = requests.post(f"{api_url}/images", json=payload)
    
    if response.status_code == 201:
        result = response.json()
        return result['image_id']
    else:
        return None

def test_list_images(api_url):
    
    response = requests.get(f"{api_url}/images")
    if response.status_code == 200:
        result = response.json()
        
        response = requests.get(f"{api_url}/images?user_id={TEST_USER_ID}")
        if response.status_code == 200:
            result = response.json()
        
        response = requests.get(f"{api_url}/images?tags=test,demo")
        if response.status_code == 200:
            result = response.json()
        
        response = requests.get(f"{api_url}/images?title=test")
        if response.status_code == 200:
            result = response.json()
    else:
        print(f" Listing failed: {response.status_code} - {response.text}")

def test_view_image(api_url, image_id):
    if not image_id:
        print("\nSkipping view test - no image ID available")
        return
        
    print(f"\nTesting image viewing")
    response = requests.get(f"{api_url}/images/{image_id}?metadata_only=true")
    if response.status_code == 200:
        print("✓ Retrieved metadata only")
    else:
        print(f"Failed: {response.status_code}")
    

    response = requests.get(f"{api_url}/images/{image_id}")
    if response.status_code == 200:
        result = response.json()
    else:
        print(f"Failed: {response.status_code}")
    
    payload = {
        "user_id": TEST_USER_ID
    }
    
    response = requests.delete(f"{api_url}/images/{image_id}", json=payload)
    if response.status_code == 200:
        print("✓ Image deleted successfully")
    else:
        print(f"❌ Deletion failed: {response.status_code} - {response.text}")

def get_api_id():
    try:
        import boto3
        apigateway = boto3.client(
            'apigateway',
            endpoint_url='http://localhost:4566',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
        
        apis = apigateway.get_rest_apis()
        for api in apis['items']:
            if api['name'] == 'image-service-api':
                return api['id']
        
        return None
        
    except Exception as e:
        return None

def main():

    api_id = get_api_id()
    if not api_id:
        return
    api_url = API_BASE_URL.format(api_id=api_id)

    time.sleep(1)
    
    # Run tests
    image_id = test_upload_image(api_url)
    test_list_images(api_url)
    test_view_image(api_url, image_id)
    
    print("Test suite completed!")

if __name__ == "__main__":
    main()
