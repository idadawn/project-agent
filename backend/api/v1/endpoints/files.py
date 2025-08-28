from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
import os
import aiofiles
from app_core.config import settings
from services.file_processor import FileProcessor, get_file_processor
import uuid

router = APIRouter()


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    file_processor: FileProcessor = Depends(get_file_processor)
):
    try:
        uploaded_files = []
        
        for file in files:
            # Validate file size
            if file.size and file.size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {file.filename} is too large. Maximum size is {settings.MAX_FILE_SIZE} bytes."
                )
            
            # Create unique filename
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
            
            # Ensure upload directory exists
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Process file to extract summary
            file_info = await file_processor.process_file(file_path, file.filename)
            
            uploaded_files.append({
                "file_id": file_id,
                "original_filename": file.filename,
                "stored_filename": unique_filename,
                "file_path": file_path,
                "file_size": len(content),
                "file_type": file.content_type,
                "summary": file_info.get("summary", ""),
                "content_preview": file_info.get("content_preview", "")
            })
        
        return {
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_files():
    try:
        if not os.path.exists(settings.UPLOAD_DIR):
            return {"files": []}
        
        files = []
        for filename in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": stat.st_ctime,
                    "modified_at": stat.st_mtime
                })
        
        return {"files": files}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{file_id}")
async def delete_file(file_id: str):
    try:
        # Find file by ID
        if not os.path.exists(settings.UPLOAD_DIR):
            raise HTTPException(status_code=404, detail="File not found")
        
        for filename in os.listdir(settings.UPLOAD_DIR):
            if filename.startswith(file_id):
                file_path = os.path.join(settings.UPLOAD_DIR, filename)
                os.remove(file_path)
                return {"message": f"File {filename} deleted successfully"}
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    try:
        if not os.path.exists(settings.UPLOAD_DIR):
            raise HTTPException(status_code=404, detail="File not found")
        
        for filename in os.listdir(settings.UPLOAD_DIR):
            if filename.startswith(file_id):
                file_path = os.path.join(settings.UPLOAD_DIR, filename)
                
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
                
                return {
                    "filename": filename,
                    "content": content.decode('utf-8', errors='ignore')
                }
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))