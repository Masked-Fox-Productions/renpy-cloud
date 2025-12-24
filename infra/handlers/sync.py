"""Lambda handlers for sync operations."""

import json
import os
import time
from typing import Dict, List, Any, Optional
import boto3
from datetime import datetime

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

MANIFEST_TABLE = os.environ['MANIFEST_TABLE']
SAVE_FILES_BUCKET = os.environ['SAVE_FILES_BUCKET']

manifest_table = dynamodb.Table(MANIFEST_TABLE)


def get_user_id(event: Dict[str, Any]) -> str:
    """Extract user ID from JWT claims."""
    try:
        # HTTP API format
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            authorizer = event['requestContext']['authorizer']
            if 'jwt' in authorizer and 'claims' in authorizer['jwt']:
                return authorizer['jwt']['claims']['sub']
        
        raise ValueError("No user ID found in request context")
    except Exception as e:
        raise ValueError(f"Failed to extract user ID: {e}")


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse request body from event."""
    body = event.get('body', '{}')
    if isinstance(body, str):
        return json.loads(body)
    return body


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create HTTP response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body)
    }


def get_s3_key(user_id: str, game_id: str, filename: str) -> str:
    """Generate S3 key for a file."""
    return f"users/{user_id}/games/{game_id}/{filename}"


def generate_presigned_url(
    bucket: str,
    key: str,
    operation: str,
    expiration: int = 300
) -> str:
    """Generate a pre-signed URL for S3 operations."""
    return s3_client.generate_presigned_url(
        ClientMethod=operation,
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=expiration
    )


def get_remote_manifest(user_id: str, game_id: str) -> Dict[str, Any]:
    """Get remote manifest from DynamoDB."""
    try:
        response = manifest_table.get_item(
            Key={
                'user_id': user_id,
                'game_id': game_id
            }
        )
        if 'Item' in response:
            return response['Item'].get('files', {})
        return {}
    except Exception as e:
        print(f"Error getting remote manifest: {e}")
        return {}


def update_remote_manifest(
    user_id: str,
    game_id: str,
    files: Dict[str, Any]
) -> None:
    """Update remote manifest in DynamoDB."""
    try:
        manifest_table.put_item(
            Item={
                'user_id': user_id,
                'game_id': game_id,
                'files': files,
                'last_updated': int(time.time()),
            }
        )
    except Exception as e:
        print(f"Error updating remote manifest: {e}")
        raise


def compare_files(
    local_info: Dict[str, Any],
    remote_info: Optional[Dict[str, Any]]
) -> str:
    """
    Compare local and remote file info to determine action.
    
    Returns:
        'upload', 'download', 'noop', or 'conflict'
    """
    if remote_info is None:
        # File doesn't exist remotely
        return 'upload'
    
    local_mtime = local_info.get('modified_timestamp', 0)
    remote_mtime = remote_info.get('modified_timestamp', 0)
    
    # Compare timestamps
    if local_mtime > remote_mtime:
        return 'upload'
    elif local_mtime < remote_mtime:
        return 'download'
    else:
        # Timestamps match
        local_checksum = local_info.get('checksum', '')
        remote_checksum = remote_info.get('checksum', '')
        
        if local_checksum != remote_checksum:
            # Conflict: same timestamp but different content
            # Use deterministic resolution: longer checksum wins, or alphabetically
            if local_checksum > remote_checksum:
                return 'upload'
            else:
                return 'download'
        
        return 'noop'


def plan_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle sync plan requests.
    
    Compares local manifest with remote and returns actions to take.
    """
    try:
        # Extract user ID from JWT
        user_id = get_user_id(event)
        
        # Parse request body
        body = parse_body(event)
        game_id = body.get('game_id')
        local_manifest = body.get('manifest', {})
        
        if not game_id:
            return create_response(400, {'error': 'Missing game_id'})
        
        # Get remote manifest
        remote_manifest = get_remote_manifest(user_id, game_id)
        
        # Plan sync actions
        uploads = []
        downloads = []
        conflicts = []
        updated_remote_manifest = dict(remote_manifest)
        
        # Check local files
        for filename, local_info in local_manifest.items():
            remote_info = remote_manifest.get(filename)
            action = compare_files(local_info, remote_info)
            
            s3_key = get_s3_key(user_id, game_id, filename)
            
            if action == 'upload':
                upload_url = generate_presigned_url(
                    SAVE_FILES_BUCKET,
                    s3_key,
                    'put_object'
                )
                uploads.append({
                    'filename': filename,
                    'upload_url': upload_url
                })
                # Update manifest to reflect upcoming upload
                updated_remote_manifest[filename] = local_info
            
            elif action == 'download':
                download_url = generate_presigned_url(
                    SAVE_FILES_BUCKET,
                    s3_key,
                    'get_object'
                )
                downloads.append({
                    'filename': filename,
                    'download_url': download_url
                })
            
            elif action == 'conflict':
                # For conflicts, we still choose one (deterministic)
                # but mark it as a conflict for logging
                download_url = generate_presigned_url(
                    SAVE_FILES_BUCKET,
                    s3_key,
                    'get_object'
                )
                conflicts.append({
                    'filename': filename,
                    'action': 'download',
                    'download_url': download_url
                })
        
        # Check for files that exist remotely but not locally
        for filename, remote_info in remote_manifest.items():
            if filename not in local_manifest:
                s3_key = get_s3_key(user_id, game_id, filename)
                download_url = generate_presigned_url(
                    SAVE_FILES_BUCKET,
                    s3_key,
                    'get_object'
                )
                downloads.append({
                    'filename': filename,
                    'download_url': download_url
                })
        
        # Update remote manifest if there are uploads
        if uploads:
            update_remote_manifest(user_id, game_id, updated_remote_manifest)
        
        return create_response(200, {
            'uploads': uploads,
            'downloads': downloads,
            'conflicts': conflicts,
            'deletes': []  # Not implemented yet
        })
    
    except ValueError as e:
        return create_response(401, {'error': str(e)})
    
    except Exception as e:
        print(f"Error in plan_handler: {e}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Internal server error'})


def complete_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle sync completion notifications.
    
    This is for logging/analytics purposes.
    """
    try:
        # Extract user ID from JWT
        user_id = get_user_id(event)
        
        # Parse request body
        body = parse_body(event)
        game_id = body.get('game_id')
        success = body.get('success', False)
        error = body.get('error')
        
        if not game_id:
            return create_response(400, {'error': 'Missing game_id'})
        
        # Log completion (could be stored in DynamoDB for analytics)
        print(f"Sync completed for user {user_id}, game {game_id}: "
              f"success={success}, error={error}")
        
        return create_response(200, {'acknowledged': True})
    
    except ValueError as e:
        return create_response(401, {'error': str(e)})
    
    except Exception as e:
        print(f"Error in complete_handler: {e}")
        return create_response(500, {'error': 'Internal server error'})

