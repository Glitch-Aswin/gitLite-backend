from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ========================
# REPOSITORY MODELS
# ========================
class RepositoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RepositoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RepositoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: str
    created_at: datetime
    updated_at: datetime


# ========================
# FILE MODELS
# ========================
class FileCreate(BaseModel):
    filename: str
    content_text: Optional[str] = None
    content_binary: Optional[bytes] = None
    commit_message: Optional[str] = None
    mime_type: Optional[str] = "text/plain"


class FileUpdate(BaseModel):
    content_text: Optional[str] = None
    content_binary: Optional[bytes] = None
    commit_message: str


class FileResponse(BaseModel):
    id: int
    repository_id: int
    filename: str
    created_at: datetime
    updated_at: datetime
    current_version: int


class FileDetailResponse(FileResponse):
    content_text: Optional[str] = None
    content_binary: Optional[bytes] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


# ========================
# FILE VERSION MODELS
# ========================
class FileVersionResponse(BaseModel):
    id: int
    file_id: int
    version_number: int
    parent_version_id: Optional[int]
    created_at: datetime
    commit_message: Optional[str]
    content_hash: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]


class FileVersionDetailResponse(FileVersionResponse):
    content_text: Optional[str] = None
    content_binary: Optional[bytes] = None


class FileDiffResponse(BaseModel):
    file_id: int
    filename: str
    version1: int
    version2: int
    diff: str


# ========================
# REPOSITORY STATS MODELS
# ========================
class RepositoryStats(BaseModel):
    total_files: int
    total_size: int
    total_versions: int
    last_activity: Optional[datetime]


class ActivityItem(BaseModel):
    file_id: int
    filename: str
    version_number: int
    commit_message: Optional[str]
    created_at: datetime


class CompareRequest(BaseModel):
    state1_date: datetime
    state2_date: datetime
