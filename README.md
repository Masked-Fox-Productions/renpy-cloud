# renpy-cloud

**Cloud save synchronization for Ren’Py games.**  
Think *Steam Cloud*, but lightweight, open, and serverless.

`renpy-cloud` provides a Python client library for Ren’Py games plus a deployable AWS backend that synchronizes:

- `persistent` data
- Active save slots only
- Across devices
- Securely, using Amazon Cognito

The design is intentionally minimal: small files, infrequent syncs, predictable conflict resolution.

---

## Features

- ☁️ Cloud sync for Ren’Py `persistent` and save files
- 🔐 Secure authentication via **Amazon Cognito**
- 📦 Serverless backend (API Gateway + Lambda + S3 + DynamoDB)
- 🧠 Smart sync planning (upload / download / noop)
- ⏱ Sync throttling (default: once every 5 minutes)
- 🚪 Forced sync on quit
- 🗂 S3 versioning for easy rollback
- 🧩 MIT licensed, extensible, and self-hosted

---

## Non-Goals (by design)

- No real-time syncing
- No delta or block-level uploads
- No vendor lock-in to Steam, itch.io, etc.
- No “magic” background processes

This is a **deterministic, explicit system** that does one thing well.

---

## How It Works

1. The Ren’Py game detects local save changes.
2. Every 5 minutes (or on quit), it sends a **local file manifest** to the API.
3. The backend compares local vs remote metadata.
4. The API returns a **sync plan**:
   - Upload
   - Download
   - No-op
5. The client executes the plan using **pre-signed S3 URLs**.

If timestamps match, nothing happens—no wasted bandwidth.

---

## Repository Structure

```
.
├── renpy_cloud/        # Python client (pip package)
├── infra/              # AWS infrastructure (Serverless Framework)
├── example_game/       # Minimal Ren’Py integration example
├── README.md
└── LICENSE
```

---

## Requirements

### Client
- Ren’Py 7.4+ or 8.x
- Python 3.8+

### Backend
- AWS account
- AWS CLI configured
- Node.js 18+ (recommended)
- Serverless Framework v3+

---

## Backend Setup (AWS)

The backend is **self-hosted**. You deploy your own stack.

### 1️⃣ Install Serverless Framework

```bash
npm i -g serverless
```

(Or use `npx serverless` if you prefer not to install globally.)

### 2️⃣ Deploy Infrastructure

```bash
cd infra
serverless deploy
```

This creates:

- Cognito User Pool
- Cognito App Client
- API Gateway
- Lambda function
- S3 bucket (versioning enabled)
- DynamoDB manifest table

### 3️⃣ Capture Outputs

After deployment, note the outputs printed by Serverless (and/or in `serverless info`):

- `API_BASE_URL`
- `COGNITO_USER_POOL_ID`
- `COGNITO_APP_CLIENT_ID`
- `AWS_REGION`

You’ll need these for the Ren’Py client config.

---

## Client Installation

Add the package to your project (local or pip install):

```bash
pip install renpy-cloud
```

Or vendor it directly into your Ren’Py project.

---

## Ren’Py Integration

### Minimal Setup

```python
init python:
    import renpy_cloud

    renpy_cloud.configure(
        api_base_url="https://your-api-id.execute-api.us-east-1.amazonaws.com",
        game_id="my_game_id",
        aws_region="us-east-1",
        cognito_user_pool_id="us-east-1_XXXXXXX",
        cognito_app_client_id="YYYYYYYYYYYY",
    )
```

### On Game Start

```python
label start:
    $ renpy_cloud.sync_on_start()
    return
```

### On Quit

```python
init python:
    config.quit_action = renpy_cloud.sync_on_quit
```

---

## Sync Behavior

### What Gets Synced
- `persistent`
- Files belonging to the **most recently modified save slot**

### When
- At most once every **5 minutes**
- Always on **quit**

### Conflict Resolution
- Newer timestamp wins
- If timestamps match → no-op
- If content differs despite equal timestamps → deterministic winner, local backup created

### Offline Safe
- Sync failures never block gameplay
- Local saves always take priority
- Automatic retry on next window

---

## Authentication Flow

- Users sign up / sign in via Cognito
- JWT access token sent to API Gateway
- Lambda identifies users via `sub` claim
- No AWS credentials ever shipped to clients

---

## Security Model

- No long-lived credentials on client
- S3 access via short-lived pre-signed URLs
- Per-user, per-game isolation
- Optional rate limiting via API Gateway

---

## Development Status

This is an **MVP**:
- Stable API contract
- Designed for extension
- Production-safe for small games

Planned additions:
- Manual restore points
- Save slot browsing
- Encryption options
- Terraform / CDK modules

---

## Philosophy

Ren’Py developers deserve modern infrastructure **without**:
- bloated SDKs
- platform lock-in
- hidden state
- magic behavior

Everything here is explicit, inspectable, and owned by you.

---

## License

MIT License.  
Use it, fork it, ship it, improve it.
