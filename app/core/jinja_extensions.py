import re
from jinja2 import Environment

def get_jinja_env():
    """
    Returns a Jinja2 Environment. 
    Note: docxtpl tags (tr, tc, p, r) are usually handled by docxtpl's patch_xml.
    If they remain in the XML, it usually means the patch_xml regex missed them.
    We will handle them via pre-processing in our routes.
    """
    return Environment()

def patch_docx_tags(xml_src: str) -> str:
    """
    Manually strip docxtpl prefixes like 'tr ', 'tc ', etc. from jinja tags.
    docxtpl's internal patch_xml can be strict about spaces.
    Example: {% tr for x in y %} -> {% for x in y %}
    
    This improved version also handles moving the tags outside the <w:tr> 
    if the tag is intended for row repetition, preventing alternating empty rows.
    """
    
    def fix_tr_logic(m):
        row_start = m.group(1)
        full_tag = m.group(2)
        delim_start = m.group(3) # {% or {{
        tag_content = m.group(4) # e.g. "for x in y"
        delim_end = m.group(5)   # %} or }}
        row_end = m.group(6)
        
        # Check if row has OTHER meaningful text content besides tags and XML
        # We strip XML tags, Jinja delimiters, and whitespace
        other_content = re.sub(r'({%|{{|%}|}}|<[^>]+>)', '', row_start + row_end).strip()
        
        clean_tag = f"{delim_start} {tag_content} {delim_end}"
        
        if not other_content:
            # Row only contains this tag (and maybe XML noise/whitespace)
            # Replace entire row with the clean tag so it vanishes from layout
            return clean_tag
        else:
            # Row has other content (e.g. {{ item.name }})
            # Wrap the row with the tag
            if any(k in tag_content for k in ['for', 'if']):
                return f"{clean_tag}{row_start}{row_end}"
            elif any(k in tag_content for k in ['endfor', 'endif', 'else']):
                return f"{row_start}{row_end}{clean_tag}"
            else:
                # Fallback: just strip in place
                return f"{row_start}{clean_tag}{row_end}"

    # 1. Handle row-level tags (tr) robustly
    # This pattern allows for XML noise (like <w:rPr>...) between delimiters and 'tr'
    tr_pat = r'(<w:tr[ >](?:(?!<w:tr[ >]).)*?)(({%|{{)\s*(?:<[^>]+>\s*)*tr\s+([^%}]*?)\s*(%}|}}))(.*?</w:tr>)'
    xml_src = re.sub(tr_pat, fix_tr_logic, xml_src, flags=re.DOTALL)

    # 2. Fallback for other tags (tc, p, r) - just strip prefix
    # Broaden to handle XML noise like <w:rPr> between the delimiter and the prefix
    for tag in ['tr', 'tc', 'p', 'r']:
        xml_src = re.sub(r'({%|{{)\s*(?:<[^>]+>\s*)*' + tag + r'\s+', r'\1 ', xml_src)
        
    return xml_src
