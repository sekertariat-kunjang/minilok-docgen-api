import os
import sys
from pathlib import Path

# Add current dir to path to import app modules
sys.path.append(os.getcwd())

from app.core.docx_processor import DocxProcessor
from app.core.jinja_extensions import patch_docx_tags, get_jinja_env
from jinja2 import meta

TEMPLATES_DIR = Path("templates")

def scan_templates():
    print(f"Scanning templates in {TEMPLATES_DIR.absolute()}...")
    templates = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".docx") and not f.startswith("~")]
    
    for t_name in templates:
        print(f"\n--- Checking: {t_name} ---")
        try:
            name_no_ext = t_name.replace(".docx", "")
            processor = DocxProcessor(name_no_ext)
            
            # 1. Check raw XML for problematic tags
            doc = processor.doc
            # Force initialization if needed
            if not hasattr(doc, 'docx') or doc.docx is None:
                from docx import Document
                doc.docx = Document(str(processor.template_path))
            
            xml = doc.get_xml()
            
            # Check for split tags (e.g. { % tr )
            if "{ %" in xml or "{{ " in xml or " }} " in xml:
                print("  [WARN] Potential split/spaced Jinja delimiters found.")
            
            # 2. Check how our patcher handles it
            patched_xml = patch_docx_tags(xml)
            
            # 3. Try to parse with Jinja
            env = get_jinja_env()
            try:
                parsed_content = env.parse(patched_xml)
                vars = meta.find_undeclared_variables(parsed_content)
                print(f"  [OK] Jinja Parse successful. Variables: {sorted(list(vars))}")
            except Exception as je:
                print(f"  [ERROR] Jinja Parse FAILED: {je}")
                # Try to find the context of the error
                error_lines = str(je).split('\n')
                print(f"    Detail: {error_lines[0]}")
                
        except Exception as e:
            print(f"  [CRITICAL] Processor failed initialization: {e}")

if __name__ == "__main__":
    scan_templates()
