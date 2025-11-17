
export interface NodeContent {
    content_id: string;
    node_id: string;
    markdown_content?: string;
    ai_generated_summary?: string;
    ai_generated_extension?: string;
    manim_guidelines?: string;
    created_at: string;
    updated_at: string;
}

export interface NodeLinkResponse {
    link_id: string;
    node_id: string;
    link_type: string;
    zotero_key?: string;
    youtube_video_id?: string;
    drive_file_id?: string;
    file_name?: string;
    file_size_bytes?: number;
    file_mime_type?: string;
    linked_node_id?: string;
    link_relationship?: string;
    created_at: string;
}

export interface NodeLinkZoteroCreate {
    zotero_key: string;
}

export interface NodeLinkYouTubeCreate {
    youtube_url: string;
}

export interface NodeLinkPDFCreate {
    drive_file_id: string;
    file_name: string;
    file_size_bytes?: number;
    file_mime_type?: string;
}

export interface NodeLinkNodeCreate {
    linked_node_id: string;
    link_relationship?: string;
}

export type NodeType =
    | 'CHAPTER'
    | 'SECTION'
    | 'TOPIC'
    | 'CONTENT'
    | 'ASSESSMENT'
    | 'QUESTION'
    | 'PROJECT';

export interface Node {
    node_id: string;
    curriculum_id: string;
    title: string;
    order_index: number;
    node_type: NodeType;  // [NEW] Explicit node type
    deleted_at?: string | null;  // [NEW] Soft deletion timestamp
    created_at: string;
    updated_at: string;
    parent_node_id?: string;
    content?: NodeContent; // Changed to NodeContent interface
    links?: NodeLinkResponse[]; // Changed to array of NodeLink interface
}

export interface NodeCreate {
    title: string;
    parent_node_id?: string;
    node_type?: NodeType;  // [NEW] Optional node type (defaults to CONTENT)
}

export interface Curriculum {
    curriculum_id: string;
    title: string;
    description: string;
    icon?: string;
    author?: string;
    image?: string;
    nodes: Node[];
    created_at?: string;
    updated_at?: string;
    is_public?: boolean;
}

export interface CurriculumCreate {
    title: string;
    description?: string;
}

export interface CurriculumUpdate {
    title?: string;
    description?: string;
    is_public?: boolean;
}

// GCP Integration Types
export interface BackupInfo {
    backup_id: string;
    timestamp: string;
    size_mb: number;
    device_id: string;
    device_name: string;
    checksum: string;
    compression_ratio?: number;
}

export interface BackupRestoreOptions {
    device_id: string;
    available_backups: BackupInfo[];
    latest_backup?: BackupInfo;
    conflict_resolution?: 'latest' | 'manual' | 'merge';
}

export interface SyncMetadata {
    sync_id: string;
    device_id: string;
    device_name: string;
    last_sync: string;
    last_modified: string;
    sync_status: 'pending' | 'in_progress' | 'completed' | 'failed';
    error_message?: string;
}

export interface GCPStatus {
    enabled: boolean;
    project_id?: string;
    location?: string;
    available_services: string[];
    last_health_check: string;
    features_available: {
        cloud_storage: boolean;
        backup_restore: boolean;
        multi_device_sync: boolean;
        ai_features: boolean;
    };
}

export interface BackupCreateRequest {
    device_name?: string;
    description?: string;
}

export interface BackupRestoreRequest {
    backup_id: string;
    conflict_resolution?: 'latest' | 'manual' | 'merge';
}

export interface AIContentRequest {
    content: string;
    node_id: string;
}

export interface AIContentResponse {
    result: string;
    tokens_used: number;
    processing_time_ms: number;
}

export interface ManimGuidelinesRequest {
    node_id: string;
    image_base64: string;
    image_filename: string;
}

export interface DeviceSyncStatus {
    device_id: string;
    device_name: string;
    last_sync: string;
    sync_status: 'synced' | 'pending' | 'error';
    pending_changes: number;
}
