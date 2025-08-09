import os
from fastapi import APIRouter
from fastapi.responses import FileResponse

# Define the path to your resume
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'static')
RESUME_PATH = os.path.join(STATIC_DIR, 'Fadhil_Ahmad_Hidayat_Resume.pdf')
RESUME_FILENAME = "Fadhil_Ahmad_Hidayat_Resume.pdf"

router = APIRouter()

@router.get("/download")
async def download_resume():
    """
    Provides a direct download link for the resume PDF.
    """
    if not os.path.exists(RESUME_PATH):
        return {"error": "File not found"}, 404
        
    return FileResponse(
        path=RESUME_PATH,
        filename=RESUME_FILENAME,
        media_type='application/pdf'
    )
