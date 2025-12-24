"""Tests for Lambda handler functions."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Set required environment variables before importing
os.environ.setdefault('MANIFEST_TABLE', 'test-manifest-table')
os.environ.setdefault('SAVE_FILES_BUCKET', 'test-save-bucket')

# Add the infra/handlers directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'infra', 'handlers'))

from sync import (
    plan_handler,
    complete_handler,
    get_user_id,
    parse_body,
    create_response,
    compare_files,
    get_s3_key,
)


def test_get_user_id_from_jwt():
    """Test extracting user ID from JWT claims."""
    event = {
        'requestContext': {
            'authorizer': {
                'jwt': {
                    'claims': {
                        'sub': 'test-user-id-123'
                    }
                }
            }
        }
    }
    
    user_id = get_user_id(event)
    assert user_id == 'test-user-id-123'


def test_get_user_id_missing():
    """Test get_user_id raises when no user ID found."""
    event = {'requestContext': {}}
    
    with pytest.raises(ValueError, match="No user ID found"):
        get_user_id(event)


def test_parse_body_string():
    """Test parsing JSON string body."""
    event = {
        'body': '{"key": "value"}'
    }
    
    body = parse_body(event)
    assert body == {'key': 'value'}


def test_parse_body_dict():
    """Test parsing dict body."""
    event = {
        'body': {'key': 'value'}
    }
    
    body = parse_body(event)
    assert body == {'key': 'value'}


def test_create_response():
    """Test creating HTTP response."""
    response = create_response(200, {'status': 'ok'})
    
    assert response['statusCode'] == 200
    assert 'Content-Type' in response['headers']
    assert json.loads(response['body']) == {'status': 'ok'}


def test_get_s3_key():
    """Test generating S3 key."""
    key = get_s3_key('user123', 'game456', 'save.dat')
    assert key == 'users/user123/games/game456/save.dat'


def test_compare_files_no_remote():
    """Test comparison when file doesn't exist remotely."""
    local_info = {'modified_timestamp': 1234567890.0}
    assert compare_files(local_info, None) == 'upload'


def test_compare_files_local_newer():
    """Test comparison when local file is newer."""
    local_info = {'modified_timestamp': 2000.0}
    remote_info = {'modified_timestamp': 1000.0}
    assert compare_files(local_info, remote_info) == 'upload'


def test_compare_files_remote_newer():
    """Test comparison when remote file is newer."""
    local_info = {'modified_timestamp': 1000.0}
    remote_info = {'modified_timestamp': 2000.0}
    assert compare_files(local_info, remote_info) == 'download'


def test_compare_files_same_timestamp_same_checksum():
    """Test comparison with matching timestamps and checksums."""
    local_info = {
        'modified_timestamp': 1000.0,
        'checksum': 'abc123'
    }
    remote_info = {
        'modified_timestamp': 1000.0,
        'checksum': 'abc123'
    }
    assert compare_files(local_info, remote_info) == 'noop'


def test_compare_files_conflict():
    """Test comparison with conflict (same time, different content)."""
    local_info = {
        'modified_timestamp': 1000.0,
        'checksum': 'zzz999'
    }
    remote_info = {
        'modified_timestamp': 1000.0,
        'checksum': 'aaa111'
    }
    # Should resolve deterministically
    result = compare_files(local_info, remote_info)
    assert result in ['upload', 'download']


@patch.dict(os.environ, {
    'MANIFEST_TABLE': 'test-manifest-table',
    'SAVE_FILES_BUCKET': 'test-save-bucket'
})
@patch('sync.manifest_table')
@patch('sync.s3_client')
def test_plan_handler_success(mock_s3, mock_table):
    """Test plan handler with successful request."""
    # Mock DynamoDB response
    mock_table.get_item.return_value = {
        'Item': {
            'user_id': 'test-user',
            'game_id': 'test-game',
            'files': {},
            'last_updated': 1234567890
        }
    }
    
    # Mock S3 presigned URL generation
    mock_s3.generate_presigned_url.return_value = 'https://s3.example.com/presigned'
    
    event = {
        'requestContext': {
            'authorizer': {
                'jwt': {
                    'claims': {'sub': 'test-user'}
                }
            }
        },
        'body': json.dumps({
            'game_id': 'test-game',
            'manifest': {
                'test.save': {
                    'path': 'test.save',
                    'size': 1024,
                    'modified_timestamp': 1234567890.0,
                    'checksum': 'abc123'
                }
            }
        })
    }
    
    response = plan_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'uploads' in body
    assert 'downloads' in body
    assert 'conflicts' in body


@patch.dict(os.environ, {
    'MANIFEST_TABLE': 'test-manifest-table',
    'SAVE_FILES_BUCKET': 'test-save-bucket'
})
def test_plan_handler_missing_game_id():
    """Test plan handler with missing game_id."""
    event = {
        'requestContext': {
            'authorizer': {
                'jwt': {
                    'claims': {'sub': 'test-user'}
                }
            }
        },
        'body': json.dumps({
            'manifest': {}
        })
    }
    
    response = plan_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body


@patch.dict(os.environ, {
    'MANIFEST_TABLE': 'test-manifest-table',
    'SAVE_FILES_BUCKET': 'test-save-bucket'
})
def test_plan_handler_unauthorized():
    """Test plan handler with missing auth."""
    event = {
        'requestContext': {},
        'body': json.dumps({'game_id': 'test-game', 'manifest': {}})
    }
    
    response = plan_handler(event, None)
    
    assert response['statusCode'] == 401


@patch.dict(os.environ, {
    'MANIFEST_TABLE': 'test-manifest-table',
    'SAVE_FILES_BUCKET': 'test-save-bucket'
})
def test_complete_handler_success():
    """Test complete handler with successful request."""
    event = {
        'requestContext': {
            'authorizer': {
                'jwt': {
                    'claims': {'sub': 'test-user'}
                }
            }
        },
        'body': json.dumps({
            'game_id': 'test-game',
            'success': True
        })
    }
    
    response = complete_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['acknowledged'] is True


@patch.dict(os.environ, {
    'MANIFEST_TABLE': 'test-manifest-table',
    'SAVE_FILES_BUCKET': 'test-save-bucket'
})
def test_complete_handler_missing_game_id():
    """Test complete handler with missing game_id."""
    event = {
        'requestContext': {
            'authorizer': {
                'jwt': {
                    'claims': {'sub': 'test-user'}
                }
            }
        },
        'body': json.dumps({
            'success': False
        })
    }
    
    response = complete_handler(event, None)
    
    assert response['statusCode'] == 400

