from fastapi import APIRouter

# Try to import all endpoints, with fallback for CI/CD compatibility
try:
    from backend.app.api.v1.endpoints import auth, curriculums, nodes, literature, youtube, simple_crud, gcp, google_drive, sync
    GOOGLE_DRIVE_AVAILABLE = True
    SYNC_AVAILABLE = True
except ImportError:
    # If any endpoint import fails, import without it
    try:
        from backend.app.api.v1.endpoints import auth, curriculums, nodes, literature, youtube, simple_crud, gcp, sync
        google_drive = None
        GOOGLE_DRIVE_AVAILABLE = False
        SYNC_AVAILABLE = True
    except ImportError:
        # If sync also fails, import without it
        from backend.app.api.v1.endpoints import auth, curriculums, nodes, literature, youtube, simple_crud, gcp
        google_drive = None
        sync = None
        GOOGLE_DRIVE_AVAILABLE = False
        SYNC_AVAILABLE = False

api_router = APIRouter()
api_router.include_router(auth.router)  # Auth endpoints at /auth
api_router.include_router(curriculums.router, prefix="/curriculums", tags=["curriculums"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
api_router.include_router(literature.router, prefix="/literature", tags=["literature"])
api_router.include_router(youtube.router, prefix="/youtube", tags=["youtube"])
api_router.include_router(simple_crud.router, prefix="/simple-curriculums", tags=["simple-curriculums"])
api_router.include_router(gcp.router)  # GCP endpoints at /gcp

# Only include Google Drive router if available
if GOOGLE_DRIVE_AVAILABLE and google_drive is not None:
    api_router.include_router(google_drive.router)  # Google Drive endpoints at /google-drive

# Only include Sync router if available
if SYNC_AVAILABLE and sync is not None:
    api_router.include_router(sync.router)  # Sync endpoints at /sync