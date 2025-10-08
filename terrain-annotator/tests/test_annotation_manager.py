import pytest
from unittest.mock import MagicMock
from core.annotation_manager import AnnotationManager
from models.annotation import Annotation

@pytest.fixture
def mock_db_manager():
    """Fixture for a mocked DatabaseManager."""
    db_manager = MagicMock()
    db_manager.is_connected.return_value = True
    db_manager.get_cursor.return_value = MagicMock()
    return db_manager

def test_save_annotation_success(mock_db_manager):
    """Tests the successful saving of an annotation."""
    # Arrange
    manager = AnnotationManager(mock_db_manager)
    annotation = Annotation(geom="POLYGON((0 0, 1 1, 1 0, 0 0))", class_name="Hill")

    # Act
    result = manager.save_annotation(annotation)

    # Assert
    assert result is True
    mock_db_manager.get_cursor.assert_called_once()
    mock_db_manager.conn.commit.assert_called_once()
    mock_db_manager.conn.rollback.assert_not_called()

def test_save_annotation_db_error(mock_db_manager):
    """Tests handling of a database error during save."""
    # Arrange
    # Simulate a database error on execute
    mock_cursor = mock_db_manager.get_cursor()
    mock_cursor.execute.side_effect = Exception("DB Error")

    manager = AnnotationManager(mock_db_manager)
    annotation = Annotation(geom="POLYGON((0 0, 1 1, 1 0, 0 0))", class_name="Hill")

    # Act
    result = manager.save_annotation(annotation)

    # Assert
    assert result is False
    mock_db_manager.conn.commit.assert_not_called()
    mock_db_manager.conn.rollback.assert_called_once()

def test_save_annotation_not_connected(mock_db_manager):
    """Tests that saving fails if the database is not connected."""
    # Arrange
    mock_db_manager.is_connected.return_value = False
    manager = AnnotationManager(mock_db_manager)
    annotation = Annotation(geom="POLYGON((0 0, 1 1, 1 0, 0 0))", class_name="Hill")

    # Act
    result = manager.save_annotation(annotation)

    # Assert
    assert result is False
    mock_db_manager.get_cursor.assert_not_called()