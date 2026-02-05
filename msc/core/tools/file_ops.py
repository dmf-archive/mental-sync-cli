import os
from typing import Any
from pydantic import BaseModel, Field
from msc.core.tools.base import BaseTool

class WriteFileArgs(BaseModel):
    path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")

class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Atomically write content to a file. Directories will be created if they don't exist."
    args_schema = WriteFileArgs

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        path: str = kwargs["path"]
        content: str = kwargs["content"]
        
        abs_path = os.path.normpath(os.path.abspath(os.path.join(self.context.workspace_root, path)))
        
        if not any(abs_path.lower().startswith(os.path.normpath(p).lower()) for p in self.context.allowed_paths):
            return {"status": "error", "message": f"Access denied: {path} is outside allowed paths."}

        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "path": path, "bytes": len(content)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class ApplyDiffArgs(BaseModel):
    path: str = Field(..., description="Path to the file to modify")
    diff: str = Field(..., description="SEARCH/REPLACE block")

class ApplyDiffTool(BaseTool):
    name = "apply_diff"
    description = "Apply precise modifications to a file using SEARCH/REPLACE blocks."
    args_schema = ApplyDiffArgs

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        path: str = kwargs["path"]
        diff_str: str = kwargs["diff"]
        
        abs_path = os.path.normpath(os.path.abspath(os.path.join(self.context.workspace_root, path)))
        
        if not any(abs_path.lower().startswith(os.path.normpath(p).lower()) for p in self.context.allowed_paths):
            return {"status": "error", "message": f"Access denied: {path} is outside allowed paths."}

        if not os.path.exists(abs_path):
            return {"status": "error", "message": f"File not found: {path}"}

        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()

            import re
            # 增强的正则解析，支持可选的行号和分隔符
            pattern = r"<<<<<<< SEARCH\s*(?::start_line:\d+\s*)?(?:-+\s*)?(.*?)\s*=======\s*(.*?)\s*>>>>>>> REPLACE"
            matches = re.findall(pattern, diff_str, re.DOTALL)
            
            if not matches:
                return {"status": "error", "message": "Invalid diff format. Expected <<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE"}

            new_content = content
            for search_block, replace_block in matches:
                search_block = search_block.strip()
                replace_block = replace_block.strip()
                
                if search_block in new_content:
                    new_content = new_content.replace(search_block, replace_block)
                else:
                    return {"status": "error", "message": f"Search block not found in file: {search_block[:50]}..."}

            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return {"status": "success", "path": path}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class ListFilesArgs(BaseModel):
    path: str = Field(".", description="Directory path to list")
    recursive: bool = Field(False, description="Whether to list files recursively")

class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List files and directories in a structured format."
    args_schema = ListFilesArgs

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        path: str = kwargs.get("path", ".")
        recursive: bool = kwargs.get("recursive", False)
        
        abs_path = os.path.normpath(os.path.abspath(os.path.join(self.context.workspace_root, path)))
        
        if not any(abs_path.lower().startswith(os.path.normpath(p).lower()) for p in self.context.allowed_paths):
            return {"status": "error", "message": f"Access denied: {path} is outside allowed paths."}

        if not os.path.isdir(abs_path):
            return {"status": "error", "message": f"Not a directory: {path}"}

        files = []
        try:
            if recursive:
                for root, dirs, filenames in os.walk(abs_path):
                    rel_root = os.path.relpath(root, abs_path)
                    if rel_root == ".": rel_root = ""
                    for d in dirs:
                        files.append(os.path.join(rel_root, d) + "/")
                    for f in filenames:
                        files.append(os.path.join(rel_root, f))
            else:
                for item in os.listdir(abs_path):
                    if os.path.isdir(os.path.join(abs_path, item)):
                        files.append(item + "/")
                    else:
                        files.append(item)
            return {"status": "success", "path": path, "files": sorted(files)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
