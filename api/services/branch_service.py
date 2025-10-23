from supabase import Client
from api.models.branch_schemas import (
    BranchCreate,
    MergeRequestCreate,
    MergeConflictInfo,
    ConflictResolution
)
from fastapi import HTTPException
from typing import List, Dict


class BranchService:
    def __init__(self, db: Client):
        self.db = db
    
    async def create_branch(self, repo_id: int, branch_data: BranchCreate, user_id: str):
        """Create a new branch from parent branch"""
        # Verify repository exists
        repo = self.db.table('repositories').select('id').eq('id', repo_id).execute()
        if not repo.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Check if branch already exists
        existing = self.db.table('branches')\
            .select('id')\
            .eq('repository_id', repo_id)\
            .eq('name', branch_data.name)\
            .execute()
        
        if existing.data:
            raise HTTPException(status_code=400, detail=f"Branch '{branch_data.name}' already exists")
        
        # Get parent branch
        parent_branch = None
        if branch_data.parent_branch_name:
            parent_response = self.db.table('branches')\
                .select('id')\
                .eq('repository_id', repo_id)\
                .eq('name', branch_data.parent_branch_name)\
                .execute()
            
            if not parent_response.data:
                raise HTTPException(status_code=404, detail=f"Parent branch '{branch_data.parent_branch_name}' not found")
            parent_branch = parent_response.data[0]
        
        # Create branch
        branch_response = self.db.table('branches').insert({
            'repository_id': repo_id,
            'name': branch_data.name,
            'parent_branch_id': parent_branch['id'] if parent_branch else None,
            'created_by': user_id,
            'is_default': False
        }).execute()
        
        if not branch_response.data:
            raise HTTPException(status_code=400, detail="Failed to create branch")
        
        new_branch = branch_response.data[0]
        
        # Copy file pointers from parent
        if parent_branch:
            parent_pointers = self.db.table('branch_file_pointers')\
                .select('file_id, version_id, version_number')\
                .eq('branch_id', parent_branch['id'])\
                .execute()
            
            if parent_pointers.data:
                new_pointers = [
                    {
                        'branch_id': new_branch['id'],
                        'file_id': p['file_id'],
                        'version_id': p['version_id'],
                        'version_number': p['version_number']
                    }
                    for p in parent_pointers.data
                ]
                self.db.table('branch_file_pointers').insert(new_pointers).execute()
        
        return new_branch
    
    async def list_branches(self, repo_id: int):
        """List all branches"""
        response = self.db.table('branches')\
            .select('*')\
            .eq('repository_id', repo_id)\
            .order('is_default', desc=True)\
            .order('created_at', desc=True)\
            .execute()
        
        return response.data
    
    async def get_branch(self, repo_id: int, branch_name: str):
        """Get branch with file versions"""
        branch = self.db.table('branches')\
            .select('*')\
            .eq('repository_id', repo_id)\
            .eq('name', branch_name)\
            .execute()
        
        if not branch.data:
            raise HTTPException(status_code=404, detail=f"Branch '{branch_name}' not found")
        
        branch_data = branch.data[0]
        
        # Get files in this branch
        files = self.db.table('branch_file_pointers')\
            .select('file_id, version_id, version_number, files!inner(filename, repository_id)')\
            .eq('branch_id', branch_data['id'])\
            .execute()
        
        branch_data['files'] = files.data
        return branch_data
    
    async def get_branch_version_history(self, repo_id: int, branch_name: str):
        """Get all version history for a branch"""
        # Get branch
        branch = self.db.table('branches')\
            .select('id')\
            .eq('repository_id', repo_id)\
            .eq('name', branch_name)\
            .execute()
        
        if not branch.data:
            raise HTTPException(status_code=404, detail=f"Branch '{branch_name}' not found")
        
        branch_id = branch.data[0]['id']
        
        # Get all versions from branch_versions table
        versions = self.db.table('branch_versions')\
            .select('*, files!inner(filename), file_versions!inner(commit_message, created_at, file_size, mime_type, content_hash)')\
            .eq('branch_id', branch_id)\
            .order('created_at', desc=True)\
            .execute()
        
        return versions.data
    
    async def delete_branch(self, repo_id: int, branch_name: str):
        """Delete branch (cannot delete default)"""
        branch = self.db.table('branches')\
            .select('id, is_default')\
            .eq('repository_id', repo_id)\
            .eq('name', branch_name)\
            .execute()
        
        if not branch.data:
            raise HTTPException(status_code=404, detail=f"Branch '{branch_name}' not found")
        
        if branch.data[0]['is_default']:
            raise HTTPException(status_code=400, detail="Cannot delete default branch")
        
        self.db.table('branches').delete().eq('id', branch.data[0]['id']).execute()
        return {"message": f"Branch '{branch_name}' deleted"}
    
    async def create_merge_request(self, repo_id: int, merge_data: MergeRequestCreate, user_id: str):
        """Create merge request with conflict detection"""
        # Get branches
        source = self.db.table('branches')\
            .select('id, name')\
            .eq('repository_id', repo_id)\
            .eq('name', merge_data.source_branch)\
            .execute()
        
        target = self.db.table('branches')\
            .select('id, name')\
            .eq('repository_id', repo_id)\
            .eq('name', merge_data.target_branch)\
            .execute()
        
        if not source.data:
            raise HTTPException(status_code=404, detail=f"Source branch '{merge_data.source_branch}' not found")
        if not target.data:
            raise HTTPException(status_code=404, detail=f"Target branch '{merge_data.target_branch}' not found")
        
        source_branch = source.data[0]
        target_branch = target.data[0]
        
        # Detect conflicts
        conflicts = await self._detect_conflicts(source_branch['id'], target_branch['id'])
        
        # Create merge request
        mr = self.db.table('merge_requests').insert({
            'repository_id': repo_id,
            'source_branch_id': source_branch['id'],
            'target_branch_id': target_branch['id'],
            'title': merge_data.title,
            'description': merge_data.description,
            'created_by': user_id,
            'status': 'conflicts' if conflicts else 'open',
            'has_conflicts': bool(conflicts)
        }).execute()
        
        if not mr.data:
            raise HTTPException(status_code=400, detail="Failed to create merge request")
        
        merge_request = mr.data[0]
        
        # Create conflict records
        if conflicts:
            conflict_records = [
                {
                    'merge_request_id': merge_request['id'],
                    'file_id': c['file_id'],
                    'source_version_id': c['source_version_id'],
                    'target_version_id': c['target_version_id'],
                    'conflict_type': 'content'
                }
                for c in conflicts
            ]
            self.db.table('merge_conflicts').insert(conflict_records).execute()
        
        return {
            **merge_request,
            'source_branch_name': source_branch['name'],
            'target_branch_name': target_branch['name'],
            'conflicts': [
                MergeConflictInfo(
                    file_id=c['file_id'],
                    filename=c['filename'],
                    conflict_type='content',
                    source_version=c['source_version'],
                    target_version=c['target_version']
                )
                for c in conflicts
            ]
        }
    
    async def _detect_conflicts(self, source_branch_id: int, target_branch_id: int) -> List[Dict]:
        """
        Detect merge conflicts between branches
        
        A conflict only occurs when BOTH branches have modified the same file
        with different content since they diverged.
        """
        conflicts = []
        
        # Get source branch to find parent (common ancestor)
        source_branch = self.db.table('branches')\
            .select('parent_branch_id')\
            .eq('id', source_branch_id)\
            .execute()
        
        parent_branch_id = source_branch.data[0]['parent_branch_id'] if source_branch.data else None
        
        # Get file pointers for all three: source, target, and parent (common ancestor)
        source_pointers = self.db.table('branch_file_pointers')\
            .select('file_id, version_id, version_number, files!inner(filename)')\
            .eq('branch_id', source_branch_id)\
            .execute()
        
        target_pointers = self.db.table('branch_file_pointers')\
            .select('file_id, version_id, version_number')\
            .eq('branch_id', target_branch_id)\
            .execute()
        
        # Get parent pointers if source was branched from target
        parent_pointers = {}
        if parent_branch_id == target_branch_id:
            # Source was branched directly from target
            # Use target's current state as baseline (simple approach)
            # In reality, we'd need to track branch creation time
            parent_pointers = {p['file_id']: p for p in target_pointers.data}
        elif parent_branch_id:
            # Source branched from another branch, get that branch's pointers
            parent_response = self.db.table('branch_file_pointers')\
                .select('file_id, version_id, version_number')\
                .eq('branch_id', parent_branch_id)\
                .execute()
            parent_pointers = {p['file_id']: p for p in parent_response.data}
        
        target_map = {p['file_id']: p for p in target_pointers.data}
        
        # Check for conflicts
        for source_p in source_pointers.data:
            file_id = source_p['file_id']
            
            # File exists in target?
            if file_id in target_map:
                target_p = target_map[file_id]
                
                # If versions are the same, no conflict
                if source_p['version_id'] == target_p['version_id']:
                    continue
                
                # Check if this is a real conflict or just a fast-forward
                # Get the parent/ancestor version for this file
                parent_version_id = parent_pointers.get(file_id, {}).get('version_id') if parent_pointers else None
                
                # If parent exists and source branched from target
                if parent_branch_id == target_branch_id and parent_version_id:
                    # Fast-forward check: Did target change since branching?
                    if target_p['version_id'] == parent_version_id:
                        # Target hasn't changed, source has
                        # This is a fast-forward merge, NOT a conflict
                        continue
                    
                    # Did source change since branching?
                    if source_p['version_id'] == parent_version_id:
                        # Source hasn't changed, target has
                        # No conflict, keep target's version
                        continue
                
                # Both versions differ from each other
                # Check if content actually differs (not just version numbers)
                source_v = self.db.table('file_versions')\
                    .select('content_hash')\
                    .eq('id', source_p['version_id'])\
                    .execute()
                
                target_v = self.db.table('file_versions')\
                    .select('content_hash')\
                    .eq('id', target_p['version_id'])\
                    .execute()
                
                # Only conflict if content hashes differ
                if (source_v.data and target_v.data and 
                    source_v.data[0]['content_hash'] != target_v.data[0]['content_hash']):
                    
                    # Check if parent has same content as either branch
                    if parent_version_id:
                        parent_v = self.db.table('file_versions')\
                            .select('content_hash')\
                            .eq('id', parent_version_id)\
                            .execute()
                        
                        if parent_v.data:
                            parent_hash = parent_v.data[0]['content_hash']
                            source_hash = source_v.data[0]['content_hash']
                            target_hash = target_v.data[0]['content_hash']
                            
                            # If source changed but target didn't: fast-forward (no conflict)
                            if target_hash == parent_hash and source_hash != parent_hash:
                                continue
                            
                            # If target changed but source didn't: keep target (no conflict)
                            if source_hash == parent_hash and target_hash != parent_hash:
                                continue
                    
                    # Real conflict: both branches modified the file differently
                    conflicts.append({
                        'file_id': file_id,
                        'filename': source_p['files']['filename'],
                        'source_version_id': source_p['version_id'],
                        'target_version_id': target_p['version_id'],
                        'source_version': source_p['version_number'],
                        'target_version': target_p['version_number']
                    })
        
        return conflicts
    
    async def merge_branches(self, merge_request_id: int, user_id: str):
        """Execute merge after conflicts resolved"""
        # Get merge request
        mr = self.db.table('merge_requests')\
            .select('*')\
            .eq('id', merge_request_id)\
            .execute()
        
        if not mr.data:
            raise HTTPException(status_code=404, detail="Merge request not found")
        
        merge_request = mr.data[0]
        
        if merge_request['status'] == 'merged':
            raise HTTPException(status_code=400, detail="Already merged")
        
        # Check all conflicts resolved
        if merge_request['has_conflicts']:
            unresolved = self.db.table('merge_conflicts')\
                .select('id')\
                .eq('merge_request_id', merge_request_id)\
                .eq('resolved', False)\
                .execute()
            
            if unresolved.data:
                raise HTTPException(status_code=400, detail="Unresolved conflicts remain")
        
        # Get resolved conflicts to skip them (already updated by resolve_conflict)
        resolved_conflicts = self.db.table('merge_conflicts')\
            .select('file_id')\
            .eq('merge_request_id', merge_request_id)\
            .eq('resolved', True)\
            .execute()
        
        resolved_file_ids = {c['file_id'] for c in resolved_conflicts.data}
        
        # Get source pointers
        source_pointers = self.db.table('branch_file_pointers')\
            .select('file_id, version_id, version_number')\
            .eq('branch_id', merge_request['source_branch_id'])\
            .execute()
        
        # Update target branch pointers (skip already resolved conflicts)
        for pointer in source_pointers.data:
            # Skip files that had conflicts (already resolved via resolve_conflict)
            if pointer['file_id'] in resolved_file_ids:
                continue
            
            existing = self.db.table('branch_file_pointers')\
                .select('id')\
                .eq('branch_id', merge_request['target_branch_id'])\
                .eq('file_id', pointer['file_id'])\
                .execute()
            
            if existing.data:
                # Update
                self.db.table('branch_file_pointers')\
                    .update({
                        'version_id': pointer['version_id'],
                        'version_number': pointer['version_number']
                    })\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
            else:
                # Insert
                self.db.table('branch_file_pointers').insert({
                    'branch_id': merge_request['target_branch_id'],
                    'file_id': pointer['file_id'],
                    'version_id': pointer['version_id'],
                    'version_number': pointer['version_number']
                }).execute()
        
        # Update merge request
        self.db.table('merge_requests')\
            .update({
                'status': 'merged',
                'merged_by': user_id,
                'merged_at': 'now()'
            })\
            .eq('id', merge_request_id)\
            .execute()
        
        return {"message": "Branches merged successfully"}
    
    async def resolve_conflict(self, conflict_id: int, resolution: ConflictResolution):
        """Resolve a specific conflict by updating target branch pointer"""
        # Get conflict with merge request details
        conflict = self.db.table('merge_conflicts')\
            .select('*, merge_requests!inner(target_branch_id, source_branch_id)')\
            .eq('id', conflict_id)\
            .execute()
        
        if not conflict.data:
            raise HTTPException(status_code=404, detail="Conflict not found")
        
        conflict_data = conflict.data[0]
        target_branch_id = conflict_data['merge_requests']['target_branch_id']
        file_id = conflict_data['file_id']
        
        # Determine which version to use based on strategy
        resolved_version_id = None
        resolved_version_number = None
        
        if resolution.resolution_strategy == "ours":
            # Keep target version (already set in target branch)
            resolved_version_id = conflict_data['target_version_id']
            version = self.db.table('file_versions')\
                .select('version_number')\
                .eq('id', resolved_version_id)\
                .execute()
            resolved_version_number = version.data[0]['version_number'] if version.data else None
            
        elif resolution.resolution_strategy == "theirs":
            # Use source version
            resolved_version_id = conflict_data['source_version_id']
            version = self.db.table('file_versions')\
                .select('version_number')\
                .eq('id', resolved_version_id)\
                .execute()
            resolved_version_number = version.data[0]['version_number'] if version.data else None
            
            # Update target branch pointer to source version
            self.db.table('branch_file_pointers')\
                .update({
                    'version_id': resolved_version_id,
                    'version_number': resolved_version_number
                })\
                .eq('branch_id', target_branch_id)\
                .eq('file_id', file_id)\
                .execute()
            
        elif resolution.resolution_strategy == "manual":
            # Create new version with manually resolved content
            if not resolution.resolved_content:
                raise HTTPException(status_code=400, detail="Resolved content required for manual resolution")
            
            # Get file and create new version
            from api.utils.helpers import calculate_content_hash, calculate_file_size
            import base64
            
            # Decode base64 content
            try:
                resolved_text = base64.b64decode(resolution.resolved_content).decode('utf-8')
            except:
                resolved_text = resolution.resolved_content
            
            # Get current file version to increment
            file = self.db.table('files')\
                .select('current_version')\
                .eq('id', file_id)\
                .execute()
            
            if not file.data:
                raise HTTPException(status_code=404, detail="File not found")
            
            new_version_number = file.data[0]['current_version'] + 1
            
            # Get parent version (target version)
            parent_version_id = conflict_data['target_version_id']
            
            # Get mime type from existing version
            parent_version = self.db.table('file_versions')\
                .select('mime_type')\
                .eq('id', parent_version_id)\
                .execute()
            mime_type = parent_version.data[0]['mime_type'] if parent_version.data else 'text/plain'
            
            # Create new version
            content_hash = calculate_content_hash(resolved_text)
            file_size = calculate_file_size(resolved_text)
            
            version_response = self.db.table('file_versions').insert({
                'file_id': file_id,
                'version_number': new_version_number,
                'parent_version_id': parent_version_id,
                'commit_message': 'Merge conflict resolution (manual)',
                'content_hash': content_hash,
                'file_size': file_size,
                'mime_type': mime_type,
                'is_full_content': True,
                'content_text': resolved_text
            }).execute()
            
            if not version_response.data:
                raise HTTPException(status_code=400, detail="Failed to create resolved version")
            
            resolved_version_id = version_response.data[0]['id']
            resolved_version_number = new_version_number
            
            # Update file current version
            self.db.table('files')\
                .update({'current_version': new_version_number})\
                .eq('id', file_id)\
                .execute()
            
            # Update target branch pointer to new version
            self.db.table('branch_file_pointers')\
                .update({
                    'version_id': resolved_version_id,
                    'version_number': resolved_version_number
                })\
                .eq('branch_id', target_branch_id)\
                .eq('file_id', file_id)\
                .execute()
        
        # Mark conflict as resolved
        self.db.table('merge_conflicts')\
            .update({
                'resolved': True,
                'resolution_strategy': resolution.resolution_strategy,
                'resolved_content': resolution.resolved_content
            })\
            .eq('id', conflict_id)\
            .execute()
        
        return {
            "message": "Conflict resolved",
            "resolved_version_id": resolved_version_id,
            "resolved_version_number": resolved_version_number
        }
    
    async def get_merge_requests(self, repo_id: int, status: str = None):
        """List merge requests"""
        query = self.db.table('merge_requests')\
            .select('*, source_branch:branches!source_branch_id(name), target_branch:branches!target_branch_id(name)')\
            .eq('repository_id', repo_id)
        
        if status:
            query = query.eq('status', status)
        
        response = query.order('created_at', desc=True).execute()
        return response.data
