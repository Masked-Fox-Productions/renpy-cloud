# Deployment Guide

Complete guide to deploying renpy-cloud for your game.

## Overview

Deploying renpy-cloud involves:
1. Deploying the AWS backend infrastructure
2. Installing the client library in your game
3. Configuring your game with the deployment outputs
4. Testing the integration

## Prerequisites

### AWS Account
- Create an AWS account: https://aws.amazon.com/
- Configure billing alerts (recommended)
- Set up IAM user with appropriate permissions

### Development Tools
- **Node.js 18+**: For Serverless Framework
- **Python 3.8+**: For the client library
- **AWS CLI**: Configured with credentials
- **Ren'Py SDK**: For game development

### AWS CLI Setup

```bash
# Install AWS CLI
pip install awscli

# Configure with your credentials
aws configure
```

You'll need:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Output format: `json`

## Step 1: Deploy Backend Infrastructure

### 1.1 Install Serverless Framework

```bash
npm install -g serverless
```

Verify installation:
```bash
serverless --version
```

### 1.2 Deploy to AWS

```bash
cd infra
serverless deploy
```

This will take 5-10 minutes and create:
- Cognito User Pool and App Client
- API Gateway HTTP API
- Lambda functions
- DynamoDB table
- S3 bucket with versioning

### 1.3 Capture Outputs

After deployment, save these values:

```
Service Information
api: https://xxxxx.execute-api.us-east-1.amazonaws.com

Stack Outputs:
ApiEndpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com
CognitoUserPoolId: us-east-1_XXXXXXX
CognitoAppClientId: YYYYYYYYYYYYYYYYYYYYYYYY
Region: us-east-1
```

Save these to a secure location - you'll need them for client configuration.

## Step 2: Install Client Library

### Option A: Install via pip (Recommended)

```bash
pip install renpy-cloud
```

### Option B: Vendor into Game

Copy the `renpy_cloud` directory into your game directory:

```
your_game/
├── game/
│   ├── renpy_cloud/     # Copy here
│   └── script.rpy
└── ...
```

## Step 3: Configure Your Game

### 3.1 Add Configuration

In your `script.rpy` or a separate config file:

```python
init python:
    import renpy_cloud
    
    renpy_cloud.configure(
        api_base_url="https://xxxxx.execute-api.us-east-1.amazonaws.com",
        game_id="your_unique_game_id",  # Choose a unique ID
        aws_region="us-east-1",
        cognito_user_pool_id="us-east-1_XXXXXXX",
        cognito_app_client_id="YYYYYYYYYYYYYYYYYYYYYYYY",
    )
```

Replace the placeholder values with your actual AWS deployment outputs.

### 3.2 Add Sync Hooks

```python
# Sync on game start
label start:
    $ renpy_cloud.sync_on_start()
    # ... rest of your game

# Sync on quit
init python:
    config.quit_action = renpy_cloud.sync_on_quit
```

### 3.3 Add Login/Signup UI

See `example_game/script.rpy` for a complete example with login screens.

Minimum implementation:

```python
# Login function
python:
    def login():
        try:
            if renpy_cloud.login(username, password):
                renpy.notify("Logged in!")
        except renpy_cloud.AuthenticationError as e:
            renpy.notify(f"Login failed: {e}")
```

## Step 4: Test Integration

### 4.1 Test Signup

1. Run your game
2. Open signup screen
3. Create an account with:
   - Valid username
   - Email address
   - Password (8+ chars, upper+lower+number)
4. Check email for verification (if enabled)

### 4.2 Test Login

1. Log in with your credentials
2. Check console for sync messages
3. Create a save file
4. Force a sync or wait 5 minutes

### 4.3 Test Cross-Device Sync

1. **Device A**: Log in and create a save
2. **Device A**: Force sync or quit game
3. **Device B**: Log in with same account
4. **Device B**: Saves should download automatically

### 4.4 Check Logs

Look for renpy-cloud messages in the Ren'Py console:

```
[renpy-cloud] Sync completed successfully
[renpy-cloud] Uploaded: persistent
[renpy-cloud] Downloaded: 1-1-LT1.save
```

## Step 5: Production Checklist

Before releasing your game with cloud saves:

