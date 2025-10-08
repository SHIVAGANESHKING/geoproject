import pytest
from unittest.mock import MagicMock
from core.database_manager import DatabaseManager

def test_connect_success(mocker):
    """Tests a successful database connection using the mocker fixture."""
    # Arrange
    mocker.patch('core.database_manager.DB_SETTINGS', {
        'host': 'fake_host', 'dbname': 'fake_db', 'user': 'fake_user', 'password': 'fake_password'
    })
    mock_connect = mocker.patch('core.database_manager.psycopg2.connect')
    mock_conn = MagicMock()
    mock_conn.closed = False  # Simulate an open connection
    mock_connect.return_value = mock_conn
    db_manager = DatabaseManager()

    # Act
    result = db_manager.connect()

    # Assert
    assert result is True
    assert db_manager.is_connected() is True
    mock_connect.assert_called_once()
    assert db_manager.conn is not None

def test_connect_failure(mocker):
    """Tests a failed database connection using the mocker fixture."""
    # Arrange
    from psycopg2 import OperationalError
    mocker.patch('core.database_manager.DB_SETTINGS', {
        'host': 'fake_host', 'dbname': 'fake_db', 'user': 'fake_user', 'password': 'fake_password'
    })
    mock_connect = mocker.patch('core.database_manager.psycopg2.connect')
    mock_connect.side_effect = OperationalError("Connection failed")
    db_manager = DatabaseManager()

    # Act
    result = db_manager.connect()

    # Assert
    assert result is False
    assert db_manager.is_connected() is False
    mock_connect.assert_called_once()
    assert db_manager.conn is None

def test_disconnect():
    """Tests disconnecting from the database."""
    # Arrange
    db_manager = DatabaseManager()
    db_manager.conn = MagicMock()
    db_manager.conn.closed = False

    # Act
    db_manager.disconnect()

    # Assert
    assert db_manager.is_connected() is False
    assert db_manager.conn is None
    assert db_manager.cursor is None