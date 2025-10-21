from fastapi import APIRouter, Depends, Header, HTTPException
from api.database import get_db
from api.models.schemas import (
    RepositoryCreate, 
    RepositoryUpdate, 
    RepositoryResponse,
    RepositoryStats,
    ActivityItem,
    CompareRequest
)
from api.services.repository_service import RepositoryService
from api.auth import get_current_user_id
from typing import List

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=List[RepositoryResponse])
async def list_repositories(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """List all repositories owned by the authenticated user"""
    service = RepositoryService(db)
    return await service.list_user_repositories(user_id)


@router.post("", response_model=RepositoryResponse)
async def create_repository(
    repo: RepositoryCreate,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Create a new repository"""
    service = RepositoryService(db)
    return await service.create_repository(repo, user_id)


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: int,
    db = Depends(get_db)
):
    """Get repository details"""
    service = RepositoryService(db)
    return await service.get_repository(repo_id)


@router.put("/{repo_id}", response_model=RepositoryResponse)
async def update_repository(
    repo_id: int,
    repo_update: RepositoryUpdate,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Update repository metadata"""
    service = RepositoryService(db)
    return await service.update_repository(repo_id, repo_update, user_id)


@router.delete("/{repo_id}")
async def delete_repository(
    repo_id: int,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Delete repository"""
    service = RepositoryService(db)
    return await service.delete_repository(repo_id, user_id)


@router.get("/{repo_id}/stats", response_model=RepositoryStats)
async def get_repository_stats(
    repo_id: int,
    db = Depends(get_db)
):
    """Get repository statistics"""
    service = RepositoryService(db)
    return await service.get_repository_stats(repo_id)


@router.get("/{repo_id}/activity", response_model=List[ActivityItem])
async def get_repository_activity(
    repo_id: int,
    limit: int = 20,
    db = Depends(get_db)
):
    """Get recent activity across all files in repository"""
    service = RepositoryService(db)
    return await service.get_repository_activity(repo_id, limit)


@router.post("/{repo_id}/compare")
async def compare_repository_states(
    repo_id: int,
    compare_data: CompareRequest,
    db = Depends(get_db)
):
    """
    Compare repository states between two dates.
    This is a simplified implementation.
    """
    service = RepositoryService(db)
    
    # Verify repository exists
    await service.get_repository(repo_id)
    
    # Get files and versions at each date
    files_response = db.table('files').select('id, filename').eq('repository_id', repo_id).execute()
    
    comparison = {
        'repository_id': repo_id,
        'state1_date': compare_data.state1_date,
        'state2_date': compare_data.state2_date,
        'changes': []
    }
    
    for file in files_response.data:
        # Get versions before each date
        v1_response = db.table('file_versions') \
            .select('version_number') \
            .eq('file_id', file['id']) \
            .lte('created_at', compare_data.state1_date.isoformat()) \
            .order('version_number', desc=True) \
            .limit(1) \
            .execute()
        
        v2_response = db.table('file_versions') \
            .select('version_number') \
            .eq('file_id', file['id']) \
            .lte('created_at', compare_data.state2_date.isoformat()) \
            .order('version_number', desc=True) \
            .limit(1) \
            .execute()
        
        v1 = v1_response.data[0]['version_number'] if v1_response.data else None
        v2 = v2_response.data[0]['version_number'] if v2_response.data else None
        
        if v1 != v2:
            comparison['changes'].append({
                'file_id': file['id'],
                'filename': file['filename'],
                'version_at_state1': v1,
                'version_at_state2': v2
            })
    
    return comparison
