"""
File system tools with security policies enforced
"""
import os
import shutil
import pathlib
from typing import Dict, Any, List, Optional
from send2trash import send2trash

from autonomous_config import is_write_path_allowed
from utils.format import format_file_info, format_directory_listing
from utils.paths import resolve_path, get_safe_path


async def handle_read(file_path: str) -> Dict[str, Any]:
    """Read file contents"""
    try:
        resolved_path = resolve_path(file_path)
        if not resolved_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        if resolved_path.is_dir():
            return {"success": False, "error": f"Path is a directory: {file_path}"}
            
        content = resolved_path.read_text(encoding='utf-8')
        return {
            "success": True,
            "content": content,
            "file_path": str(resolved_path),
            "size": len(content)
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to read file: {str(e)}"}


async def handle_write(file_path: str, content: str) -> Dict[str, Any]:
    """Write content to file with security policy enforcement"""
    try:
        resolved_path = resolve_path(file_path)
        
        # 🚨 ENFORCE SECURITY POLICY
        if not is_write_path_allowed(str(resolved_path)):
            return {
                "success": False, 
                "error": f"🚫 Caminho não permitido pela política de segurança: {file_path}"
            }
        
        # Create parent directories if needed
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        resolved_path.write_text(content, encoding='utf-8')
        
        return {
            "success": True,
            "file_path": str(resolved_path),
            "bytes_written": len(content.encode('utf-8')),
            "message": f"✅ Arquivo gravado com sucesso: {file_path}"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to write file: {str(e)}"}


async def handle_list(directory_path: str = ".") -> Dict[str, Any]:
    """List directory contents"""
    try:
        resolved_path = resolve_path(directory_path)
        if not resolved_path.exists():
            return {"success": False, "error": f"Directory not found: {directory_path}"}
        
        if not resolved_path.is_dir():
            return {"success": False, "error": f"Path is not a directory: {directory_path}"}
        
        items = []
        for item in resolved_path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
                "modified": item.stat().st_mtime
            })
        
        return {
            "success": True,
            "directory": str(resolved_path),
            "items": items,
            "total_items": len(items)
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to list directory: {str(e)}"}


async def handle_copy(source_path: str, dest_path: str) -> Dict[str, Any]:
    """Copy file or directory with security policy enforcement"""
    try:
        source = resolve_path(source_path)
        dest = resolve_path(dest_path)
        
        if not source.exists():
            return {"success": False, "error": f"Source not found: {source_path}"}
        
        # 🚨 ENFORCE SECURITY POLICY FOR DESTINATION
        if not is_write_path_allowed(str(dest)):
            return {
                "success": False,
                "error": f"🚫 Destino não permitido pela política: {dest_path}"
            }
        
        # Create parent directories if needed
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        if source.is_file():
            shutil.copy2(source, dest)
            operation = "File copied"
        else:
            shutil.copytree(source, dest, dirs_exist_ok=True)
            operation = "Directory copied"
        
        return {
            "success": True,
            "source": str(source),
            "destination": str(dest),
            "operation": operation,
            "message": f"✅ {operation}: {source_path} → {dest_path}"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to copy: {str(e)}"}


async def handle_move(source_path: str, dest_path: str) -> Dict[str, Any]:
    """Move file or directory with security policy enforcement"""
    try:
        source = resolve_path(source_path)
        dest = resolve_path(dest_path)
        
        if not source.exists():
            return {"success": False, "error": f"Source not found: {source_path}"}
        
        # 🚨 ENFORCE SECURITY POLICY FOR DESTINATION
        if not is_write_path_allowed(str(dest)):
            return {
                "success": False,
                "error": f"🚫 Destino não permitido pela política: {dest_path}"
            }
        
        # Create parent directories if needed
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(source), str(dest))
        
        return {
            "success": True,
            "source": str(source),
            "destination": str(dest),
            "message": f"✅ Movido: {source_path} → {dest_path}"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to move: {str(e)}"}


async def handle_delete(file_path: str, mode: str = "trash") -> Dict[str, Any]:
    """Delete file or directory (trash or hard delete)"""
    try:
        resolved_path = resolve_path(file_path)
        
        if not resolved_path.exists():
            return {"success": False, "error": f"Path not found: {file_path}"}
        
        if mode == "trash":
            send2trash(str(resolved_path))
            message = f"🗑️ Movido para lixeira: {file_path}"
        elif mode == "hard":
            if resolved_path.is_file():
                resolved_path.unlink()
                message = f"💥 Arquivo deletado permanentemente: {file_path}"
            else:
                shutil.rmtree(resolved_path)
                message = f"💥 Diretório deletado permanentemente: {file_path}"
        else:
            return {"success": False, "error": f"Invalid delete mode: {mode}"}
        
        return {
            "success": True,
            "path": str(resolved_path),
            "mode": mode,
            "message": message
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to delete: {str(e)}"}


async def handle_find(pattern: str, directory: str = ".", max_results: int = 100) -> Dict[str, Any]:
    """Find files matching pattern"""
    try:
        resolved_dir = resolve_path(directory)
        if not resolved_dir.exists() or not resolved_dir.is_dir():
            return {"success": False, "error": f"Invalid directory: {directory}"}
        
        matches = []
        for path in resolved_dir.rglob(pattern):
            if len(matches) >= max_results:
                break
            matches.append({
                "path": str(path.relative_to(resolved_dir)),
                "full_path": str(path),
                "type": "directory" if path.is_dir() else "file",
                "size": path.stat().st_size if path.is_file() else None
            })
        
        return {
            "success": True,
            "pattern": pattern,
            "directory": str(resolved_dir),
            "matches": matches,
            "total_found": len(matches),
            "truncated": len(matches) >= max_results
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to find files: {str(e)}"}