# -*- coding: utf-8 -*-
"""
pure_flowchart_generator.py
Generate a visual-only vertical flowchart image using Pillow.
"""

from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- Layout Constants ---
SCALE = 2  # Anti-alias scale factor
FONT_DIR = os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts')

def _load_font(size):
    for name in ['arial.ttf', 'calibri.ttf', 'tahoma.ttf']:
        path = os.path.join(FONT_DIR, name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def _load_bold_font(size):
    for name in ['arialbd.ttf', 'calibrib.ttf', 'tahomabd.ttf']:
        path = os.path.join(FONT_DIR, name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return _load_font(size)

def draw_oval(draw, x0, y0, x1, y1, fill="white", outline="black", width=2):
    draw.ellipse([x0, y0, x1, y1], fill=fill, outline=outline, width=width)

def draw_parallelogram(draw, x0, y0, x1, y1, offset=20, fill="white", outline="black", width=2):
    pts = [
        (x0 + offset, y0),
        (x1, y0),
        (x1 - offset, y1),
        (x0, y1)
    ]
    draw.polygon(pts, fill=fill, outline=outline, width=width)

def draw_rectangle(draw, x0, y0, x1, y1, fill="white", outline="black", width=2):
    draw.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=width)

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = (current_line + " " + word).strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line: lines.append(current_line)
            current_line = word
    if current_line: lines.append(current_line)
    return lines

def generate_pure_flowchart_image(
    prosedur_steps: list,
    nama_sop: str = "SOP"
) -> bytes:
    """
    Generate a vertical flowchart diagram (Black & White).
    """
    n_steps = len(prosedur_steps)
    if n_steps == 0:
        # Return empty small white image
        img = Image.new('RGB', (100, 100), 'white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    # --- Constants ---
    BOX_W = 220
    BOX_H_MIN = 60
    GAP = 40
    PADDING_V = 40
    PADDING_H = 50
    
    # Pre-calculate heights
    fn = _load_font(12 * SCALE)
    fn_bold = _load_bold_font(13 * SCALE)
    
    # Create temp draw to measure text
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    step_data = []
    total_h = PADDING_V * 2
    
    for i, step in enumerate(prosedur_steps):
        text = step.get('langkah', str(step)) if isinstance(step, dict) else str(step)
        wrapped = wrap_text(text, fn, (BOX_W - 30) * SCALE, temp_draw)
        
        line_h = temp_draw.textbbox((0, 0), "Abg", font=fn)[3] - temp_draw.textbbox((0, 0), "Abg", font=fn)[1]
        text_h = len(wrapped) * (line_h + 4)
        
        box_h = max(BOX_H_MIN, (text_h / SCALE) + 20)
        
        step_data.append({
            'text': wrapped,
            'h': box_h,
            'y_start': total_h
        })
        total_h += box_h + GAP
        
    total_h -= GAP # Remove last gap
    total_h += PADDING_V
    
    total_w = BOX_W + PADDING_H * 2
    
    # Create Image
    W, H = int(total_w * SCALE), int(total_h * SCALE)
    img = Image.new('RGB', (W, H), color='white')
    draw = ImageDraw.Draw(img)
    
    CX = W // 2
    BORDER_COLOR = "black"
    FILL_COLOR = "white"
    TEXT_COLOR = "black"
    LINE_WIDTH = max(2, 1 * SCALE)

    for i, data in enumerate(step_data):
        y0 = data['y_start'] * SCALE
        h = data['h'] * SCALE
        y1 = y0 + h
        x0 = CX - (BOX_W * SCALE) // 2
        x1 = CX + (BOX_W * SCALE) // 2
        
        # Draw Shape
        if i == 0 or i == n_steps - 1:
            # Start/End: Oval
            draw_oval(draw, x0, y0, x1, y1, fill=FILL_COLOR, outline=BORDER_COLOR, width=LINE_WIDTH)
        else:
            # Middle: Parallelogram
            draw_parallelogram(draw, x0, y0, x1, y1, offset=15*SCALE, fill=FILL_COLOR, outline=BORDER_COLOR, width=LINE_WIDTH)
            
        # Draw Text
        line_h = draw.textbbox((0, 0), "Abg", font=fn)[3] - draw.textbbox((0, 0), "Abg", font=fn)[1]
        total_text_h = len(data['text']) * (line_h + 4)
        curr_ty = y0 + (h - total_text_h) // 2
        
        for line in data['text']:
            lw = draw.textbbox((0, 0), line, font=fn)[2] - draw.textbbox((0, 0), line, font=fn)[0]
            draw.text((CX - lw // 2, curr_ty), line, font=fn, fill=TEXT_COLOR)
            curr_ty += line_h + 4
            
        # Draw Arrow to next box
        if i < n_steps - 1:
            arrow_y0 = y1
            arrow_y1 = step_data[i+1]['y_start'] * SCALE
            draw.line([(CX, arrow_y0), (CX, arrow_y1)], fill=BORDER_COLOR, width=LINE_WIDTH)
            
            # Arrowhead
            ah = 8 * SCALE
            draw.polygon([
                (CX, arrow_y1),
                (CX - ah // 2, arrow_y1 - ah),
                (CX + ah // 2, arrow_y1 - ah)
            ], fill=BORDER_COLOR)

    # Scale down for anti-aliasing
    final_img = img.resize((int(total_w), int(total_h)), Image.LANCZOS)
    
    buf = io.BytesIO()
    final_img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return buf.read()
