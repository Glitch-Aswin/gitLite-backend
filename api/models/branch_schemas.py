from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BranchCreate(BaseModel):
    name: str
    parent_branch_name: Optional[str] = "main"


class BranchResponse(BaseModel):
    id: int
    repository_id: int
    name: str
    parent_branch_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: str
    is_default: bool


class MergeRequestCreate(BaseModel):
    source_branch: str
    target_branch: str
    title: str
    description: Optional[str] = None


class MergeConflictInfo(BaseModel):
    file_id: int
    filename: str
    conflict_type: str
    source_version: int
    target_version: int


class MergeRequestResponse(BaseModel):
    id: int
    repository_id: int
    source_branch_id: int
    target_branch_id: int
    source_branch_name: str
    target_branch_name: str
    title: str
    description: Optional[str]
    status: str
    has_conflicts: bool
    conflicts: List[MergeConflictInfo] = []
    created_at: datetime
    merged_at: Optional[datetime] = None


class ConflictResolution(BaseModel):
    conflict_id: int
    resolution_strategy: str  # "ours", "theirs", "manual"
    resolved_content: Optional[str] = None
