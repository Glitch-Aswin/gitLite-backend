import hashlib
import difflib
from typing import Optional


def calculate_content_hash(content: str | bytes) -> str:
    """Calculate SHA-256 hash of content"""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()


def calculate_file_size(content: str | bytes) -> int:
    """Calculate size of content in bytes"""
    if isinstance(content, str):
        return len(content.encode('utf-8'))
    return len(content)


def generate_diff(content1: Optional[str], content2: Optional[str]) -> str:
    """Generate unified diff between two text contents"""
    if content1 is None:
        content1 = ""
    if content2 is None:
        content2 = ""
    
    lines1 = content1.splitlines(keepends=True)
    lines2 = content2.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        lines1,
        lines2,
        fromfile='version1',
        tofile='version2',
        lineterm=''
    )
    
    return ''.join(diff)


def detect_mime_type(filename: str) -> str:
    """Simple mime type detection based on file extension"""
    extension_map = {
        '.txt': 'text/plain',
        '.py': 'text/x-python',
        '.js': 'text/javascript',
        '.ts': 'text/typescript',
        '.html': 'text/html',
        '.css': 'text/css',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.md': 'text/markdown',
        '.java': 'text/x-java',
        '.cpp': 'text/x-c++',
        '.c': 'text/x-c',
        '.go': 'text/x-go',
        '.rs': 'text/x-rust',
        '.sql': 'application/sql',
        '.sh': 'application/x-sh',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.pdf': 'application/pdf',
        '.zip': 'application/zip',
    }
    
    ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    return extension_map.get(ext, 'application/octet-stream')
