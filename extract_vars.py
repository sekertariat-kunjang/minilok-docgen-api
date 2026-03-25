import docx
import re

def get_vars(path):
    doc = docx.Document(path)
    # Get XML from document part
    xml = doc._element.xml
    
    # Basic cleaning
    tags = re.findall(r'{{(.*?)}}', xml)
    tags += re.findall(r'{%(.*?)%}', xml)
    
    clean_vars = set()
    for t in tags:
        t = t.strip()
        if not t: continue
        words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', t)
        for w in words:
            if w not in ['for', 'in', 'if', 'else', 'endif', 'endfor', 'loop', 'item', 'tr', 'tc', 'p', 'r']:
                clean_vars.add(w)
    return sorted(list(clean_vars))

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "templates/sk_sample.docx"
    print(",".join(get_vars(path)))
