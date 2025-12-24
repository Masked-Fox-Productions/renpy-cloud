# Example Ren'Py Game with Cloud Sync

This is a minimal example demonstrating how to integrate `renpy-cloud` into a Ren'Py game.

## Setup

### 1. Install renpy-cloud

Copy the `renpy_cloud` package into your game directory, or install via pip:

```bash
pip install renpy-cloud
```

### 2. Configure with Your AWS Deployment

Edit `script.rpy` and replace the placeholder values in the `renpy_cloud.configure()` call with your actual AWS deployment outputs:

```python
renpy_cloud.configure(
    api_base_url="https://YOUR-API-ID.execute-api.YOUR-REGION.amazonaws.com",
    game_id="your_game_id",  # Choose a unique ID for your game
    aws_region="YOUR-REGION",
    cognito_user_pool_id="YOUR-USER-POOL-ID",
    cognito_app_client_id="YOUR-APP-CLIENT-ID",
)
```

Get these values from your Serverless deployment output:

```bash
cd ../infra
serverless info
```

### 3. Run the Game

Open the `example_game` directory with Ren'Py Launcher and run it.

## Features Demonstrated

### Login/Signup
- User authentication with Amazon Cognito
- Account creation with email verification
- Secure password handling

### Automatic Sync
- Syncs every 5 minutes (configurable)
- Syncs on game quit
- Respects throttling to avoid excessive API calls

### Manual Sync
- Force sync button in the cloud status panel
- Immediate sync regardless of throttle interval

### Cloud Status Display
- Shows connection status
- Quick access to login/logout
- Force sync option

### Persistent Data
- Demonstrates syncing of `persistent` variables
- Visit counter that syncs across devices

## Integration Points

The key integration points in `script.rpy` are:

1. **Initialization** (in `init python` block):
   ```python
   renpy_cloud.configure(...)
   ```

2. **Sync on Start** (in `start` label):
   ```python
   renpy_cloud.sync_on_start()
   ```

3. **Sync on Quit** (in `init python` block):
   ```python
   config.quit_action = lambda: renpy_cloud.sync_on_quit()
   ```

4. **Login/Signup** (custom functions):
   ```python
   renpy_cloud.login(username, password)
   renpy_cloud.signup(username, password, email)
   ```

5. **Manual Sync** (custom function):
   ```python
   renpy_cloud.force_sync()
   ```

## Customization

You can customize:
- `sync_interval_seconds` - How often to sync (default: 300 seconds)
- `timeout_seconds` - Network timeout (default: 30 seconds)
- `max_retries` - Retry attempts for failed operations (default: 3)

## Testing

To test cross-device sync:

1. Run the game on device A
2. Log in and create a save
3. Wait for sync or force sync
4. Run the game on device B
5. Log in with the same account
6. Your saves should download automatically!

## Troubleshooting

### "Not configured" error
Make sure you've replaced the placeholder values in `renpy_cloud.configure()` with your actual AWS deployment outputs.

### Sync not working
- Check that you're logged in (cloud status shows "Connected")
- Verify your AWS backend is deployed: `cd infra && serverless info`
- Check the Ren'Py console for error messages
- Try forcing a sync manually

### Login fails
- Verify Cognito User Pool and App Client IDs are correct
- Check that the AWS region matches your deployment
- Ensure your password meets Cognito requirements (8+ chars, uppercase, lowercase, number)

## Production Considerations

For production games:

1. **Security**: Store AWS configuration securely, don't commit credentials
2. **Error Handling**: Add more robust error messages and user feedback
3. **UI Polish**: Customize the login/signup screens to match your game's aesthetic
4. **Testing**: Test with poor network conditions and offline scenarios
5. **Privacy**: Add a privacy policy and terms of service
6. **Cost**: Monitor AWS usage and set up billing alerts

