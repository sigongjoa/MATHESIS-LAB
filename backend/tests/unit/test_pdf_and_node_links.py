"""
Unit tests for PDF file links and Node-to-Node linking functionality (Phase 3A).

Tests the new NodeLink extensions for:
1. Google Drive PDF file linking
2. Node-to-Node relationship linking
"""

import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from io import BytesIO

from backend.app.models.node import Node, NodeLink
from backend.app.models.curriculum import Curriculum
from backend.app.schemas.node import NodeCreate
from backend.app.services.node_service import NodeService


@pytest.fixture
def test_curriculum(db_session: Session):
    """Create a test curriculum."""
    curriculum = Curriculum(title="Test Curriculum", description="Test", gdrive_folder_id="mock_curriculum_folder_root")
    db_session.add(curriculum)
    db_session.commit()
    db_session.refresh(curriculum)
    return curriculum


@pytest.fixture(autouse=True)
def mock_gdrive_for_all_tests():
    """Mock GDrive service for all tests in this module."""
    with patch('backend.app.services.gdrive_service.gdrive_service') as mock:
        mock.create_folder.return_value = "mock_folder_auto"
        mock.upload_file.return_value = "mock_file_auto"
        yield mock


@pytest.fixture
def test_node(db_session: Session, test_curriculum: Curriculum):
    """Create a test node."""
    service = NodeService(db_session)
    node = service.create_node(
        NodeCreate(title="Test Node"),
        curriculum_id=test_curriculum.curriculum_id
    )
    # Node should now have gdrive_folder_id from the mock
    return node


class TestPDFFileLinks:
    """Test PDF file linking functionality."""

    def test_create_pdf_link(self, db_session: Session, test_node: Node, mock_gdrive_for_all_tests):
        """Test creating a PDF link for a node."""
        mock_gdrive_for_all_tests.upload_file.return_value = "drive_file_123456"
        service = NodeService(db_session)

        # Create a mock PDF file
        pdf_file = BytesIO(b"%PDF-1.4 fake pdf content")

        # Create PDF link
        pdf_link = service.create_pdf_link(
            node_id=test_node.node_id,
            file_obj=pdf_file,
            file_name="research_paper.pdf",
            file_size_bytes=2048000,
            file_mime_type="application/pdf"
        )

        assert pdf_link is not None
        assert pdf_link.node_id == str(test_node.node_id)
        assert pdf_link.link_type == "PDF"
        assert pdf_link.drive_file_id == "drive_file_123456"
        assert pdf_link.file_name == "research_paper.pdf"
        assert pdf_link.file_size_bytes == 2048000
        assert pdf_link.file_mime_type == "application/pdf"

    def test_create_pdf_link_without_optional_fields(self, db_session: Session, test_node: Node, mock_gdrive_for_all_tests):
        """Test creating a PDF link with minimal required fields."""
        mock_gdrive_for_all_tests.upload_file.return_value = "drive_file_789"
        service = NodeService(db_session)

        pdf_file = BytesIO(b"fake pdf")
        pdf_link = service.create_pdf_link(
            node_id=test_node.node_id,
            file_obj=pdf_file,
            file_name="document.pdf"
        )

        assert pdf_link.drive_file_id == "drive_file_789"
        assert pdf_link.file_name == "document.pdf"
        assert pdf_link.file_mime_type == "application/pdf"  # Default value
        assert pdf_link.file_size_bytes is None

    def test_create_pdf_link_node_not_found(self, db_session: Session):
        """Test that creating a PDF link fails if node doesn't exist."""
        service = NodeService(db_session)

        pdf_file = BytesIO(b"fake pdf")
        with pytest.raises(ValueError, match="Node not found"):
            service.create_pdf_link(
                node_id="nonexistent_node_id",
                file_obj=pdf_file,
                file_name="test.pdf"
            )

    def test_get_pdf_links(self, db_session: Session, test_node: Node, mock_gdrive_for_all_tests):
        """Test retrieving PDF links for a node."""
        # Configure mock to return different values for each call
        mock_gdrive_for_all_tests.upload_file.return_value = "drive_file_001"
        service = NodeService(db_session)

        # Create first PDF link
        pdf_link_1 = service.create_pdf_link(
            node_id=test_node.node_id,
            file_obj=BytesIO(b"pdf1"),
            file_name="document1.pdf"
        )
        
        # Change return value for second call
        mock_gdrive_for_all_tests.upload_file.return_value = "drive_file_002"
        
        # Create second PDF link
        pdf_link_2 = service.create_pdf_link(
            node_id=test_node.node_id,
            file_obj=BytesIO(b"pdf2"),
            file_name="document2.pdf"
        )

        # Retrieve PDF links
        pdf_links = service.get_pdf_links(test_node.node_id)

        assert len(pdf_links) == 2
        assert all(link.link_type == "PDF" for link in pdf_links)
        assert pdf_link_1.file_name in [link.file_name for link in pdf_links]
        assert pdf_link_2.file_name in [link.file_name for link in pdf_links]


