from supabase import Client
from api.models.schemas import FileCreate, FileUpdate
from api.utils.helpers import calculate_content_hash, calculate_file_size, generate_diff, detect_mime_type
from fastapi import HTTPException
from typing import Optional


class FileService:
    def __init__(self, db: Client):
        self.db = db
    
    async def create_file(self, repo_id: int, file_data: FileCreate):
        """Create a new file in repository"""
        # Verify repository exists
        repo_response = self.db.table('repositories').select('id').eq('id', repo_id).execute()
        if not repo_response.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Check if file already exists
        existing = self.db.table('files').select('id').eq('repository_id', repo_id).eq('filename', file_data.filename).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="File already exists in repository")
        
        # Detect mime type
        mime_type = file_data.mime_type or detect_mime_type(file_data.filename)
        
        # Create file record
        file_response = self.db.table('files').insert({
            'repository_id': repo_id,
            'filename': file_data.filename,
            'current_version': 1
        }).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=400, detail="Failed to create file")
        
        file_id = file_response.data[0]['id']
        
        # Create first version
        content = file_data.content_text or file_data.content_binary
        if content:
            content_hash = calculate_content_hash(content)
            file_size = calculate_file_size(content)
            
            version_data = {
                'file_id': file_id,
                'version_number': 1,
                'commit_message': file_data.commit_message or "Initial commit",
                'content_hash': content_hash,
                'file_size': file_size,
                'mime_type': mime_type,
                'is_full_content': True
            }
            
            if file_data.content_text:
                version_data['content_text'] = file_data.content_text
            if file_data.content_binary:
                version_data['content_binary'] = file_data.content_binary
            
            self.db.table('file_versions').insert(version_data).execute()
        
        return file_response.data[0]
    
    async def get_files_in_repository(self, repo_id: int):
        """List all files in repository"""
        # Verify repository exists
        repo_response = self.db.table('repositories').select('id').eq('id', repo_id).execute()
        if not repo_response.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        response = self.db.table('files').select('*').eq('repository_id', repo_id).execute()
        return response.data
    
    async def get_file(self, repo_id: int, file_id: int):
        """Get specific file details with current version content"""
        file_response = self.db.table('files').select('*').eq('repository_id', repo_id).eq('id', file_id).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_data = file_response.data[0]
        
        # Get current version content
        version_response = self.db.table('file_versions') \
            .select('content_text, content_binary, mime_type, file_size') \
            .eq('file_id', file_id) \
            .eq('version_number', file_data['current_version']) \
            .execute()
        
        if version_response.data:
            version_data = version_response.data[0]
            file_data['content_text'] = version_data.get('content_text')
            file_data['content_binary'] = version_data.get('content_binary')
            file_data['mime_type'] = version_data.get('mime_type')
            file_data['file_size'] = version_data.get('file_size')
        
        return file_data
    
    async def update_file(self, repo_id: int, file_id: int, file_update: FileUpdate):
        """Update file (creates new version)"""
        # Get current file
        file_response = self.db.table('files').select('*').eq('id', file_id).eq('repository_id', repo_id).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        current_file = file_response.data[0]
        new_version = current_file['current_version'] + 1
        
        # Get previous version for parent_version_id
        prev_version_response = self.db.table('file_versions') \
            .select('id, mime_type') \
            .eq('file_id', file_id) \
            .eq('version_number', current_file['current_version']) \
            .execute()
        
        parent_version_id = prev_version_response.data[0]['id'] if prev_version_response.data else None
        mime_type = prev_version_response.data[0]['mime_type'] if prev_version_response.data else 'text/plain'
        
        # Create new version
        content = file_update.content_text or file_update.content_binary
        content_hash = calculate_content_hash(content)
        file_size = calculate_file_size(content)
        
        version_data = {
            'file_id': file_id,
            'version_number': new_version,
            'parent_version_id': parent_version_id,
            'commit_message': file_update.commit_message,
            'content_hash': content_hash,
            'file_size': file_size,
            'mime_type': mime_type,
            'is_full_content': True
        }
        
        if file_update.content_text:
            version_data['content_text'] = file_update.content_text
        if file_update.content_binary:
            version_data['content_binary'] = file_update.content_binary
        
        self.db.table('file_versions').insert(version_data).execute()
        
        # Update current version in files table
        self.db.table('files').update({'current_version': new_version}).eq('id', file_id).execute()
        
        return await self.get_file(repo_id, file_id)
    
    async def delete_file(self, repo_id: int, file_id: int):
        """Delete file"""
        # Verify file exists
        file_response = self.db.table('files').select('id').eq('id', file_id).eq('repository_id', repo_id).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        self.db.table('files').delete().eq('id', file_id).execute()
        
        return {"message": "File deleted successfully"}
    
    async def get_file_versions(self, repo_id: int, file_id: int):
        """List all versions of a file"""
        # Verify file exists
        file_response = self.db.table('files').select('id, filename').eq('id', file_id).eq('repository_id', repo_id).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        versions_response = self.db.table('file_versions') \
            .select('id, file_id, version_number, parent_version_id, created_at, commit_message, content_hash, file_size, mime_type') \
            .eq('file_id', file_id) \
            .order('version_number', desc=False) \
            .execute()
        
        return versions_response.data
    
    async def get_file_version(self, repo_id: int, file_id: int, version: int):
        """Get specific version of a file"""
        # Verify file exists
        file_response = self.db.table('files').select('id').eq('id', file_id).eq('repository_id', repo_id).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        version_response = self.db.table('file_versions') \
            .select('*') \
            .eq('file_id', file_id) \
            .eq('version_number', version) \
            .execute()
        
        if not version_response.data:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return version_response.data[0]
    
    async def diff_versions(self, repo_id: int, file_id: int, v1: int, v2: int):
        """Compare two versions of a file"""
        # Verify file exists
        file_response = self.db.table('files').select('filename').eq('id', file_id).eq('repository_id', repo_id).execute()
        
        if not file_response.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        filename = file_response.data[0]['filename']
        
        # Get both versions
        version1 = await self.get_file_version(repo_id, file_id, v1)
        version2 = await self.get_file_version(repo_id, file_id, v2)
        
        # Only text files can be diffed
        if not version1.get('content_text') or not version2.get('content_text'):
            raise HTTPException(status_code=400, detail="Can only diff text files")
        
        diff = generate_diff(version1['content_text'], version2['content_text'])
        
        return {
            'file_id': file_id,
            'filename': filename,
            'version1': v1,
            'version2': v2,
            'diff': diff
        }