### Security
- [ ] Store AWS config securely (don't commit to git)
- [ ] Use environment variables for sensitive values
- [ ] Enable Cognito email verification
- [ ] Set up Cognito password policies
- [ ] Review IAM permissions

### Testing
- [ ] Test login/signup flow
- [ ] Test sync with multiple devices
- [ ] Test offline behavior
- [ ] Test conflict resolution
- [ ] Test with slow/unstable network

### Monitoring
- [ ] Set up CloudWatch alarms
- [ ] Configure billing alerts
- [ ] Set up error notifications
- [ ] Monitor API Gateway metrics

### User Experience
- [ ] Add loading indicators during sync
- [ ] Show clear error messages
- [ ] Add sync status display
- [ ] Provide manual sync button
- [ ] Add "Skip" option for cloud saves

### Documentation
- [ ] Add privacy policy
- [ ] Document cloud save feature
- [ ] Provide troubleshooting guide
- [ ] Include contact support info

### Legal
- [ ] Review AWS terms of service
- [ ] Update privacy policy for cloud storage
- [ ] Inform users about data storage
- [ ] Provide data deletion mechanism

## Multiple Environments

### Development Environment

```bash
cd infra
serverless deploy --stage dev
```

Use these outputs in your dev builds.

### Production Environment

```bash
cd infra
serverless deploy --stage production
```

Use these outputs in your production builds.

### Staging Environment

```bash
cd infra
serverless deploy --stage staging
```

Use for QA testing before production.

## Cost Management

### Estimate Costs

Use the AWS Pricing Calculator: https://calculator.aws/

Typical costs for a small game (100 users):
- API Gateway: ~$0.10/month
- Lambda: ~$0.50/month
- DynamoDB: ~$1.00/month
- S3: ~$0.50/month
- **Total: ~$2.10/month**

### Set Up Billing Alerts

1. Go to AWS Billing Console
2. Create billing alarm
3. Set threshold (e.g., $10/month)
4. Add email notification

### Monitor Usage

Check AWS Cost Explorer:
```bash
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

## Backup Strategy

### DynamoDB Backups

Enable point-in-time recovery:

```bash
aws dynamodb update-continuous-backups \
  --table-name renpy-cloud-dev-manifests \
  --point-in-time-recovery-enabled
```

### S3 Versioning

Already enabled by default in `serverless.yml`. Old versions are kept for 90 days.

### Export Backups

Periodically export user data:

```bash
aws s3 sync s3://renpy-cloud-dev-save-files ./backups/
```

## Updating

### Update Lambda Code

After changing handler code:

```bash
cd infra
serverless deploy
```

### Update Client Library

After updating renpy-cloud package:

```bash
pip install --upgrade renpy-cloud
```

Or update the vendored copy in your game.

## Rollback

### Rollback Infrastructure

```bash
cd infra
serverless rollback
```

### Rollback to Specific Deployment

```bash
serverless rollback --timestamp 1234567890
```

## Troubleshooting

### Deployment Issues

**Problem**: "Access Denied" error during deployment

**Solution**: Check IAM permissions. Required permissions:
- CloudFormation
- Lambda
- API Gateway
- S3
- DynamoDB
- Cognito
- IAM (for role creation)

**Problem**: Stack creation timeout

**Solution**: Check CloudWatch logs for the failed resource. Common issues:
- Lambda deployment package too large
- VPC configuration issues
- Resource limits reached

### Runtime Issues

**Problem**: "Not configured" error

**Solution**: Ensure `renpy_cloud.configure()` is called before any other operations.

**Problem**: Authentication fails

**Solution**:
- Verify Cognito IDs are correct
- Check user confirmed email
- Try resetting password in AWS Console

**Problem**: Sync doesn't work

**Solution**:
- Check authentication status
- Verify network connectivity
- Check Lambda logs for errors
- Ensure save directory is correct

## Cleanup

To remove all AWS resources:

```bash
cd infra
serverless remove
```

**WARNING**: This permanently deletes:
- All user accounts
- All save files
- All manifests
- All logs

Consider exporting data first!

## Getting Help

### Resources
- Documentation: README.md
- Example game: example_game/
- Contributing guide: CONTRIBUTING.md
- Infrastructure docs: infra/README.md

### Support
- GitHub Issues: Report bugs and request features
- AWS Support: For AWS-specific issues
- Community: Discord/Reddit for game dev communities

## Next Steps

After deployment:
1. Test thoroughly in development
2. Deploy to staging for QA
3. Monitor for a few days
4. Deploy to production
5. Announce cloud save feature to players
6. Monitor usage and costs
7. Iterate based on feedback

Good luck with your deployment! 🚀☁️

