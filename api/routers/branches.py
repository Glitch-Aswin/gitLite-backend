from fastapi import APIRouter, Depends, HTTPException
from api.auth import get_current_user_id
from api.database import get_db
from api.services.branch_service import BranchService
from api.models.branch_schemas import (
    BranchCreate,
    BranchResponse,
    MergeRequestCreate,
    MergeRequestResponse,
    ConflictResolution
)
from typing import List, Optional

router = APIRouter()


@router.post("/repositories/{repo_id}/branches", response_model=BranchResponse)
async def create_branch(
    repo_id: int,
    branch_data: BranchCreate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Create a new branch in the repository
    
    - **repo_id**: Repository ID
    - **name**: Branch name
    - **parent_branch_name**: Name of parent branch (optional, defaults to repository default branch)
    """
    service = BranchService(db)
    branch = await service.create_branch(repo_id, branch_data, user_id)
    return branch


@router.get("/repositories/{repo_id}/branches", response_model=List[BranchResponse])
async def list_branches(
    repo_id: int,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    List all branches in a repository
    
    - **repo_id**: Repository ID
    """
    service = BranchService(db)
    branches = await service.list_branches(repo_id)
    return branches


@router.get("/repositories/{repo_id}/branches/{branch_name}")
async def get_branch(
    repo_id: int,
    branch_name: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Get branch details with file versions
    
    - **repo_id**: Repository ID
    - **branch_name**: Branch name
    """
    service = BranchService(db)
    branch = await service.get_branch(repo_id, branch_name)
    return branch


@router.get("/repositories/{repo_id}/branches/{branch_name}/versions")
async def get_branch_versions(
    repo_id: int,
    branch_name: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Get all version history for a branch
    
    - **repo_id**: Repository ID
    - **branch_name**: Branch name
    
    Returns all versions that have been created or modified in this branch
    """
    service = BranchService(db)
    versions = await service.get_branch_version_history(repo_id, branch_name)
    return versions


@router.delete("/repositories/{repo_id}/branches/{branch_name}")
async def delete_branch(
    repo_id: int,
    branch_name: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Delete a branch (cannot delete default branch)
    
    - **repo_id**: Repository ID
    - **branch_name**: Branch name
    """
    service = BranchService(db)
    result = await service.delete_branch(repo_id, branch_name)
    return result


@router.post("/repositories/{repo_id}/merge-requests", response_model=MergeRequestResponse)
async def create_merge_request(
    repo_id: int,
    merge_data: MergeRequestCreate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Create a merge request between two branches
    
    - **repo_id**: Repository ID
    - **source_branch**: Source branch name
    - **target_branch**: Target branch name
    - **title**: Merge request title
    - **description**: Description (optional)
    
    Automatically detects conflicts between branches
    """
    service = BranchService(db)
    merge_request = await service.create_merge_request(repo_id, merge_data, user_id)
    return merge_request


@router.get("/repositories/{repo_id}/merge-requests")
async def list_merge_requests(
    repo_id: int,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    List merge requests for a repository
    
    - **repo_id**: Repository ID
    - **status**: Filter by status (open, merged, closed, conflicts) (optional)
    """
    service = BranchService(db)
    merge_requests = await service.get_merge_requests(repo_id, status)
    return merge_requests


@router.post("/merge-requests/{merge_request_id}/merge")
async def merge_branches(
    merge_request_id: int,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Execute merge after all conflicts are resolved
    
    - **merge_request_id**: Merge request ID
    """
    service = BranchService(db)
    result = await service.merge_branches(merge_request_id, user_id)
    return result


@router.post("/merge-conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: int,
    resolution: ConflictResolution,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Resolve a merge conflict
    
    - **conflict_id**: Conflict ID
    - **resolution_strategy**: Strategy used (theirs, ours, manual)
    - **resolved_content**: Final resolved content (base64 encoded)
    """
    service = BranchService(db)
    result = await service.resolve_conflict(conflict_id, resolution)
    return result
