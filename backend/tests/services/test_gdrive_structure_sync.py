"""
Tests for Google Drive Structure Sync

This module tests the integration of Google Drive folder/file creation
when creating Curriculums, Nodes, and uploading PDFs.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from io import BytesIO

from backend.app.services.curriculum_service import CurriculumService
from backend.app.services.node_service import NodeService
from backend.app.schemas.curriculum import CurriculumCreate
from backend.app.schemas.node import NodeCreate


class TestGDriveStructureSync:
    """Test Google Drive structure synchronization"""

    @patch('backend.app.services.gdrive_service.gdrive_service')
    def test_create_curriculum_creates_gdrive_folder(self, mock_gdrive, db_session):
        """Test that creating a curriculum creates a Google Drive folder"""
        # Arrange
        mock_gdrive.create_folder.return_value = "mock_folder_123"
        curriculum_service = CurriculumService(db_session)
        curriculum_data = CurriculumCreate(
            title="Physics 101",
            description="Introduction to Physics",
            is_public=False
        )

        # Act
        curriculum = curriculum_service.create_curriculum(curriculum_data)

        # Assert
        assert curriculum is not None
        assert curriculum.gdrive_folder_id == "mock_folder_123"
        mock_gdrive.create_folder.assert_called_once_with("Physics 101")

    @patch('backend.app.services.gdrive_service.gdrive_service')
    def test_create_node_creates_gdrive_subfolder(self, mock_gdrive, db_session, sample_curriculum):
        """Test that creating a node creates a Google Drive subfolder"""
        # Arrange
        mock_gdrive.create_folder.return_value = "mock_node_folder_456"
        
        # Set the curriculum's gdrive_folder_id
        sample_curriculum.gdrive_folder_id = "mock_curriculum_folder_123"
        db_session.add(sample_curriculum)
        db_session.commit()
        
        node_service = NodeService(db_session)
        node_data = NodeCreate(
            title="Newton's Laws",
            node_type="CHAPTER"
        )

        # Act
        node = node_service.create_node(node_data, curriculum_id=sample_curriculum.curriculum_id)

        # Assert
        assert node is not None
        assert node.gdrive_folder_id == "mock_node_folder_456"
        mock_gdrive.create_folder.assert_called_once_with(
            "Newton's Laws",
            parent_id="mock_curriculum_folder_123"
        )

    @patch('backend.app.services.gdrive_service.gdrive_service')
    def test_upload_pdf_uploads_to_gdrive(self, mock_gdrive, db_session, sample_node):
        """Test that uploading a PDF uploads the file to Google Drive"""
        # Arrange
        mock_gdrive.upload_file.return_value = "mock_file_789"
        
        # Set the node's gdrive_folder_id
        sample_node.gdrive_folder_id = "mock_node_folder_456"
        db_session.add(sample_node)
        db_session.commit()
        
        node_service = NodeService(db_session)
        
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4 fake pdf content"
        pdf_file = BytesIO(pdf_content)
        
        # Act
        link = node_service.create_pdf_link(
            node_id=sample_node.node_id,
            file_obj=pdf_file,
            file_name="lecture1.pdf",
            file_size_bytes=len(pdf_content),
            file_mime_type="application/pdf"
        )

        # Assert
        assert link is not None
        assert link.drive_file_id == "mock_file_789"
        assert link.file_name == "lecture1.pdf"
        assert link.link_type == "PDF"
        mock_gdrive.upload_file.assert_called_once()

    @patch('backend.app.services.gdrive_service.gdrive_service')
    def test_node_without_parent_gdrive_folder_skips_upload(self, mock_gdrive, db_session, sample_node):
        """Test that if a node has no gdrive_folder_id, PDF upload is skipped or handled gracefully"""
        # Arrange
        mock_gdrive.upload_file.return_value = "mock_file_fallback"
        
        # Ensure node has NO gdrive_folder_id
        sample_node.gdrive_folder_id = None
        db_session.add(sample_node)
        db_session.commit()
        
        node_service = NodeService(db_session)
        pdf_file = BytesIO(b"fake pdf")
        
        # Act
        link = node_service.create_pdf_link(
            node_id=sample_node.node_id,
            file_obj=pdf_file,
            file_name="test.pdf"
        )

        # Assert
        # Should still create link, but might not have drive_file_id or upload without parent
        assert link is not None
        # The mock should have been called (fallback behavior)
        mock_gdrive.upload_file.assert_called_once()


# Fixtures
@pytest.fixture
def sample_curriculum(db_session):
    """Create a sample curriculum for testing"""
    from backend.app.models.curriculum import Curriculum
    curriculum = Curriculum(
        title="Test Curriculum",
        description="Test Description",
        is_public=False
    )
    db_session.add(curriculum)
    db_session.commit()
    db_session.refresh(curriculum)
    return curriculum


@pytest.fixture
def sample_node(db_session, sample_curriculum):
    """Create a sample node for testing"""
    from backend.app.models.node import Node
    node = Node(
        title="Test Node",
        curriculum_id=sample_curriculum.curriculum_id,
        node_type="CONTENT",
        order_index=0
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    return node