class TestNodeToNodeLinks:
    """Test Node-to-Node linking functionality."""

    def test_create_node_link(self, db_session: Session, test_curriculum: Curriculum):
        """Test creating a link between two nodes."""
        service = NodeService(db_session)

        # Create two nodes
        node1 = service.create_node(
            NodeCreate(title="Node 1"),
            curriculum_id=test_curriculum.curriculum_id
        )
        node2 = service.create_node(
            NodeCreate(title="Node 2"),
            curriculum_id=test_curriculum.curriculum_id
        )

        # Create link between nodes
        node_link = service.create_node_link(
            source_node_id=node1.node_id,
            target_node_id=node2.node_id,
            link_relationship="REFERENCE"
        )

        assert node_link is not None
        assert node_link.node_id == node1.node_id
        assert node_link.linked_node_id == node2.node_id
        assert node_link.link_type == "NODE"
        assert node_link.link_relationship == "REFERENCE"

    def test_create_node_link_default_relationship(self, db_session: Session, test_curriculum: Curriculum):
        """Test that node link uses REFERENCE as default relationship."""
        service = NodeService(db_session)

        node1 = service.create_node(
            NodeCreate(title="Source"),
            curriculum_id=test_curriculum.curriculum_id
        )
        node2 = service.create_node(
            NodeCreate(title="Target"),
            curriculum_id=test_curriculum.curriculum_id
        )

        node_link = service.create_node_link(
            source_node_id=node1.node_id,
            target_node_id=node2.node_id
        )

        assert node_link.link_relationship == "REFERENCE"

    def test_create_node_link_self_link_fails(self, db_session: Session, test_node: Node):
        """Test that a node cannot link to itself."""
        service = NodeService(db_session)

        with pytest.raises(ValueError, match="Cannot link a node to itself"):
            service.create_node_link(
                source_node_id=test_node.node_id,
                target_node_id=test_node.node_id
            )

    def test_create_node_link_source_not_found(self, db_session: Session, test_node: Node):
        """Test that linking fails if source node doesn't exist."""
        service = NodeService(db_session)

        with pytest.raises(ValueError, match="Source node not found"):
            service.create_node_link(
                source_node_id="nonexistent_source",
                target_node_id=test_node.node_id
            )

    def test_create_node_link_target_not_found(self, db_session: Session, test_node: Node):
        """Test that linking fails if target node doesn't exist."""
        service = NodeService(db_session)

        with pytest.raises(ValueError, match="Target node not found"):
            service.create_node_link(
                source_node_id=test_node.node_id,
                target_node_id="nonexistent_target"
            )

    def test_get_node_to_node_links(self, db_session: Session, test_curriculum: Curriculum):
        """Test retrieving node-to-node links for a node."""
        service = NodeService(db_session)

        # Create three nodes
        node1 = service.create_node(
            NodeCreate(title="Node 1"),
            curriculum_id=test_curriculum.curriculum_id
        )
        node2 = service.create_node(
            NodeCreate(title="Node 2"),
            curriculum_id=test_curriculum.curriculum_id
        )
        node3 = service.create_node(
            NodeCreate(title="Node 3"),
            curriculum_id=test_curriculum.curriculum_id
        )

        # Create links from node1 to node2 and node3
        service.create_node_link(
            source_node_id=node1.node_id,
            target_node_id=node2.node_id,
            link_relationship="EXTENDS"
        )
        service.create_node_link(
            source_node_id=node1.node_id,
            target_node_id=node3.node_id,
            link_relationship="DEPENDS_ON"
        )

        # Retrieve links for node1
        node_links = service.get_node_to_node_links(node1.node_id)

        assert len(node_links) == 2
        assert all(link.link_type == "NODE" for link in node_links)
        assert node_links[0].node_id == str(node1.node_id)
        assert node_links[1].node_id == str(node1.node_id)


