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
    """
    for tag in ['tr', 'tc', 'p', 'r']:
        # Match {% tr ... %} or {{ tr ... }} with flexible spacing
        xml_src = re.sub(r'({%|{{)\s*' + tag + r'\s+', r'\1 ', xml_src)
    return xml_src
