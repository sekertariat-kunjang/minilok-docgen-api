from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse
import os
import io
import uuid
import tempfile
import zipfile
import traceback
import pandas as pd
from typing import Dict, Any
import urllib.parse

from app.models.schemas import DocRequest, AIRequest, SOPTableRequest
from app.services.profile_service import get_profile, update_profile, load_profile
from app.services.ai_service import generate_ai_content
from app.core.config import TEMPLATES_DIR
from app.core.docx_processor import DocxProcessor
from app.generators.sop_table_generator import generate_sop_table_image
from docxtpl import DocxTemplate
from app.core.jinja_extensions import patch_docx_tags, get_jinja_env
from jinja2 import meta
import re

router = APIRouter()

@router.get("/")
def root():
    index_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "index.html")
    return FileResponse(index_path)

@router.get("/templates")
def list_templates():
    files = [f.replace('.docx', '') for f in os.listdir(TEMPLATES_DIR) if f.endswith('.docx') and not f.startswith('~')]
    return {"templates": sorted(files)}

@router.post("/upload-template")
async def upload_template(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are allowed")
    
    file_path = TEMPLATES_DIR / file.filename
    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        return {"filename": file.filename, "status": "uploaded", "path": str(file_path)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-docx")
async def generate_docx(request: DocRequest):
    try:
        processor = DocxProcessor(request.template_name)
        
        # Merge Profile Data as base
        merged_data = load_profile()
        merged_data.update(request.data)
        
        target_stream = processor.process_and_render(merged_data)
        
        # Robust Filename: Quote for spaces, add filename* for RFC 5987 compliance
        safe_template_name = request.template_name.replace(' ', '_')
        filename = f"Generated_{safe_template_name}.docx"
        encoded_filename = urllib.parse.quote(filename)
        
        return StreamingResponse(
            target_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
            }
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        with open("error.log", "a") as f:
            f.write(f"\n--- Error ---\n")
            traceback.print_exc(file=f)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-sop-flowchart-image")
async def generate_sop_flowchart(request: SOPTableRequest):
    """
    Generate a formal SOP table PNG image in the official Puskesmas format.
    Returns the PNG as binary stream.
    """
    try:
        png_bytes = generate_sop_table_image(
            prosedur_steps=request.prosedur_steps,
            pelaksana_labels=request.pelaksana_labels,
            nama_sop=request.nama_sop
        )
        return StreamingResponse(
            io.BytesIO(png_bytes), 
            media_type="image/png"
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-ai")
async def generate_ai(request: AIRequest):
    print(f"[AI] Request received for instruction: {request.instruction[:50]}...")
    try:
        result = await generate_ai_content(request)
        print(f"[AI] Request completed successfully.")
        return result
    except Exception as e:
        with open("error.log", "a") as f:
            f.write("\n--- AI Error ---\n")
            traceback.print_exc(file=f)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-bulk")
async def generate_bulk(
    template_name: str = File(...),
    data_file: UploadFile = File(...)
):
    template_path = TEMPLATES_DIR / f"{template_name}.docx"
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
        
    try:
        content = await data_file.read()
        if data_file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error reading data file: {str(e)}")

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "generated_docs.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for index, row in df.iterrows():
                try:
                    processor = DocxProcessor(template_name)
                    
                    row_data = load_profile()
                    row_data.update(row.to_dict())
                    row_data = {k: ("" if pd.isna(v) else v) for k, v in row_data.items()}
                    
                    target_stream = processor.process_and_render(row_data)
                    
                    filename_suggestion = str(row_data.get('nama', row_data.get('nomor', f"doc_{index}")))
                    safe_filename = "".join([c for c in filename_suggestion if c.isalnum() or c in (' ', '.', '_')]).rstrip()
                    doc_filename = f"{safe_filename or f'doc_{index}'}.docx"
                    
                    zipf.writestr(doc_filename, target_stream.read())
                except Exception as e:
                    print(f"Error processing row {index}: {e}")
                    continue

        with open(zip_path, 'rb') as f:
            zip_content = f.read()
            
        # Robust ZIP Filename
        zip_filename = f"Bulk_{template_name}_{uuid.uuid4().hex[:6]}.zip"
        encoded_zip_filename = urllib.parse.quote(zip_filename)
            
        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type="application/x-zip-compressed",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_filename}"; filename*=UTF-8\'\'{encoded_zip_filename}'
            }
        )

@router.get("/get-template-variables/{template_name}")
async def get_template_variables(template_name: str):
    template_path = TEMPLATES_DIR / f"{template_name}.docx"
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        doc = DocxTemplate(str(template_path))
        doc.init_docx() # CRITICAL: Initializes doc.docx
        
        # Consistent variable extraction: use patched XML
        xml = doc.get_xml()
        xml = doc.patch_xml(xml)
        xml = patch_docx_tags(xml) # Extra robust: handles 'tr ' with spaces
        
        # Headers/Footers
        for uri in [doc.HEADER_URI, doc.FOOTER_URI]:
            for relKey, val in doc.docx._part.rels.items():
                if (val.reltype == uri) and (val.target_part.blob):
                    _xml = doc.xml_to_string(re.sub(re.compile(rb'<\?xml.*?\?>', re.S), b'', val.target_part.blob).decode('utf-8'))
                    xml += patch_docx_tags(doc.patch_xml(_xml))

        env = get_jinja_env()
        parse_content = env.parse(xml)
        variables = meta.find_undeclared_variables(parse_content)
        
        return {"variables": sorted(list(variables))}
    except Exception as e:
        with open("error.log", "a") as f:
            f.write("\n--- Variable Extraction Error ---\n")
            traceback.print_exc(file=f)
        return {"variables": [], "error": str(e)}

@router.get("/profile")
def read_profile():
    return get_profile()

@router.post("/profile")
def write_profile(data: Dict[str, Any]):
    return update_profile(data)
