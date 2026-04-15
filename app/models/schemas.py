from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class DocRequest(BaseModel):
    template_name: str
    data: Dict[str, Any]

class AIRequest(BaseModel):
    instruction: str
    fields: List[str]
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[str] = None
    doc_type: Optional[str] = "sop" # 'sop' or 'sk'
    field_counts: Optional[Dict[str, int]] = None
    structure: Optional[Dict[str, Any]] = None

class SOPTableRequest(BaseModel):
    prosedur_steps: List[Any]
    pelaksana_labels: List[str] = ["Pelaksana 1", "Pelaksana 2"]
    nama_sop: str = "SOP"
    flowchart_style: Optional[str] = "table" # 'table' or 'pure'
