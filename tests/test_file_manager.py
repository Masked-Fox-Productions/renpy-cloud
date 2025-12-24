"""Tests for file manager module."""

import os
import tempfile
import pytest
from renpy_cloud.file_manager import FileInfo, FileManager
from renpy_cloud.exceptions import StorageError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_manager(temp_dir):
    """Create a FileManager with temporary directory."""
    return FileManager(temp_dir)


def test_file_info_to_dict():
    """Test FileInfo converts to dictionary."""
    info = FileInfo(
        path='test.save',
        size=1024,
        modified_timestamp=1234567890.0,
        checksum='abc123'
    )
    
    data = info.to_dict()
    assert data['path'] == 'test.save'
    assert data['size'] == 1024
    assert data['modified_timestamp'] == 1234567890.0
    assert data['checksum'] == 'abc123'


def test_file_info_from_dict():
    """Test FileInfo creates from dictionary."""
    data = {
        'path': 'test.save',
        'size': 2048,
        'modified_timestamp': 9876543210.0,
        'checksum': 'def456'
    }
    
    info = FileInfo.from_dict(data)
    assert info.path == 'test.save'
    assert info.size == 2048
    assert info.modified_timestamp == 9876543210.0
    assert info.checksum == 'def456'


def test_calculate_file_hash(file_manager, temp_dir):
    """Test file hash calculation."""
    test_file = os.path.join(temp_dir, 'test.txt')
    with open(test_file, 'w') as f:
        f.write('Hello, World!')
    
    hash_value = file_manager.calculate_file_hash(test_file)
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA256 hex length
    # Known hash for "Hello, World!"
    assert hash_value == 'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'


def test_calculate_file_hash_missing_file(file_manager, temp_dir):
    """Test hash calculation fails for missing file."""
    with pytest.raises(StorageError, match="Failed to hash file"):
        file_manager.calculate_file_hash(os.path.join(temp_dir, 'nonexistent.txt'))


def test_get_file_info(file_manager, temp_dir):
    """Test getting file information."""
    test_file = os.path.join(temp_dir, 'test.save')
    test_content = b'Test save data'
    with open(test_file, 'wb') as f:
        f.write(test_content)
    
    info = file_manager.get_file_info(test_file)
    assert info.path == 'test.save'
    assert info.size == len(test_content)
    assert info.modified_timestamp > 0
    assert len(info.checksum) == 64


def test_get_most_recent_save_slot_no_saves(file_manager):
    """Test getting recent slot when no saves exist."""
    slot = file_manager.get_most_recent_save_slot()
    assert slot is None


def test_get_most_recent_save_slot_with_saves(file_manager, temp_dir):
    """Test getting most recent save slot."""
    # Create save files with different mtimes
    import time
    
    save1 = os.path.join(temp_dir, '1-1-LT1.save')
    with open(save1, 'wb') as f:
        f.write(b'save 1')
    
    time.sleep(0.01)  # Ensure different mtimes
    
    save2 = os.path.join(temp_dir, '2-1-LT1.save')
    with open(save2, 'wb') as f:
        f.write(b'save 2')
    
    slot = file_manager.get_most_recent_save_slot()
    assert slot == 2  # Most recent


def test_get_slot_files(file_manager, temp_dir):
    """Test getting all files for a slot."""
    # Create files for slot 1
    files = ['1-1-LT1.save', '1-2-LT1.save', '1-1-LT1.png']
    for filename in files:
        with open(os.path.join(temp_dir, filename), 'wb') as f:
            f.write(b'data')
    
    # Create file for different slot
    with open(os.path.join(temp_dir, '2-1-LT1.save'), 'wb') as f:
        f.write(b'data')
    
    slot_files = file_manager.get_slot_files(1)
    assert len(slot_files) == 3
    assert all('1-' in os.path.basename(f) for f in slot_files)


def test_get_persistent_file(file_manager, temp_dir):
    """Test getting persistent file path."""
    persistent_path = os.path.join(temp_dir, 'persistent')
    with open(persistent_path, 'wb') as f:
        f.write(b'persistent data')
    
    result = file_manager.get_persistent_file()
    assert result == persistent_path


def test_get_persistent_file_missing(file_manager):
    """Test getting persistent file when it doesn't exist."""
    result = file_manager.get_persistent_file()
    assert result is None


def test_build_local_manifest(file_manager, temp_dir):
    """Test building local manifest."""
    # Create persistent file
    persistent = os.path.join(temp_dir, 'persistent')
    with open(persistent, 'wb') as f:
        f.write(b'persistent data')
    
    # Create save files
    save1 = os.path.join(temp_dir, '1-1-LT1.save')
    with open(save1, 'wb') as f:
        f.write(b'save data 1')
    
    manifest = file_manager.build_local_manifest()
    
    assert 'persistent' in manifest
    assert '1-1-LT1.save' in manifest
    assert isinstance(manifest['persistent'], FileInfo)


def test_backup_file(file_manager, temp_dir):
    """Test backing up a file."""
    test_file = os.path.join(temp_dir, 'test.save')
    with open(test_file, 'wb') as f:
        f.write(b'original data')
    
    backup_path = file_manager.backup_file(test_file)
    
    assert os.path.exists(backup_path)
    with open(backup_path, 'rb') as f:
        assert f.read() == b'original data'


def test_read_file(file_manager, temp_dir):
    """Test reading file contents."""
    test_file = os.path.join(temp_dir, 'test.txt')
    test_data = b'test content'
    with open(test_file, 'wb') as f:
        f.write(test_data)
    
    content = file_manager.read_file(test_file)
    assert content == test_data


def test_write_file(file_manager, temp_dir):
    """Test writing file contents."""
    test_file = os.path.join(temp_dir, 'test.txt')
    test_data = b'new content'
    
    file_manager.write_file(test_file, test_data, backup=False)
    
    with open(test_file, 'rb') as f:
        assert f.read() == test_data


def test_write_file_with_backup(file_manager, temp_dir):
    """Test writing file creates backup of existing."""
    test_file = os.path.join(temp_dir, 'test.txt')
    
    # Create original file
    with open(test_file, 'wb') as f:
        f.write(b'original')
    
    # Overwrite with backup
    file_manager.write_file(test_file, b'new', backup=True)
    
    # Original should be backed up
    backup_dir = os.path.join(temp_dir, '.renpy_cloud_backups')
    assert os.path.exists(backup_dir)
    backups = os.listdir(backup_dir)
    assert len(backups) > 0


def test_get_full_path(file_manager, temp_dir):
    """Test getting full path for filename."""
    full_path = file_manager.get_full_path('test.save')
    assert full_path == os.path.join(temp_dir, 'test.save')

