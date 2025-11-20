# RAG 데이터베이스 스키마

## 📋 목차
1. [ERD](#1-erd)
2. [테이블 정의](#2-테이블-정의)
3. [인덱스 전략](#3-인덱스-전략)
4. [마이그레이션](#4-마이그레이션)
5. [데이터 정합성](#5-데이터-정합성)

---

## 1. ERD

```
┌─────────────────────┐
│   curriculums       │
│  (기존 테이블)       │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────▼──────────┐       ┌─────────────────────┐
│    rag_chunks       │ N   1 │   rag_documents     │
│                     ├───────┤                     │
│ - chunk_id (PK)     │       │ - document_id (PK)  │
│ - document_id (FK)  │       │ - file_path         │
│ - content           │       │ - document_type     │
│ - metadata (JSON)   │       │ - status            │
│ - curriculum_id(FK) │       │ - created_at        │
│ - node_id (FK)      │       └─────────────────────┘
│ - created_at        │
│ - updated_at        │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────▼──────────┐
│   rag_query_logs    │
│                     │
│ - log_id (PK)       │
│ - query_id          │
│ - user_id (FK)      │
│ - query_text        │
│ - answer            │
│ - sources (JSON)    │
│ - confidence        │
│ - processing_time   │
│ - created_at        │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────▼──────────┐
│   rag_feedback      │
│                     │
│ - feedback_id (PK)  │
│ - query_id (FK)     │
│ - user_id (FK)      │
│ - rating            │
│ - feedback_type     │
│ - comment           │
│ - created_at        │
└─────────────────────┘
```

---

## 2. 테이블 정의

### 2.1 rag_documents

문서 메타데이터 및 인덱싱 상태를 관리합니다.

```sql
CREATE TABLE rag_documents (
    document_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,  -- SHA-256
    
    -- 문서 분류
    document_type VARCHAR(50) NOT NULL,  -- 'curriculum', 'school_plan'
    policy_version VARCHAR(20) NOT NULL,  -- '2022개정', '2015개정'
    scope_type VARCHAR(20) NOT NULL,  -- 'NATIONAL', 'SCHOOL'
    institution_id VARCHAR(100),  -- 학교 ID (SCHOOL인 경우)
    
    -- 인덱싱 상태
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    chunks_count INTEGER DEFAULT 0,
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    error_message TEXT,
    
    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 인덱스
    INDEX idx_status (status),
    INDEX idx_document_type (document_type),
    INDEX idx_policy_version (policy_version),
    INDEX idx_file_hash (file_hash),
    UNIQUE INDEX idx_file_path (file_path)
);
```

### 2.2 rag_chunks

파싱된 청크 데이터를 저장합니다.

```sql
CREATE TABLE rag_chunks (
    chunk_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    document_id VARCHAR(36) NOT NULL,
    
    -- 청크 내용
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,  -- 중복 방지
    chunk_index INTEGER NOT NULL,  -- 문서 내 순서
    
    -- 메타데이터 (JSON)
    metadata JSON NOT NULL,
    
    -- 임베딩 정보
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-large',
    embedding_dimension INTEGER NOT NULL DEFAULT 3072,
    vector_id VARCHAR(100),  -- Qdrant point ID
    
    -- 레거시 시스템 연동
    curriculum_id VARCHAR(36),
    node_id VARCHAR(36),
    
    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 외래 키
    FOREIGN KEY (document_id) REFERENCES rag_documents(document_id) ON DELETE CASCADE,
    FOREIGN KEY (curriculum_id) REFERENCES curriculums(curriculum_id) ON DELETE SET NULL,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE SET NULL,
    
    -- 인덱스
    INDEX idx_document_id (document_id),
    INDEX idx_curriculum_id (curriculum_id),
    INDEX idx_node_id (node_id),
    INDEX idx_content_hash (content_hash),
    
    -- JSON 메타데이터 인덱스 (MySQL 5.7+)
    INDEX idx_policy_version ((CAST(metadata->>'$.policy_version' AS CHAR(20)))),
    INDEX idx_scope_type ((CAST(metadata->>'$.scope_type' AS CHAR(20)))),
    INDEX idx_document_type ((CAST(metadata->>'$.document_type' AS CHAR(50)))),
    
    -- 복합 인덱스
    UNIQUE INDEX idx_document_chunk (document_id, chunk_index)
);
```

### 2.3 rag_query_logs

사용자 질의 및 응답 로그를 저장합니다.

```sql
CREATE TABLE rag_query_logs (
    log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    query_id VARCHAR(36) NOT NULL UNIQUE,
    
    -- 사용자 정보
    user_id VARCHAR(36) NOT NULL,
    
    -- 질의 정보
    query_text TEXT NOT NULL,
    filters JSON,
    top_k INTEGER NOT NULL DEFAULT 5,
    
    -- 응답 정보
    answer TEXT NOT NULL,
    sources JSON NOT NULL,  -- 검색된 청크 목록
    confidence FLOAT,
    
    -- 성능 메트릭
    processing_time_ms INTEGER NOT NULL,
    embedding_time_ms INTEGER,
    search_time_ms INTEGER,
    llm_time_ms INTEGER,
    
    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래 키
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- 인덱스
    INDEX idx_user_id (user_id),
    INDEX idx_query_id (query_id),
    INDEX idx_created_at (created_at),
    
    -- 전문 검색 인덱스
    FULLTEXT INDEX idx_query_text (query_text)
);
```

### 2.4 rag_feedback

사용자 피드백을 저장합니다.

```sql
CREATE TABLE rag_feedback (
    feedback_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    query_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    
    -- 피드백 내용
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    feedback_type VARCHAR(20),  -- 'helpful', 'incorrect', 'incomplete', 'irrelevant'
    comment TEXT,
    
    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래 키
    FOREIGN KEY (query_id) REFERENCES rag_query_logs(query_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- 인덱스
    INDEX idx_query_id (query_id),
    INDEX idx_user_id (user_id),
    INDEX idx_rating (rating),
    INDEX idx_feedback_type (feedback_type)
);
```

### 2.5 rag_indexing_jobs

비동기 인덱싱 작업을 추적합니다.

```sql
CREATE TABLE rag_indexing_jobs (
    job_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    document_id VARCHAR(36) NOT NULL,
    
    -- 작업 상태
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    progress INTEGER NOT NULL DEFAULT 0,  -- 0-100
    current_step VARCHAR(50),  -- 'parsing', 'embedding', 'indexing'
    
    -- 진행 상황
    chunks_processed INTEGER DEFAULT 0,
    chunks_total INTEGER DEFAULT 0,
    
    -- 타임스탬프
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_completion TIMESTAMP,
    
    -- 에러 정보
    error_message TEXT,
    error_stack TEXT,
    
    -- 외래 키
    FOREIGN KEY (document_id) REFERENCES rag_documents(document_id) ON DELETE CASCADE,
    
    -- 인덱스
    INDEX idx_status (status),
    INDEX idx_document_id (document_id)
);
```

---

## 3. 인덱스 전략

### 3.1 성능 최적화 인덱스

```sql
-- 자주 사용되는 필터 조합
CREATE INDEX idx_chunks_filter ON rag_chunks (
    (CAST(metadata->>'$.policy_version' AS CHAR(20))),
    (CAST(metadata->>'$.scope_type' AS CHAR(20))),
    (CAST(metadata->>'$.grade_level' AS CHAR(20)))
);

-- 최근 질의 조회
CREATE INDEX idx_recent_queries ON rag_query_logs (
    user_id,
    created_at DESC
);

-- 피드백 통계
CREATE INDEX idx_feedback_stats ON rag_feedback (
    rating,
    feedback_type,
    created_at
);
```

### 3.2 파티셔닝 (대용량 데이터 대비)

```sql
-- rag_query_logs를 월별로 파티셔닝
ALTER TABLE rag_query_logs
PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
    PARTITION p202511 VALUES LESS THAN (202512),
    PARTITION p202512 VALUES LESS THAN (202601),
    PARTITION p202601 VALUES LESS THAN (202602),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

---

## 4. 마이그레이션

### 4.1 Alembic 마이그레이션 스크립트

```python
# backend/alembic/versions/001_create_rag_tables.py

"""create rag tables

Revision ID: 001_rag_tables
Revises: [previous_revision]
Create Date: 2025-11-20 22:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '001_rag_tables'
down_revision = '[previous_revision]'
branch_labels = None
depends_on = None

def upgrade():
    # rag_documents
    op.create_table(
        'rag_documents',
        sa.Column('document_id', sa.String(36), primary_key=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('policy_version', sa.String(20), nullable=False),
        sa.Column('scope_type', sa.String(20), nullable=False),
        sa.Column('institution_id', sa.String(100)),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('chunks_count', sa.Integer, server_default='0'),
        sa.Column('processing_started_at', sa.TIMESTAMP),
        sa.Column('processing_completed_at', sa.TIMESTAMP),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # 인덱스 생성
    op.create_index('idx_status', 'rag_documents', ['status'])
    op.create_index('idx_document_type', 'rag_documents', ['document_type'])
    op.create_index('idx_policy_version', 'rag_documents', ['policy_version'])
    op.create_index('idx_file_hash', 'rag_documents', ['file_hash'])
    op.create_index('idx_file_path', 'rag_documents', ['file_path'], unique=True)
    
    # rag_chunks
    op.create_table(
        'rag_chunks',
        sa.Column('chunk_id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('metadata', mysql.JSON, nullable=False),
        sa.Column('embedding_model', sa.String(100), nullable=False, server_default='text-embedding-3-large'),
        sa.Column('embedding_dimension', sa.Integer, nullable=False, server_default='3072'),
        sa.Column('vector_id', sa.String(100)),
        sa.Column('curriculum_id', sa.String(36)),
        sa.Column('node_id', sa.String(36)),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['rag_documents.document_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['curriculum_id'], ['curriculums.curriculum_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.node_id'], ondelete='SET NULL'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # 나머지 테이블 생성...

def downgrade():
    op.drop_table('rag_feedback')
    op.drop_table('rag_query_logs')
    op.drop_table('rag_indexing_jobs')
    op.drop_table('rag_chunks')
    op.drop_table('rag_documents')
```

### 4.2 마이그레이션 실행

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "create rag tables"

# 마이그레이션 적용
alembic upgrade head

# 롤백
alembic downgrade -1
```

---

## 5. 데이터 정합성

### 5.1 제약 조건

```sql
-- 문서 상태 검증
ALTER TABLE rag_documents
ADD CONSTRAINT chk_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'));

-- 평점 범위 검증
ALTER TABLE rag_feedback
ADD CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5);

-- 진행률 범위 검증
ALTER TABLE rag_indexing_jobs
ADD CONSTRAINT chk_progress CHECK (progress BETWEEN 0 AND 100);
```

### 5.2 트리거

```sql
-- 청크 수 자동 업데이트
DELIMITER $$

CREATE TRIGGER update_chunks_count_insert
AFTER INSERT ON rag_chunks
FOR EACH ROW
BEGIN
    UPDATE rag_documents
    SET chunks_count = chunks_count + 1
    WHERE document_id = NEW.document_id;
END$$

CREATE TRIGGER update_chunks_count_delete
AFTER DELETE ON rag_chunks
FOR EACH ROW
BEGIN
    UPDATE rag_documents
    SET chunks_count = chunks_count - 1
    WHERE document_id = OLD.document_id;
END$$

DELIMITER ;
```

### 5.3 데이터 정리 (Cleanup)

```sql
-- 90일 이상 된 로그 삭제
DELETE FROM rag_query_logs
WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- 실패한 인덱싱 작업 정리
DELETE FROM rag_indexing_jobs
WHERE status = 'failed'
AND completed_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

---

## 6. 백업 및 복구

### 6.1 백업 전략

```bash
# 전체 백업
mysqldump -u root -p mathesis_lab \
  rag_documents rag_chunks rag_query_logs rag_feedback rag_indexing_jobs \
  > rag_backup_$(date +%Y%m%d).sql

# 증분 백업 (최근 1일 데이터만)
mysqldump -u root -p mathesis_lab \
  --where="created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)" \
  rag_query_logs rag_feedback \
  > rag_incremental_$(date +%Y%m%d).sql
```

### 6.2 복구

```bash
# 복구
mysql -u root -p mathesis_lab < rag_backup_20251120.sql
```

---

**문서 버전**: 1.0  
**작성일**: 2025-11-20  
**작성자**: MATHESIS LAB 개발팀  
**DB 버전**: PostgreSQL 14+ / MySQL 8.0+
