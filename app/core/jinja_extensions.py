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
    HEAL AND CLEAN JINJA TAGS IN XML.
    This is a super-robust version that handles split delimiters ({{ ... }} or {% ... %})
    even if Word has inserted XML tags in the middle of them.
    """
    
    # 1. HEAL SPLIT DELIMITERS
    # Example: {<w:rPr>...</w:rPr>{  -> {{
    xml_src = re.sub(r'\{\s*(?:<[^>]+>\s*)*\{', '{{', xml_src)
    xml_src = re.sub(r'\}\s*(?:<[^>]+>\s*)*\}', '}}', xml_src)
    xml_src = re.sub(r'\{\s*(?:<[^>]+>\s*)*%', '{%', xml_src)
    xml_src = re.sub(r'%\s*(?:<[^>]+>\s*)*\}', '%}', xml_src)

    # 2. STRIP XML INSIDE TAGS
    # Find anything between {{ }} or {% %} and remove all <...> tags from it
    def clean_inner_tag(m):
        start, inner, end = m.groups()
        # Remove all XML tags from inner content
        clean_inner = re.sub(r'<[^>]+>', '', inner)
        return f"{start}{clean_inner}{end}"

    xml_src = re.sub(r'(\{\{|\{%)(.*?)(\}\}|%\})', clean_inner_tag, xml_src, flags=re.DOTALL)

    # 3. FIX TR/TC/P/R LOGIC (Simplified and more robust)
    def fix_tr_logic(m):
        row_start = m.group(1) # <w:tr ...>
        full_tag = m.group(2)  # {% tr for ... %}
        delim_start = m.group(3) # {% or {{
        tag_content = m.group(4) # for x in y (already cleaned of tr prefix by re.sub below)
        delim_end = m.group(5)   # %} or }}
        row_end = m.group(6)     # ... </w:tr>
        
        # Strip prefixes from tag_content if they are still there
        clean_content = re.sub(r'^\s*(tr|tc|p|r)\s+', '', tag_content)
        clean_tag = f"{delim_start} {clean_content} {delim_end}"
        
        # Check if row only contains this tag and noise
        other_content = re.sub(r'({%|{{|%}|}}|<[^>]+>|\s)', '', row_start + row_end)
        
        if not other_content:
            return clean_tag # Replace entire row if it's just a loop tag
        else:
            if any(k in clean_content for k in ['for', 'if']):
                return f"{clean_tag}{row_start}{row_end}"
            elif any(k in clean_content for k in ['endfor', 'endif', 'else']):
                return f"{row_start}{row_end}{clean_tag}"
            else:
                return f"{row_start}{clean_tag}{row_end}"

    # Handle 'tr' explicitly for row looping
    tr_pat = r'(<w:tr[ >](?:(?!<w:tr[ >]).)*?)(({%|{{)\s*tr\s+([^%}]*?)\s*(%}|}}))(.*?</w:tr>)'
    xml_src = re.sub(tr_pat, fix_tr_logic, xml_src, flags=re.DOTALL)

    # Global prefix stripping for any remaining tags
    for tag in ['tr', 'tc', 'p', 'r']:
        xml_src = re.sub(r'({%|{{)\s*' + tag + r'\s+', r'\1 ', xml_src)
        
    return xml_src
