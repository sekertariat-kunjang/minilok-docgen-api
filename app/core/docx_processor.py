import io
import zlib
import base64
import traceback
import httpx
from docxtpl import DocxTemplate, InlineImage
from app.core.jinja_extensions import patch_docx_tags, get_jinja_env
import re
from docx.shared import Mm
from app.core.config import TEMPLATES_DIR
from app.generators.sop_table_generator import generate_sop_table_image
from typing import Dict, Any

class DocxProcessor:
    def __init__(self, template_name: str):
        self.template_path = TEMPLATES_DIR / f"{template_name}.docx"
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found")
        self.doc = DocxTemplate(str(self.template_path))

    def process_and_render(self, merged_data: Dict[str, Any]) -> io.BytesIO:
        # SOP Table Injection
        if "ai_sop_table_data" in merged_data:
            self._inject_sop_table(merged_data)

        # Mermaid Flowchart Injection
        self._inject_mermaid_charts(merged_data)

        # List Helpers
        self._inject_list_helpers(merged_data)

        # Robust tag patching: 
        # We can't easily hook into build_xml without subclassing, 
        # but we can provide a jinja_env and pre-patch the internal XML if needed.
        # Actually, docxtpl 0.20.2 uses patch_xml internally. 
        # To be safe, we'll use a jinja_env from our helper.
        self.doc.render(merged_data, jinja_env=get_jinja_env())
        
        target_stream = io.BytesIO()
        self.doc.save(target_stream)
        target_stream.seek(0)
        return target_stream

    def _inject_sop_table(self, merged_data: Dict[str, Any]):
        print("--- Generating Formal SOP Table ---")
        try:
            table_data = merged_data["ai_sop_table_data"]
            steps = table_data.get("prosedur_steps", [])
            pelaksana = table_data.get("pelaksana_labels", ["Pelaksana 1", "Pelaksana 2"])
            judul = table_data.get("nama_sop", merged_data.get("nama_sop", "SOP"))
            
            png_bytes = generate_sop_table_image(
                prosedur_steps=steps,
                pelaksana_labels=pelaksana,
                nama_sop=judul
            )
            img_stream = io.BytesIO(png_bytes)
            merged_data["ai_flowchart"] = InlineImage(self.doc, image_descriptor=img_stream, width=Mm(170))
            print("    [OK] Formal SOP Table generated and injected into 'ai_flowchart'")
            
            # Generate Audit Table Data
            audit_steps = []
            for i, step in enumerate(steps):
                langkah = step.get("langkah", str(step)) if isinstance(step, dict) else str(step)
                # Ensure it starts with 'Apakah '
                if not langkah.strip().lower().startswith("apakah"):
                    langkah = f"Apakah {langkah[0].lower()}{langkah[1:]}?" if langkah else "Apakah ?"
                audit_steps.append({"no": i + 1, "langkah": langkah})
            
            merged_data["ai_audit_table"] = audit_steps
            print(f"    [OK] Generated {len(audit_steps)} audit steps into 'ai_audit_table'")
        except Exception as e:
            print(f"    [ERROR] Error generating formal SOP table: {e}")
            traceback.print_exc()

    def _inject_mermaid_charts(self, merged_data: Dict[str, Any]):
        MERMAID_INDICATORS = ("graph TD", "graph LR", "graph TB", "graph RL", "flowchart", "sequenceDiagram", "classDiagram", "stateDiagram")
        for key, value in list(merged_data.items()):
            if not isinstance(value, str):
                continue
            stripped = value.strip()
            if stripped.startswith("```"):
                lines = stripped.split('\n')
                inner_lines = lines[1:-1] if lines[-1].strip() == '```' else lines[1:]
                stripped = '\n'.join(inner_lines).strip()
            
            if any(ind in stripped for ind in MERMAID_INDICATORS):
                print(f"--- Processing Flowchart for key='{key}' ---")
                try:
                    compressed = zlib.compress(stripped.encode('utf-8'), 9)
                    encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
                    kroki_url = f"https://kroki.io/mermaid/png/{encoded}"
                    with httpx.Client(timeout=20.0) as client:
                        resp = client.get(kroki_url)
                        if resp.status_code == 200:
                            img_stream = io.BytesIO(resp.content)
                            merged_data[key] = InlineImage(self.doc, image_descriptor=img_stream, width=Mm(150))
                            print(f"    [OK] Injected chart ({len(resp.content)} bytes) for {key}")
                        else:
                            print(f"    [ERROR] Kroki error {resp.status_code}: {resp.text[:200]}")
                            merged_data[key] = "[Flowchart gagal di-render]"
                except Exception as e:
                    print(f"    [ERROR] Error for {key}: {e}")
                    merged_data[key] = "[Flowchart error]"

    def _inject_list_helpers(self, merged_data: Dict[str, Any]):
        list_helpers = {}
        for key, value in merged_data.items():
            target_key = key if key.endswith('_list') else f"{key}_list"
            if isinstance(value, list):
                list_helpers[target_key] = value
            elif isinstance(value, str) and '\n' in value:
                list_helpers[target_key] = [line.strip() for line in value.split('\n') if line.strip()]
            elif isinstance(value, str):
                list_helpers[target_key] = [value]
        merged_data.update(list_helpers)