class TestMixedLinkTypes:
    """Test handling of mixed link types (PDF, Node-to-Node, YouTube)."""

    def test_node_with_multiple_link_types(self, db_session: Session, test_curriculum: Curriculum, test_node: Node, mock_gdrive_for_all_tests):
        """Test a single node with multiple types of links."""
        mock_gdrive_for_all_tests.upload_file.return_value = "drive_file_001"
        service = NodeService(db_session)

        # Create another node for node-to-node linking
        other_node = service.create_node(
            NodeCreate(title="Other Node"),
            curriculum_id=test_curriculum.curriculum_id
        )

        # Create different types of links
        pdf_link = service.create_pdf_link(
            node_id=test_node.node_id,
            file_obj=BytesIO(b"fake pdf"),
            file_name="document.pdf"
        )

        node_link = service.create_node_link(
            source_node_id=test_node.node_id,
            target_node_id=other_node.node_id,
            link_relationship="EXTENDS"
        )

        youtube_link = service.create_youtube_link(
            node_id=test_node.node_id,
            youtube_url="https://youtu.be/dQw4w9WgXcQ"
        )

        # Retrieve all links
        all_links = service.get_node_links(test_node.node_id)

        assert len(all_links) == 3
        link_types = [link.link_type for link in all_links]
        assert "PDF" in link_types
        assert "NODE" in link_types
        assert "YOUTUBE" in link_types

    def test_filter_pdf_links_from_mixed(self, db_session: Session, test_curriculum: Curriculum, test_node: Node, mock_gdrive_for_all_tests):
        """Test filtering PDF links from a mixed set of link types."""
        service = NodeService(db_session)

        other_node = service.create_node(
            NodeCreate(title="Target"),
            curriculum_id=test_curriculum.curriculum_id
        )

        # Create multiple link types
        mock_gdrive_for_all_tests.upload_file.return_value = "drive_file_001"
        service.create_pdf_link(
            node_id=test_node.node_id,
            file_obj=BytesIO(b"pdf1"),
            file_name="doc1.pdf"
        )
        
        mock_gdrive_for_all_tests.upload_file.return_value = "drive_file_002"
        service.create_pdf_link(
            node_id=test_node.node_id,
            file_obj=BytesIO(b"pdf2"),
            file_name="doc2.pdf"
        )
        
        service.create_node_link(
            source_node_id=test_node.node_id,
            target_node_id=other_node.node_id
        )

        # Filter PDF links
        pdf_links = service.get_pdf_links(test_node.node_id)

        assert len(pdf_links) == 2
        assert all(link.link_type == "PDF" for link in pdf_links)

    def test_filter_node_links_from_mixed(self, db_session: Session, test_curriculum: Curriculum, test_node: Node, mock_gdrive_for_all_tests):
        """Test filtering node-to-node links from a mixed set of link types."""
        mock_gdrive_for_all_tests.upload_file.return_value = "drive_file_001"
        service = NodeService(db_session)

        node1 = service.create_node(
            NodeCreate(title="Target 1"),
            curriculum_id=test_curriculum.curriculum_id
        )
        node2 = service.create_node(
            NodeCreate(title="Target 2"),
            curriculum_id=test_curriculum.curriculum_id
        )

        # Create multiple link types
        service.create_pdf_link(
            node_id=test_node.node_id,
            file_obj=BytesIO(b"pdf"),
            file_name="doc.pdf"
        )
        service.create_node_link(
            source_node_id=test_node.node_id,
            target_node_id=node1.node_id,
            link_relationship="EXTENDS"
        )
        service.create_node_link(
            source_node_id=test_node.node_id,
            target_node_id=node2.node_id,
            link_relationship="DEPENDS_ON"
        )

        # Filter node links
        node_links = service.get_node_to_node_links(test_node.node_id)

        assert len(node_links) == 2
        assert all(link.link_type == "NODE" for link in node_links)
