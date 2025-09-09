# 📸 Image Service API

A comprehensive image upload and management service with both serverless (Lambda + API Gateway) and Flask implementations.

## API Endpoints

| POST | `/images` | Upload image with metadata |
| GET | `/images` | List images with filtering |
| GET | `/images/{id}` | View/download specific image |
| DELETE | `/images/{id}` | Delete specific image |

Port no.4566

## Setup Instructions

### Prerequisites

1. **Docker & Docker Compose**: For running LocalStack
2. **Python 3.7+**: For running the application
3. **Git**: For version control

## Usage Examples

### 1. Upload Image

```bash
curl -X POST http://localhost:{portno}/restapis/{api_id}/dev/_user_request_/images \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "title": "My Photo",
    "description": "A beautiful sunset",
    "tags": ["sunset", "nature", "photography"],
    "image_data": "<base64-encoded-image>",
    "filename": "sunset.jpg"
  }'
```

**Response**:
```json
{
  "message": "Image uploaded successfully",
  "image_id": "uuid-string",
  "metadata": {
    "image_id": "uuid-string",
    "user_id": "user123",
    "title": "My Photo",
    "description": "A beautiful sunset",
    "tags": ["sunset", "nature", "photography"],
    "filename": "sunset.jpg",
    "content_type": "image/jpeg",
    "file_size": 1024576,
    "created_at": "2025-09-07T10:30:00.000Z"
  }
}
```

## Database Schema

### DynamoDB Table: `image-metadata`

**Primary Key**: `image_id` (String)

**Attributes**:
- `image_id`: Unique identifier for the image
- `user_id`: ID of the user who uploaded the image
- `s3_key`: S3 object key for the image file
- `filename`: Original filename
- `title`: Image title
- `description`: Image description
- `tags`: Array of tags
- `content_type`: MIME type of the image
- `file_size`: Size of the image in bytes
- `created_at`: Upload timestamp (ISO format)
- `updated_at`: Last update timestamp (ISO format)


## Development

### Running Tests

```bash
python test_api.py
```

