# renpy-cloud Infrastructure

AWS serverless backend for renpy-cloud using Serverless Framework.

## Architecture

The backend consists of:

- **Amazon Cognito**: User authentication and authorization
- **API Gateway (HTTP API)**: RESTful API endpoints with JWT authorization
- **AWS Lambda**: Serverless compute for sync logic
- **DynamoDB**: Stores file manifests and metadata
- **S3**: Stores actual save files with versioning enabled

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Node.js 18+ installed
- Serverless Framework v3+

## Installation

### 1. Install Serverless Framework

```bash
npm install -g serverless
# or use npx
```

### 2. Install Dependencies

```bash
cd infra
npm install
```

### 3. Install Python Dependencies

The Lambda functions require boto3 (included in Lambda runtime):

```bash
pip install -r requirements.txt
```

## Deployment

### Deploy to AWS

```bash
serverless deploy
```

This will:
1. Create CloudFormation stack
2. Provision all AWS resources
3. Deploy Lambda functions
4. Output configuration values

### Deploy to Specific Stage

```bash
serverless deploy --stage production
```

Stages help separate environments (dev, staging, prod).

### Get Deployment Info

```bash
serverless info
```

This shows:
- API endpoint URL
- Cognito User Pool ID
- Cognito App Client ID
- DynamoDB table name
- S3 bucket name

## Configuration

### Serverless.yml

Key configuration sections:

#### Provider Settings

```yaml
provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}
```

#### Functions

- `syncPlan`: Handles sync plan requests (POST /sync/plan)
- `syncComplete`: Handles sync completion (POST /sync/complete)

Both functions are protected by JWT authorization via Cognito.

#### Resources

- `CognitoUserPool`: User authentication
- `CognitoUserPoolClient`: App client for authentication
- `ManifestTable`: DynamoDB table for file manifests
- `SaveFilesBucket`: S3 bucket for save files

## API Endpoints

### POST /sync/plan

Request a sync plan by comparing local and remote manifests.

**Request:**
```json
{
  "game_id": "my_game",
  "manifest": {
    "persistent": {
      "path": "persistent",
      "size": 1024,
      "modified_timestamp": 1234567890.0,
      "checksum": "abc123..."
    }
  }
}
```

**Response:**
```json
{
  "uploads": [
    {
      "filename": "persistent",
      "upload_url": "https://s3.amazonaws.com/..."
    }
  ],
  "downloads": [
    {
      "filename": "1-1-LT1.save",
      "download_url": "https://s3.amazonaws.com/..."
    }
  ],
  "conflicts": [],
  "deletes": []
}
```

### POST /sync/complete

Notify backend that sync is complete (for logging/analytics).

**Request:**
```json
{
  "game_id": "my_game",
  "success": true,
  "error": null
}
```

**Response:**
```json
{
  "acknowledged": true
}
```

## Testing

### Unit Tests

```bash
cd ..
pytest tests/test_lambda_handlers.py
```

### Manual Testing with curl

Get an access token first (using Cognito SDK or manually), then:

```bash
curl -X POST https://YOUR-API.execute-api.us-east-1.amazonaws.com/sync/plan \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "test_game",
    "manifest": {}
  }'
```

## Monitoring

### View Logs

```bash
# Tail logs for syncPlan function
serverless logs -f syncPlan -t

# View last 100 lines
serverless logs -f syncPlan --startTime 1h
```

### CloudWatch

Logs are automatically sent to CloudWatch Logs:
- Log group: `/aws/lambda/renpy-cloud-{stage}-syncPlan`
- Log group: `/aws/lambda/renpy-cloud-{stage}-syncComplete`

### Metrics

Monitor in AWS Console:
- API Gateway: Request count, latency, errors
- Lambda: Invocations, duration, errors, throttles
- DynamoDB: Read/write capacity, throttles
- S3: Requests, data transfer

## Cost Optimization

### DynamoDB
- Uses PAY_PER_REQUEST billing mode
- No idle charges
- Scales automatically

