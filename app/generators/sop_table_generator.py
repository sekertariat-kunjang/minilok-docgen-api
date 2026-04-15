# -*- coding: utf-8 -*-
"""
sop_table_generator.py
Generate a formal Indonesian Puskesmas SOP table image using Pillow.

Table structure (matches the official format):
+----+------------------+----------+----------+----------+-------------------+-------+--------+-----+
| No | Uraian Prosedur  | Bidan 1  | Pel. 2   | Pel. 3   | Persyrt/Kelengkpn | Waktu | Output | Ket |
+----+------------------+----------+----------+----------+-------------------+-------+--------+-----+

"""

from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- Layout Constants ---
SCALE = 2  # Anti-alias scale factor

FONT_DIR = os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts')

def _load_font(size):
    """Load Arial if available, fallback to default."""
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


def draw_flowsymbol(draw, symbol_type, cx, cy, w, color_border="#1e40af", color_fill="#dbeafe"):
    """Draw a small flowchart symbol at (cx, cy) center with given width."""
    h = int(w * 0.55)
    x0, y0 = cx - w // 2, cy - h // 2
    x1, y1 = cx + w // 2, cy + h // 2

    if symbol_type == "start_end":
        # Rounded rectangle (stadium/pill)
        r = h // 2
        draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=color_fill, outline=color_border, width=2)

    elif symbol_type == "process":
        # Rectangle
        draw.rectangle([x0, y0, x1, y1], fill=color_fill, outline=color_border, width=2)

    elif symbol_type == "decision":
        # Diamond
        pts = [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]
        draw.polygon(pts, fill="#fef9c3", outline="#ca8a04", width=2)

    elif symbol_type == "arrow_down":
        # Downward arrow line
        mx = cx
        draw.line([(mx, y0 + 4), (mx, y1 - 4)], fill=color_border, width=2)
        # arrowhead
        draw.polygon([(mx, y1), (mx - 6, y1 - 10), (mx + 6, y1 - 10)], fill=color_border)


