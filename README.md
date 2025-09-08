# Instagram-like Image Service

A scalable image upload and storage service built with Python, AWS services (API Gateway, Lambda, S3, DynamoDB), and LocalStack for local development.

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

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd MontyCloudTest
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start LocalStack**:
   ```bash
   docker-compose up -d
   ```

4. **Setup AWS infrastructure**:
   ```bash
   python setup_infrastructure.py
   ```

5. **Run tests** (optional):
   ```bash
   python test_api.py
   ```

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

### 2. List Images

**Basic listing**:
```bash
curl http://localhost:portno/restapis/{api_id}/dev/_user_request_/images
```

**Filter by user**:
```bash
curl "http://localhost:{portno}/restapis/{api_id}/dev/_user_request_/images?user_id=user123"
```

**Filter by tags**:
```bash
curl "http://localhost:{portno}/restapis/{api_id}/dev/_user_request_/images?tags=sunset,nature"
```

**Search by title**:
```bash
curl "http://localhost:{portno}/restapis/{api_id}/dev/_user_request_/images?title=photo"
```

**Date range filter**:
```bash
curl "http://localhost:{portno}/restapis/{api_id}/dev/_user_request_/images?date_from=2025-09-01&date_to=2025-09-30"
```

### 3. View Image

**Get metadata only**:
```bash
curl "http://localhost:{portno}/restapis/{api_id}/dev/_user_request_/images/{image_id}?metadata_only=true"
```

**Get full image data**:
```bash
curl http://localhost:{portno}/restapis/{api_id}/dev/_user_request_/images/{image_id}
```

**Download image**:
```bash
curl "http://localhost:{portno}/restapis/{api_id}/dev/_user_request_/images/{image_id}?download=true" \
  --output downloaded_image.jpg
```

### 4. Delete Image

```bash
curl -X DELETE http://localhost:{portno}/restapis/{api_id}/dev/_user_request_/images/{image_id} \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123"
  }'
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

**Global Secondary Indexes**:
- `user-id-index`: Allows querying by `user_id` with `created_at` as sort key

## Filtering Options

The `/images` endpoint supports the following query parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `user_id` | String | Filter by user ID | `?user_id=user123` |
| `tags` | String | Comma-separated tags | `?tags=sunset,nature` |
| `date_from` | String | Start date (ISO format) | `?date_from=2025-09-01` |
| `date_to` | String | End date (ISO format) | `?date_to=2025-09-30` |
| `title` | String | Search in title (partial match) | `?title=photo` |
| `limit` | Integer | Maximum results (default: 50) | `?limit=100` |

## Scalability Features

1. **Serverless Architecture**: Auto-scaling Lambda functions
2. **Global Secondary Indexes**: Efficient querying by user and tags
3. **S3 Storage**: Virtually unlimited image storage
4. **API Gateway**: Built-in rate limiting and caching
5. **NoSQL Database**: Horizontal scaling with DynamoDB

## Security Considerations

1. **User Authorization**: Users can only delete their own images
2. **File Type Validation**: Only allowed image formats accepted
3. **File Size Limits**: 10MB maximum file size
4. **Input Validation**: Comprehensive validation of all inputs

## Development

### Running Tests

```bash
python test_api.py
```

### Adding New Features

1. Create new Lambda function in `lambda_functions/`
2. Update `setup_infrastructure.py` to deploy the function
3. Add API Gateway routes if needed
4. Update tests in `test_api.py`

### Monitoring

LocalStack provides logs for all services. Check Docker logs:

```bash
docker-compose logs -f localstack
```

## Troubleshooting

### Common Issues

1. **LocalStack not responding**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. **Infrastructure setup fails**:
   ```bash
   # Wait for LocalStack to be fully ready
   sleep 10
   python setup_infrastructure.py
   ```

3. **Lambda function errors**:
   - Check CloudWatch logs in LocalStack
   - Verify environment variables are set correctly

### Health Check

```bash
curl http://localhost:{portno}/health
``

## License

This project is licensed under the MIT License.
