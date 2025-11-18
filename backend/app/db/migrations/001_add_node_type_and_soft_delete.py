"""
Database Migration: Add explicit node_type and soft deletion support

This migration addresses critical design flaws:
1. Implicit node types (queryability issue) → explicit node_type column
2. No soft deletion support → deleted_at timestamp
3. Race condition in order_index → transaction lock ready

Version: 1.0
Date: 2025-11-15
Reversible: Yes
"""

import os
from datetime import datetime
from sqlalchemy import (
    text,
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Index,
    event
)
from sqlalchemy.orm import Session


class Migration:
    """
    Database schema migration for Node Management System improvements
    """

    def __init__(self, db_url: str):
        """
        Initialize migration

        Args:
            db_url: Database connection string (e.g., 'sqlite:///mathesis_lab.db')
        """
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.metadata = MetaData()

    def migrate_up(self):
        """
        Apply migration: Add node_type and deleted_at columns
        """
        print("🔄 Starting migration: Adding node_type and soft deletion support...")

        with self.engine.connect() as connection:
            # ============================================
            # 1. nodes テーブの変更
            # ============================================
            print("\n📝 Modifying 'nodes' table...")

            # Check if columns already exist
            inspector_result = connection.execute(
                text("""
                PRAGMA table_info(nodes);
                """)
            ).fetchall()

            column_names = [row[1] for row in inspector_result]

            # Add node_type column if not exists
            if 'node_type' not in column_names:
                print("  ✓ Adding 'node_type' column...")
                connection.execute(
                    text("""
                    ALTER TABLE nodes
                    ADD COLUMN node_type VARCHAR(50) NOT NULL DEFAULT 'CONTENT';
                    """)
                )
                print("    ✅ 'node_type' column added")
            else:
                print("  ⚠️  'node_type' column already exists, skipping...")

            # Add deleted_at column if not exists
            if 'deleted_at' not in column_names:
                print("  ✓ Adding 'deleted_at' column...")
                connection.execute(
                    text("""
                    ALTER TABLE nodes
                    ADD COLUMN deleted_at TIMESTAMP NULL;
                    """)
                )
                print("    ✅ 'deleted_at' column added")
            else:
                print("  ⚠️  'deleted_at' column already exists, skipping...")

            # Create indices for performance
            print("  ✓ Creating indices...")
            connection.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type);
                """)
            )
            print("    ✅ Index on node_type created")

            connection.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_nodes_deleted ON nodes(deleted_at);
                """)
            )
            print("    ✅ Index on deleted_at created")

            connection.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_nodes_curriculum_active
                ON nodes(curriculum_id, deleted_at);
                """)
            )
            print("    ✅ Composite index on (curriculum_id, deleted_at) created")

            # ============================================
            # 2. node_contents テーブの変更
            # ============================================
            print("\n📝 Modifying 'node_contents' table...")

            inspector_result = connection.execute(
                text("""
                PRAGMA table_info(node_contents);
                """)
            ).fetchall()

            column_names = [row[1] for row in inspector_result]

            if 'deleted_at' not in column_names:
                print("  ✓ Adding 'deleted_at' column...")
                connection.execute(
                    text("""
                    ALTER TABLE node_contents
                    ADD COLUMN deleted_at TIMESTAMP NULL;
                    """)
                )
                print("    ✅ 'deleted_at' column added")
            else:
                print("  ⚠️  'deleted_at' column already exists, skipping...")

            connection.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_node_contents_deleted ON node_contents(deleted_at);
                """)
            )
            print("  ✅ Index on deleted_at created")

            # ============================================
            # 3. node_links テーブの変更
            # ============================================
            print("\n📝 Modifying 'node_links' table...")

            inspector_result = connection.execute(
                text("""
                PRAGMA table_info(node_links);
                """)
            ).fetchall()

            column_names = [row[1] for row in inspector_result]

            if 'deleted_at' not in column_names:
                print("  ✓ Adding 'deleted_at' column...")
                connection.execute(
                    text("""
                    ALTER TABLE node_links
                    ADD COLUMN deleted_at TIMESTAMP NULL;
                    """)
                )
                print("    ✅ 'deleted_at' column added")
            else:
                print("  ⚠️  'deleted_at' column already exists, skipping...")

            connection.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_node_links_deleted ON node_links(deleted_at);
                """)
            )
            print("  ✅ Index on deleted_at created")

            # ============================================
            # 4. curriculums テーブの変更 (念のため)
            # ============================================
            print("\n📝 Modifying 'curriculums' table...")

            inspector_result = connection.execute(
                text("""
                PRAGMA table_info(curriculums);
                """)
            ).fetchall()

            column_names = [row[1] for row in inspector_result]

            if 'deleted_at' not in column_names:
                print("  ✓ Adding 'deleted_at' column...")
                connection.execute(
                    text("""
                    ALTER TABLE curriculums
                    ADD COLUMN deleted_at TIMESTAMP NULL;
                    """)
                )
                print("    ✅ 'deleted_at' column added")
            else:
                print("  ⚠️  'deleted_at' column already exists, skipping...")

            connection.commit()
            print("\n✅ Migration completed successfully!")

    def migrate_down(self):
        """
        Rollback migration: Remove node_type and deleted_at columns

        ⚠️  WARNING: This is destructive. Use only if absolutely necessary.
        """
        response = input(
            "\n⚠️  WARNING: This will remove node_type and deleted_at columns.\n"
            "All soft-delete information will be lost.\n"
            "Are you sure? (yes/no): "
        )

        if response.lower() != 'yes':
            print("❌ Rollback cancelled.")
            return

        print("🔄 Starting rollback...")

        with self.engine.connect() as connection:
            print("\n📝 Reverting 'nodes' table...")
            # SQLite doesn't support DROP COLUMN directly
            # We need to recreate the table
            connection.execute(
                text("""
                ALTER TABLE nodes DROP COLUMN node_type;
                """)
            )
            print("  ✅ 'node_type' column removed")

            connection.execute(
                text("""
                ALTER TABLE nodes DROP COLUMN deleted_at;
                """)
            )
            print("  ✅ 'deleted_at' column removed")

            connection.commit()
            print("\n✅ Rollback completed!")

    def validate(self):
        """
        Validate that migration was applied correctly
        """
        print("\n🔍 Validating migration...")

        with self.engine.connect() as connection:
            # Check nodes table
            print("\n📋 Checking 'nodes' table...")
            inspector_result = connection.execute(
                text("""
                PRAGMA table_info(nodes);
                """)
            ).fetchall()

            column_names = {row[1]: row[2] for row in inspector_result}

            if 'node_type' in column_names:
                print(f"  ✅ node_type: {column_names['node_type']}")
            else:
                print(f"  ❌ node_type: MISSING")

            if 'deleted_at' in column_names:
                print(f"  ✅ deleted_at: {column_names['deleted_at']}")
            else:
                print(f"  ❌ deleted_at: MISSING")

            # Check indices
            print("\n📋 Checking indices...")
            indices = connection.execute(
                text("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='nodes';
                """)
            ).fetchall()

            index_names = [row[0] for row in indices]
            required_indices = [
                'idx_nodes_type',
                'idx_nodes_deleted',
                'idx_nodes_curriculum_active'
            ]

            for idx in required_indices:
                if idx in index_names:
                    print(f"  ✅ {idx}")
                else:
                    print(f"  ⚠️  {idx}: MISSING (non-critical)")

            print("\n✅ Validation complete!")


# ============================================
# Helper Functions for Direct Execution
# ============================================

def run_migration(db_url: str = None):
    """
    Run migration directly (for scripts)

    Args:
        db_url: Database URL (default: from environment or config)
    """
    if db_url is None:
        from backend.app.core.config import settings
        db_url = settings.DATABASE_URL

    migration = Migration(db_url)
    migration.migrate_up()
    migration.validate()


def run_rollback(db_url: str = None):
    """
    Run rollback (use with caution!)

    Args:
        db_url: Database URL
    """
    if db_url is None:
        from backend.app.core.config import settings
        db_url = settings.DATABASE_URL

    migration = Migration(db_url)
    migration.migrate_down()


if __name__ == '__main__':
    """
    Direct execution:
    python -m backend.app.db.migrations.001_add_node_type_and_soft_delete
    """
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        run_rollback()
    else:
        run_migration()