def generate_sop_table_image(
    prosedur_steps: list,
    pelaksana_labels: list = None,
    nama_sop: str = "SOP",
) -> bytes:
    """
    Generate an SOP table image in the oficial Puskesmas format.

    Args:
        prosedur_steps: list of dicts with keys: langkah (str), waktu (str), output (str), syarat (str)
        pelaksana_labels: list of role names e.g. ['Petugas', 'Dokter', 'Admin']
        nama_sop: title shown above the table

    Returns:
        PNG bytes
    """
    if pelaksana_labels is None:
        pelaksana_labels = ['Pelaksana 1', 'Pelaksana 2']

    n_rows = len(prosedur_steps)
    n_pel = len(pelaksana_labels)

    # --- Column widths (px at SCALE=1) ---
    col_no = 30
    col_uraian = 200
    col_pel = 80        # per pelaksana column
    col_syarat = 130
    col_waktu = 55
    col_output = 90
    col_ket = 45

    total_w = col_no + col_uraian + (col_pel * n_pel) + col_syarat + col_waktu + col_output + col_ket + 2

    row_h_header = 60
    row_h_step = 110

    total_h = 10 + row_h_header + n_rows * row_h_step + 10  # header + rows + padding

    # Scale up for anti-aliasing
    W = total_w * SCALE
    H = total_h * SCALE

    img = Image.new('RGB', (W, H), color='white')
    draw = ImageDraw.Draw(img)

    fn = _load_font(14 * SCALE)
    fn_bold = _load_bold_font(16 * SCALE)
    fn_sm = _load_font(14 * SCALE)
    fn_title = _load_bold_font(14 * SCALE)
    fn_header = _load_bold_font(14 * SCALE)

    BORDER = "black"
    HEADER_BG = "white"
    HEADER_FG = "black"
    CELL_BG = "white"
    ALT_BG = "white"
    FLOW_COLOR = "black"
    FLOW_FILL = "white"

    def sx(v): return v * SCALE
    def sy(v): return v * SCALE

    # --- Compute column X positions ---
    cols = {}
    x = 0
    cols['no'] = x;      x += col_no
    cols['uraian'] = x;  x += col_uraian
    cols['pel'] = []
    for i in range(n_pel):
        cols['pel'].append(x); x += col_pel
    cols['syarat'] = x;  x += col_syarat
    cols['waktu'] = x;   x += col_waktu
    cols['output'] = x;  x += col_output
    cols['ket'] = x;     x += col_ket

    y_header = 10

    def draw_cell_bg(x, y, w, h, bg):
        draw.rectangle([sx(x), sy(y), sx(x + w), sy(y + h)], fill=bg, outline=BORDER, width=SCALE)

    def draw_cell_text(x, y, w, h, text, font=None, fg="black", align="center", valign="center", pad=4):
        if font is None: font = fn_sm
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        # wrap text if too wide
        if tw > sx(w - pad * 2):
            words = text.split()
            lines = []
            cur = ""
            for word in words:
                test = (cur + " " + word).strip()
                bb = draw.textbbox((0, 0), test, font=font)
                if bb[2] - bb[0] > sx(w - pad * 2):
                    if cur: lines.append(cur)
                    cur = word
                else:
                    cur = test
            if cur: lines.append(cur)
            text_rendered = lines
        else:
            text_rendered = [text]

        total_text_h = len(text_rendered) * (th + 2)
        if valign == "center":
            ty = sy(y) + (sy(h) - total_text_h) // 2
        else:
            ty = sy(y) + sy(pad)

        for line in text_rendered:
            bb = draw.textbbox((0, 0), line, font=font)
            lw = bb[2] - bb[0]
            if align == "center":
                tx = sx(x) + (sx(w) - lw) // 2
            elif align == "right":
                tx = sx(x + w) - lw - sx(pad)
            else:
                tx = sx(x) + sx(pad)
            draw.text((tx, ty), line, font=font, fill=fg)
            ty += th + 2

    # --- Draw Header Row ---
    # Merge pelaksana sub-header
    draw_cell_bg(cols['no'], y_header, col_no, row_h_header, HEADER_BG)
    draw_cell_text(cols['no'], y_header, col_no, row_h_header, "No", fn_header, HEADER_FG)

    draw_cell_bg(cols['uraian'], y_header, col_uraian, row_h_header, HEADER_BG)
    draw_cell_text(cols['uraian'], y_header, col_uraian, row_h_header, "Uraian Prosedur", fn_header, HEADER_FG)

    for i, label in enumerate(pelaksana_labels):
        draw_cell_bg(cols['pel'][i], y_header, col_pel, row_h_header, HEADER_BG)
        draw_cell_text(cols['pel'][i], y_header, col_pel, row_h_header, label, fn_header, HEADER_FG)

    draw_cell_bg(cols['syarat'], y_header, col_syarat, row_h_header, HEADER_BG)
    draw_cell_text(cols['syarat'], y_header, col_syarat, row_h_header, "Persyrt/\nKelengkapan", fn_header, HEADER_FG)

    draw_cell_bg(cols['waktu'], y_header, col_waktu, row_h_header, HEADER_BG)
    draw_cell_text(cols['waktu'], y_header, col_waktu, row_h_header, "Waktu", fn_header, HEADER_FG)

    draw_cell_bg(cols['output'], y_header, col_output, row_h_header, HEADER_BG)
    draw_cell_text(cols['output'], y_header, col_output, row_h_header, "Output", fn_header, HEADER_FG)

    draw_cell_bg(cols['ket'], y_header, col_ket, row_h_header, HEADER_BG)
    draw_cell_text(cols['ket'], y_header, col_ket, row_h_header, "Ket", fn_header, HEADER_FG)

    # --- Draw Data Rows ---
    for row_idx, step in enumerate(prosedur_steps):
        y_row = y_header + row_h_header + row_idx * row_h_step
        bg = CELL_BG if row_idx % 2 == 0 else ALT_BG

        langkah = step.get('langkah', step) if isinstance(step, dict) else str(step)
        waktu = step.get('waktu', '-') if isinstance(step, dict) else '-'
        output = step.get('output', '-') if isinstance(step, dict) else '-'
        syarat = step.get('syarat', '-') if isinstance(step, dict) else '-'

        # No.
        draw_cell_bg(cols['no'], y_row, col_no, row_h_step, bg)
        draw_cell_text(cols['no'], y_row, col_no, row_h_step, str(row_idx + 1), fn_bold, "black")

        # Uraian Prosedur
        draw_cell_bg(cols['uraian'], y_row, col_uraian, row_h_step, bg)
        draw_cell_text(cols['uraian'], y_row, col_uraian, row_h_step, langkah, fn_sm, "black", align="left", valign="top")

        # Pelaksana columns (Flowchart symbols in Pelaksana 1)
        for i in range(n_pel):
            draw_cell_bg(cols['pel'][i], y_row, col_pel, row_h_step, bg)
            # Find which column to draw symbol. Default to 0.
            target_col = step.get('pelaksana_index', 0) if isinstance(step, dict) else 0
            
            if i == target_col:
                # Use provided type if available, fallback to positional defaults
                provided_type = step.get('type') if isinstance(step, dict) else None
                if provided_type:
                    sym_type = provided_type
                elif row_idx == 0 or row_idx == n_rows - 1:
                    sym_type = 'start_end'
                else:
                    sym_type = 'process'
                cx = cols['pel'][i] + col_pel // 2
                cy = y_row + row_h_step // 2
                
                # Draw symbol
                draw_flowsymbol(draw, sym_type, sx(cx), sy(cy), sx(col_pel - 20), FLOW_COLOR, FLOW_FILL)
                
                # Draw arrow down to next step if not last
                if row_idx < n_rows - 1:
                    ax = sx(cx)
                    ay_start = sy(cy + 18) # Bottom of symbol
                    ay_end = sy(y_row + row_h_step + 4) # Top of next symbol (roughly)
                    draw.line([(ax, ay_start), (ax, ay_end)], fill=FLOW_COLOR, width=sx(2))
                    # Arrowhead
                    draw.polygon([(ax, ay_end + 4), (ax-sx(4), ay_end-sx(6)), (ax+sx(4), ay_end-sx(6))], fill=FLOW_COLOR)

        # Mutu Baku columns
        draw_cell_bg(cols['syarat'], y_row, col_syarat, row_h_step, bg)
        draw_cell_text(cols['syarat'], y_row, col_syarat, row_h_step, syarat, fn_sm, "black", align="left", valign="top")

        draw_cell_bg(cols['waktu'], y_row, col_waktu, row_h_step, bg)
        draw_cell_text(cols['waktu'], y_row, col_waktu, row_h_step, waktu, fn_sm, "black")

        draw_cell_bg(cols['output'], y_row, col_output, row_h_step, bg)
        draw_cell_text(cols['output'], y_row, col_output, row_h_step, output, fn_sm, "black", align="left", valign="top")

        draw_cell_bg(cols['ket'], y_row, col_ket, row_h_step, bg)
        draw_cell_text(cols['ket'], y_row, col_ket, row_h_step, '-', fn_sm, "black")

    # Scale down for final output (anti-aliasing)
    final_img = img.resize((total_w, total_h), Image.LANCZOS)

    buf = io.BytesIO()
    final_img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return buf.read()


if __name__ == "__main__":
    # Quick test
    steps = [
        {"langkah": "Petugas memanggil pasien sesuai nomor antrian", "waktu": "1 Menit", "output": "Pasien siap", "syarat": "Nomor antrian"},
        {"langkah": "Petugas mengukur suhu tubuh menggunakan termometer digital", "waktu": "2 Menit", "output": "Hasil suhu tercatat", "syarat": "Termometer, APD"},
        {"langkah": "Petugas mencatat hasil pengukuran di rekam medis", "waktu": "1 Menit", "output": "Rekam medis terisi", "syarat": "Rekam medis"},
        {"langkah": "Petugas menginformasikan hasil ke pasien", "waktu": "1 Menit", "output": "Pasien mengetahui hasil", "syarat": "-"},
    ]
    png_bytes = generate_sop_table_image(steps, pelaksana_labels=["Petugas", "Dokter"], nama_sop="SOP Pengecekan Suhu Tubuh Pasien")
    with open("test_sop_table.png", "wb") as f:
        f.write(png_bytes)
    print(f"Generated: test_sop_table.png ({len(png_bytes)} bytes)")
