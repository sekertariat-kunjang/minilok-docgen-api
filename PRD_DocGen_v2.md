# Product Requirements Document (PRD): DocGen v2 (PDF-First)

## 1. Visi & Objektif
**DocGen v2** adalah pembaruan arsitektur (clean slate) dari sistem generator dokumen Puskesmas (SK dan SOP). Objektif utamanya adalah **menjamin stabilitas absolut (100% robust) pada hasil akhir (output) dokumen**, menghilangkan isu "format rusak" atau "tag tidak terbaca", dan memastikan Tata Naskah Baku Puskesmas terkunci sempurna dalam wujud format **PDF**.

## 2. Masalah Saat Ini (Pain Points di v1)
- **Kerapuhan XML Word**: Penggunaan `docxtpl` untuk memanipulasi file DOCX sangat rentan terhadap *hidden formatting* di Microsoft Word, khususnya pada tag *looping* baris tabel (`{% tr %}`) yang sering digunakan di SK (Mengingat, Menimbang, Memutuskan).
- **Inkonsistensi Output**: File DOCX yang di-download user bisa saja terbuka dengan layout yang bergeser atau rusak di komputer yang berbeda beda versinya.
- **Frustrasi Pengguna**: Pesan error *TemplateSyntaxError* yang rumit menyulitkan user non-teknis.

## 3. Solusi Utama: Arsitektur Hibrida (DOCX to PDF)
User (staf Puskesmas) tetap bisa membuat/mengedit *Template Master* menggunakan Microsoft Word (.docx). Ini mempertahankan kemudahan penggunaan.
Namun, sistem **TIDAK AKAN** merender kembali file .docx kepada user akhir. Sistem akan memproses data ke dalam file DOCX di *background*, lalu secara instan mengonversinya menjadi **PDF Murni** menggunakan *LibreOffice Headless Engine* di server.

## 4. Fitur Inti (Core Features)

### A. Template Management & Health Check
- **Upload Template (.docx)**: Sistem menerima file DOCX.
- **Auto-Healing & Validation**: Sistem secara otomatis membersihkan XML Word dari tag Jinja yang terpecah (*Super Robust Tag Cleaner*). Menolak template jika masih ada error logika Jinja dan menampilkan lokasi error secara presisi.

### B. AI "Magic Fill" (Sumopod API)
- Menggunakan prompt *system* yang spesifik untuk Tata Naskah Hukum (untuk SK) dan Instruksional (untuk SOP).
- Output AI di-parse dari JSON dan langsung dimasukkan ke dalam variabel *Template Master*.

### C. PDF Generation Engine (Core Shift)
- **Single Document**: Menggabungkan data Profil Puskesmas + Input Manual + Hasil AI -> Render via `docxtpl` -> **Convert ke PDF via LibreOffice** -> Return PDF/Streaming Response.
- **Preview UI**: Menampilkan preview PDF secara langsung di browser setelah _generate_.

### D. Bulk Mail Merge (PDF Archive)
- Upload Template + File Excel/CSV berisi ratusan row data.
- Output: File `.zip` berisi ratusan file `.pdf` yang sudah dinamai rapi (contoh: `SOP_Kefarmasian_JohnDoe.pdf`).

## 5. Technical Stack & Infrastructure

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Templating**: `docxtpl` (dengan *Super Robust Tag Cleaner* kustom)
- **PDF Engine**: `subprocess` memanggil `libreoffice --headless --convert-to pdf`
- **AI Integration**: `httpx` / `requests` memanggil Sumopod API.

### Frontend
- **HTML/JS/CSS murni** (Vanilla) atau digabung dalam folder `static/` milik FastAPI.
- Menambahkan PDF.js atau native `<iframe>` untuk menampilkan preview PDF.

### Deployment (Railway)
- **PENTING**: Server Linux di Railway tidak memiliki Microsoft Office atau LibreOffice secara bawaan.
- **Nixpacks**: Wajib menggunakan konfigurasi khusus (misal file [nixpacks.toml](file:///c:/Users/star/3D%20Objects/minilok-docgen-api/nixpacks.toml) atau `Aptfile`) agar Railway meng-install `libreoffice` saat proses *build*.

## 6. Struktur Direktori Baru (Clean Slate Draft)
```text
docgen-v2/
├── app/
│   ├── api/
│   │   └── routes.py         # Endpoints FastAPI
│   ├── core/
│   │   ├── config.py         # Env vars, paths
│   │   ├── template_engine.py# docxtpl + Robust Cleaner
│   │   └── pdf_engine.py     # Wrapper untuk LibreOffice Headless call
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   └── services/
│       └── ai_service.py     # Sumopod logic
├── static/
│   ├── index.html            # UI Baru (PDF Preview)
│   ├── css/
│   └── js/
├── templates/                # Folder penyimpanan .docx master
├── temp_docs/                # Folder sementara untuk konversi PDF (harus auto-clean)
├── main.py                   # FastAPI entry point
├── requirements.txt          # Python deps
└── nixpacks.toml             # Konfigurasi Railway untuk OS dependencies (LibreOffice)
```

## 7. Fase Implementasi (Roadmap)
1. **Fase 1: Setup Infrastructure**: Membuat folder baru, inisialisasi FastAPI dasar, dan yang terpenting: membuktikan konversi DOCX ke PDF berjalan via LibreOffice di Python (secara lokal).
2. **Fase 2: Core Generation**: Memindahkan logika `docxtpl` dan *Robust Cleaner* dari v1. Menguji *parsing* template SK dan SOP ke format PDF.
3. **Fase 3: Frontend & AI**: Membangun UI yang terhubung ke endpoint, integrasi Sumopod, dan PDF Viewer.
4. **Fase 4: Deployment**: Menyiapkan konfigurasi Nixpacks dan men-*deploy* ke Railway. Menguji konversi PDF dalam *high-load* (Bulk).
