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


def generate_diff(content1: Optional[str], content2: Optional[str], context_lines: int = 3) -> str:
    """
    Generate enhanced unified diff between two text contents.
    
    Args:
        content1: Original content
        content2: Modified content
        context_lines: Number of context lines around changes (default: 3)
    
    Returns:
        Unified diff string with statistics
    """
    if content1 is None:
        content1 = ""
    if content2 is None:
        content2 = ""
    
    lines1 = content1.splitlines(keepends=True)
    lines2 = content2.splitlines(keepends=True)
    
    # Generate unified diff with context
    diff_lines = list(difflib.unified_diff(
        lines1,
        lines2,
        fromfile='a/file',
        tofile='b/file',
        lineterm='',
        n=context_lines
    ))
    
    if not diff_lines:
        return "No changes detected"
    
    # Calculate statistics
    additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
    
    # Build diff with header
    result = []
    result.append(f"Changes: +{additions} -{deletions}")
    result.append("=" * 50)
    result.extend(diff_lines)
    
    return '\n'.join(result)


def generate_side_by_side_diff(content1: Optional[str], content2: Optional[str]) -> dict:
    """
    Generate side-by-side diff for better visualization.
    
    Returns:
        Dictionary with line-by-line changes and metadata
    """
    if content1 is None:
        content1 = ""
    if content2 is None:
        content2 = ""
    
    lines1 = content1.splitlines()
    lines2 = content2.splitlines()
    
    # Use SequenceMatcher for more detailed comparison
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    
    changes = []
    additions = 0
    deletions = 0
    modifications = 0
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            modifications += (i2 - i1)
            changes.append({
                'type': 'modify',
                'old_lines': lines1[i1:i2],
                'new_lines': lines2[j1:j2],
                'old_line_numbers': list(range(i1 + 1, i2 + 1)),
                'new_line_numbers': list(range(j1 + 1, j2 + 1))
            })
        elif tag == 'delete':
            deletions += (i2 - i1)
            changes.append({
                'type': 'delete',
                'old_lines': lines1[i1:i2],
                'old_line_numbers': list(range(i1 + 1, i2 + 1))
            })
        elif tag == 'insert':
            additions += (j2 - j1)
            changes.append({
                'type': 'insert',
                'new_lines': lines2[j1:j2],
                'new_line_numbers': list(range(j1 + 1, j2 + 1))
            })
        elif tag == 'equal':
            # Include some context lines
            changes.append({
                'type': 'equal',
                'lines': lines1[i1:i2],
                'line_numbers': list(range(i1 + 1, i2 + 1))
            })
    
    return {
        'changes': changes,
        'statistics': {
            'additions': additions,
            'deletions': deletions,
            'modifications': modifications,
            'total_changes': additions + deletions + modifications
        },
        'summary': f"+{additions} -{deletions} ~{modifications}"
    }


def generate_compact_diff(content1: Optional[str], content2: Optional[str]) -> str:
    """
    Generate compact diff showing only changed sections.
    Useful for large files with small changes.
    """
    if content1 is None:
        content1 = ""
    if content2 is None:
        content2 = ""
    
    lines1 = content1.splitlines()
    lines2 = content2.splitlines()
    
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    result = []
    
    additions = 0
    deletions = 0
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue  # Skip unchanged sections
        
        if tag == 'replace':
            result.append(f"@ Line {i1 + 1}-{i2} → {j1 + 1}-{j2}")
            for line in lines1[i1:i2]:
                result.append(f"- {line}")
                deletions += 1
            for line in lines2[j1:j2]:
                result.append(f"+ {line}")
                additions += 1
        elif tag == 'delete':
            result.append(f"@ Line {i1 + 1}-{i2} (deleted)")
            for line in lines1[i1:i2]:
                result.append(f"- {line}")
                deletions += 1
        elif tag == 'insert':
            result.append(f"@ Line {j1 + 1}-{j2} (added)")
            for line in lines2[j1:j2]:
                result.append(f"+ {line}")
                additions += 1
        
        result.append("")  # Empty line between sections
    
    if not result:
        return "No changes detected"
    
    header = f"Summary: +{additions} -{deletions}\n{'=' * 50}\n"
    return header + '\n'.join(result)


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