### S3
- Lifecycle rule: Delete old versions after 90 days
- Versioning enabled for data protection

### Lambda
- Free tier: 1M requests/month
- Typical cost: $0.00001667/GB-second

### Estimated Monthly Costs

For a small game (100 active users):
- API Gateway: ~$0.10
- Lambda: ~$0.50
- DynamoDB: ~$1.00
- S3: ~$0.50
- **Total: ~$2.10/month**

For a larger game (10,000 users):
- API Gateway: ~$10
- Lambda: ~$15
- DynamoDB: ~$25
- S3: ~$5
- **Total: ~$55/month**

## Security

### Authentication
- JWT tokens from Cognito
- No AWS credentials on client
- Per-user isolation in S3/DynamoDB

### S3 Access
- Pre-signed URLs (5 minute expiry)
- No public access
- Versioning enabled

### API Gateway
- HTTPS only
- JWT authorizer on all endpoints
- CORS configured

### IAM
- Lambda has minimal required permissions
- Separate roles per function
- No wildcard permissions

## Maintenance

### Update Lambda Code

```bash
serverless deploy function -f syncPlan
```

### Update Configuration

Edit `serverless.yml`, then:

```bash
serverless deploy
```

### Backup

DynamoDB and S3 both have built-in redundancy, but consider:
- Point-in-time recovery for DynamoDB
- Cross-region replication for S3
- Regular exports to backup location

### Rollback

CloudFormation stores previous versions:

```bash
# List deployments
aws cloudformation list-stacks

# Rollback
serverless rollback
```

## Troubleshooting

### Deployment Fails

**Issue**: CloudFormation stack creation failed

**Solution**:
```bash
# Check stack events
aws cloudformation describe-stack-events --stack-name renpy-cloud-dev

# Delete failed stack
serverless remove

# Try again
serverless deploy
```

### Lambda Errors

**Issue**: Lambda function returns 500 errors

**Solution**:
```bash
# Check logs
serverless logs -f syncPlan -t

# Common issues:
# - Missing environment variables
# - IAM permission errors
# - Python import errors
```

### Cognito Issues

**Issue**: Authentication fails

**Solution**:
- Verify User Pool ID and Client ID are correct
- Check that `USER_PASSWORD_AUTH` flow is enabled
- Ensure user is confirmed (check email)

### DynamoDB Throttling

**Issue**: DynamoDB throttling errors

**Solution**:
- DynamoDB PAY_PER_REQUEST scales automatically
- Check for hot partitions
- Consider caching frequently accessed items

## Cleanup

Remove all resources:

```bash
serverless remove
```

This deletes:
- Lambda functions
- API Gateway
- DynamoDB table
- **S3 bucket (WARNING: This deletes all save files!)**
- Cognito User Pool
- IAM roles

Note: S3 buckets with versioning may require manual deletion of all versions first.

## Advanced Configuration

### Custom Domain

Add to `serverless.yml`:

```yaml
custom:
  customDomain:
    domainName: api.yourgame.com
    certificateName: '*.yourgame.com'
    basePath: ''
    stage: ${self:provider.stage}
    createRoute53Record: true
```

### VPC Configuration

For private resources:

```yaml
provider:
  vpc:
    securityGroupIds:
      - sg-xxxxxx
    subnetIds:
      - subnet-xxxxxx
      - subnet-yyyyyy
```

### Environment Variables

Add secrets:

```yaml
provider:
  environment:
    CUSTOM_SECRET: ${env:CUSTOM_SECRET}
```

### Rate Limiting

Add to API Gateway:

```yaml
provider:
  httpApi:
    throttle:
      rateLimit: 100
      burstLimit: 200
```

## Support

- GitHub Issues: https://github.com/yourusername/renpy-cloud/issues
- Documentation: https://github.com/yourusername/renpy-cloud#readme
- AWS Documentation: https://docs.aws.amazon.com/

