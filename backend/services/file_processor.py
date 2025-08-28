from typing import Dict, Any, Optional
import os
from docx import Document
import PyPDF2
from app_core.llm_client import llm_manager


class FileProcessor:
    def __init__(self):
        self.llm_client = llm_manager.get_client("researcher")
        self.supported_formats = ['.pdf', '.docx', '.txt', '.md']
    
    async def process_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        try:
            # Extract content
            content = await self._extract_content(file_path, original_filename)
            
            # Generate summary
            summary = await self._generate_summary(content, original_filename)
            
            # Create content preview
            preview = content[:500] + "..." if len(content) > 500 else content
            
            return {
                "filename": original_filename,
                "file_path": file_path,
                "content_length": len(content),
                "summary": summary,
                "content_preview": preview,
                "file_type": self._get_file_extension(original_filename)
            }
            
        except Exception as e:
            return {
                "filename": original_filename,
                "file_path": file_path,
                "error": str(e),
                "summary": f"Failed to process file: {str(e)}",
                "content_preview": "",
                "file_type": self._get_file_extension(original_filename)
            }
    
    async def _extract_content(self, file_path: str, filename: str) -> str:
        file_ext = self._get_file_extension(filename).lower()
        
        if file_ext == '.pdf':
            return self._extract_pdf_content(file_path)
        elif file_ext == '.docx':
            return self._extract_docx_content(file_path)
        elif file_ext in ['.txt', '.md']:
            return self._extract_text_content(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _extract_pdf_content(self, file_path: str) -> str:
        content = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text.strip():
                        content.append(f"[Page {page_num}]\n{page_text}")
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
        
        return "\n\n".join(content)
    
    def _extract_docx_content(self, file_path: str) -> str:
        try:
            doc = Document(file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)
            
            return "\n\n".join(content)
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")
    
    def _extract_text_content(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                raise Exception(f"Text extraction failed: {str(e)}")
    
    async def _generate_summary(self, content: str, filename: str) -> str:
        try:
            summary_prompt = f"""Please analyze this document and provide a concise summary.

Document: {filename}
Content length: {len(content)} characters

Content:
{content[:2000]}{"..." if len(content) > 2000 else ""}

Provide:
1. Main topic/purpose (1-2 sentences)
2. Key points or findings (3-5 bullet points)
3. Document type and context
4. Most relevant information for proposal writing

Keep the summary under 200 words and focus on information that would be useful for creating proposals or strategic documents."""
            
            messages = [
                {"role": "system", "content": "You are a document analysis expert. Provide clear, concise summaries that highlight the most important and actionable information."},
                {"role": "user", "content": summary_prompt}
            ]
            
            summary = await self.llm_client.generate(messages)
            return summary
            
        except Exception as e:
            return f"Auto-generated summary unavailable: {str(e)}"
    
    def _get_file_extension(self, filename: str) -> str:
        return os.path.splitext(filename)[1]


# Global file processor instance
_file_processor = None


def get_file_processor() -> FileProcessor:
    global _file_processor
    if _file_processor is None:
        _file_processor = FileProcessor()
    return _file_processor