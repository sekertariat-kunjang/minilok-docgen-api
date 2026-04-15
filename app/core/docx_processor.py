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
from app.generators.pure_flowchart_generator import generate_pure_flowchart_image
from typing import Dict, Any

class DocxProcessor:
    def __init__(self, template_name: str):
        self.template_path = TEMPLATES_DIR / f"{template_name}.docx"
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found")
        self.doc = DocxTemplate(str(self.template_path))
        
        # Monkeypatch patch_xml to be more robust against leftover 'tr ', 'tc ', etc. prefixes
        original_patch_xml = self.doc.patch_xml
        def robust_patch_xml(xml_src: str) -> str:
            # 1. Standard docxtpl patching
            patched_xml = original_patch_xml(xml_src)
            # 2. Our extra robust tag patching
            return patch_docx_tags(patched_xml)
        
        self.doc.patch_xml = robust_patch_xml

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
            judul = table_data.get("nama_sop", merged_data.get("nama_sop", "SOP"))
            style = table_data.get("flowchart_style", "table")
            
            if style == "pure":
                print(f"    [INFO] Using 'pure' visual flowchart style")
                png_bytes = generate_pure_flowchart_image(
                    prosedur_steps=steps,
                    nama_sop=judul
                )
            else:
                print(f"    [INFO] Using 'table' formal SOP style")
                png_bytes = generate_sop_table_image(
                    prosedur_steps=steps,
                    pelaksana_labels=table_data.get("pelaksana_labels", ["Petugas", "Unit Terkait"]),
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
        from docxtpl import RichText
        import re

        list_helpers = {}
        for key, value in list(merged_data.items()):
            target_key = key if key.endswith('_list') else f"{key}_list"
            
            is_array = isinstance(value, list)
            is_multiline = isinstance(value, str) and '\n' in value
            
            # Only format as single-tag RichText if the key explicitely has _ol_ suffix
            # For backward compatibility, fields without _ol_ remain as standard lists for {% tr %} loops
            is_ol_field = "_ol_" in key.lower()
            
            if is_array or is_multiline:
                raw_list = value if is_array else [line.strip() for line in value.split('\n') if line.strip()]
                list_helpers[target_key] = raw_list
                
                # If it's a designated single-tag field, convert array into formatted string with line breaks
                # We intentionally don't use RichText because simple strings joined by \n perfectly 
                # inherit the font, color, and size of the {{ tag }} from the Word template.
                if is_ol_field:
                    formatted_collection = []
                    letters = 'abcdefghijklmnopqrstuvwxyz'
                    dictums = ['KESATU', 'KEDUA', 'KETIGA', 'KEEMPAT', 'KELIMA', 'KEENAM', 'KETUJUH', 'KEDELAPAN', 'KESEMBILAN', 'KESEPULUH']
                    
                    suffix = key.lower().split('_ol_')[-1] if '_ol_' in key.lower() else '1'
                    
                    for i, item in enumerate(raw_list):
                        item_text = item.get('langkah', str(item)) if isinstance(item, dict) else str(item)
                        
                        # Fix stray literal "\n" or actual newlines that shouldn't be inside a single item
                        item_text = item_text.replace('\\n', ' ').replace('\n', ' ')
                        
                        # Clean pre-existing random starting counters from AI or Frontend
                        item_text = re.sub(r'^\d+[\.\)\s]+', '', item_text).strip()
                        item_text = re.sub(r'^[a-z]\s*[\.\)]\s+', '', item_text, flags=re.IGNORECASE).strip()
                        item_text = re.sub(r'^(KESATU|KEDUA|KETIGA|KEEMPAT|KELIMA|KEENAM|KETUJUH)\s*[:\.]\s+', '', item_text, flags=re.IGNORECASE).strip()
                        
                        prefix = ""
                        if suffix == 'a':
                            prefix = f"{letters[i % 26]}. "
                        elif suffix == 'kesatu':
                            idx = i if i < len(dictums) else len(dictums)-1
                            prefix = f"{dictums[idx]}: "
                        else:
                            prefix = f"{i+1}. " # default to 1.
                            
                        formatted_collection.append(f"{prefix}{item_text}")
                    
                    # Join with actual newlines; docxtpl translates \n into internal Word soft breaks
                    merged_data[key] = '\n'.join(formatted_collection)
            
            elif isinstance(value, str):
                list_helpers[target_key] = [value]
                
        merged_data.update(list_helpers)
