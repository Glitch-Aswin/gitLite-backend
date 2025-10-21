from supabase import Client
from api.models.schemas import RepositoryCreate, RepositoryUpdate
from fastapi import HTTPException


class RepositoryService:
    def __init__(self, db: Client):
        self.db = db
    
    async def create_repository(self, repo: RepositoryCreate, owner_id: str):
        """Create a new repository"""
        try:
            response = self.db.table('repositories').insert({
                'name': repo.name,
                'description': repo.description,
                'owner_id': owner_id
            }).execute()
            
            if not response.data:
                raise HTTPException(status_code=400, detail="Failed to create repository")
            
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error creating repository: {str(e)}")
    
    async def get_repository(self, repo_id: int):
        """Get repository by ID"""
        response = self.db.table('repositories').select('*').eq('id', repo_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        return response.data[0]
    
    async def update_repository(self, repo_id: int, repo_update: RepositoryUpdate, owner_id: str):
        """Update repository metadata"""
        # First check if repository exists and belongs to user
        existing = await self.get_repository(repo_id)
        if existing['owner_id'] != owner_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this repository")
        
        # Build update dict with only provided fields
        update_data = {k: v for k, v in repo_update.model_dump().items() if v is not None}
        
        if not update_data:
            return existing
        
        response = self.db.table('repositories').update(update_data).eq('id', repo_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to update repository")
        
        return response.data[0]
    
    async def delete_repository(self, repo_id: int, owner_id: str):
        """Delete repository"""
        # First check if repository exists and belongs to user
        existing = await self.get_repository(repo_id)
        if existing['owner_id'] != owner_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this repository")
        
        response = self.db.table('repositories').delete().eq('id', repo_id).execute()
        
        return {"message": "Repository deleted successfully"}
    
    async def get_repository_stats(self, repo_id: int):
        """Get repository statistics"""
        # Verify repository exists
        await self.get_repository(repo_id)
        
        # Get file count
        files_response = self.db.table('files').select('id', count='exact').eq('repository_id', repo_id).execute()
        file_count = files_response.count or 0
        
        # Get total versions and size
        versions_response = self.db.table('file_versions') \
            .select('file_size, files!inner(repository_id)') \
            .eq('files.repository_id', repo_id) \
            .execute()
        
        total_size = sum(v.get('file_size', 0) or 0 for v in versions_response.data)
        version_count = len(versions_response.data)
        
        # Get last activity
        last_activity_response = self.db.table('file_versions') \
            .select('created_at, files!inner(repository_id)') \
            .eq('files.repository_id', repo_id) \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
        
        last_activity = last_activity_response.data[0]['created_at'] if last_activity_response.data else None
        
        return {
            'total_files': file_count,
            'total_size': total_size,
            'total_versions': version_count,
            'last_activity': last_activity
        }
    
    async def get_repository_activity(self, repo_id: int, limit: int = 20):
        """Get recent activity across all files in repository"""
        # Verify repository exists
        await self.get_repository(repo_id)
        
        response = self.db.table('file_versions') \
            .select('id, file_id, version_number, commit_message, created_at, files!inner(filename, repository_id)') \
            .eq('files.repository_id', repo_id) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        activities = []
        for item in response.data:
            activities.append({
                'file_id': item['file_id'],
                'filename': item['files']['filename'],
                'version_number': item['version_number'],
                'commit_message': item.get('commit_message'),
                'created_at': item['created_at']
            })
        
        return activities
