from fastapi import APIRouter, Depends, Query
from api.database import get_db
from api.models.schemas import (
    FileCreate,
    FileUpdate,
    FileResponse,
    FileDetailResponse,
    FileVersionResponse,
    FileVersionDetailResponse,
    FileDiffResponse
)
from api.services.file_service import FileService
from typing import List, Optional

router = APIRouter(tags=["files"])


@router.post("/repositories/{repo_id}/files", response_model=FileResponse)
async def create_file(
    repo_id: int,
    file_data: FileCreate,
    branch: Optional[str] = Query(None, description="Upload file to specific branch"),
    db = Depends(get_db)
):
    """
    Create or upload a new file to repository
    
    - **repo_id**: Repository ID
    - **file_data**: File content and metadata
    - **branch**: Optional branch name to upload file to specific branch
    """
    service = FileService(db)
    return await service.create_file(repo_id, file_data, branch)


@router.get("/repositories/{repo_id}/files", response_model=List[FileResponse])
async def list_files(
    repo_id: int,
    branch: Optional[str] = Query(None, description="Filter files by branch name"),
    db = Depends(get_db)
):
    """
    List all files in repository
    
    - **repo_id**: Repository ID
    - **branch**: Optional branch name to filter files for specific branch
    """
    service = FileService(db)
    return await service.get_files_in_repository(repo_id, branch)


@router.get("/repositories/{repo_id}/files/{file_id}", response_model=FileDetailResponse)
async def get_file(
    repo_id: int,
    file_id: int,
    branch: Optional[str] = Query(None, description="Get file version from specific branch"),
    db = Depends(get_db)
):
    """
    Get specific file details with version content
    
    - **repo_id**: Repository ID
    - **file_id**: File ID
    - **branch**: Optional branch name to get branch-specific version
    """
    service = FileService(db)
    return await service.get_file(repo_id, file_id, branch)


@router.put("/repositories/{repo_id}/files/{file_id}", response_model=FileDetailResponse)
async def update_file(
    repo_id: int,
    file_id: int,
    file_update: FileUpdate,
    branch: Optional[str] = Query(None, description="Update file in specific branch"),
    db = Depends(get_db)
):
    """
    Update file (creates new version)
    
    - **repo_id**: Repository ID
    - **file_id**: File ID
    - **file_update**: Updated content and commit message
    - **branch**: Optional branch name to create version in specific branch
    """
    service = FileService(db)
    return await service.update_file(repo_id, file_id, file_update, branch)


@router.delete("/repositories/{repo_id}/files/{file_id}")
async def delete_file(
    repo_id: int,
    file_id: int,
    db = Depends(get_db)
):
    """Delete file"""
    service = FileService(db)
    return await service.delete_file(repo_id, file_id)


@router.get("/repositories/{repo_id}/files/{file_id}/versions", response_model=List[FileVersionResponse])
async def list_file_versions(
    repo_id: int,
    file_id: int,
    branch: Optional[str] = Query(None, description="Get versions for specific branch only"),
    db = Depends(get_db)
):
    """
    List versions of a file
    
    - **repo_id**: Repository ID
    - **file_id**: File ID
    - **branch**: Optional branch name - if provided, returns only the version this branch points to
    """
    service = FileService(db)
    return await service.get_file_versions(repo_id, file_id, branch)


@router.get("/repositories/{repo_id}/files/{file_id}/versions/{version}", response_model=FileVersionDetailResponse)
async def get_file_version(
    repo_id: int,
    file_id: int,
    version: int,
    db = Depends(get_db)
):
    """Get specific version of a file"""
    service = FileService(db)
    return await service.get_file_version(repo_id, file_id, version)


@router.get("/repositories/{repo_id}/files/{file_id}/diff/{v1}/{v2}")
async def diff_file_versions(
    repo_id: int,
    file_id: int,
    v1: int,
    v2: int,
    db = Depends(get_db)
):
    """
    Compare two versions of a file with enhanced diff formats.
    
    Returns multiple diff formats:
    - **diff**: Enhanced unified diff with statistics (git-style)
    - **side_by_side**: Detailed line-by-line comparison with metadata
    - **compact**: Concise diff showing only changed sections
    
    Perfect for:
    - Code review workflows
    - Change tracking
    - Visual diff displays in UI
    """
    service = FileService(db)
    return await service.diff_versions(repo_id, file_id, v1, v2)
