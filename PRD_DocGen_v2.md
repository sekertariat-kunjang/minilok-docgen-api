# Product Requirements Document (PRD): DocGen Stable v2

## 1. Visi & Objektif
**DocGen v2** adalah sistem generator dokumen modular untuk Puskesmas (SK dan SOP). Objektif utamanya adalah **stabilitas format (docx)**, kemudahan bagi user melalui **AI Magic Fill**, dan integrasi **Otomatisasi Tabel Prosedur** yang sesuai dengan standar akreditasi.

## 2. Masalah & Solusi
- **Masalah**: Manipulasi tag Word (`docxtpl`) seringkali rusak jika user tidak hati-hati saat mengedit template (tag terpecah oleh XML Word).
- **Solusi**: Mengimplementasikan **Super Robust Tag Cleaner** yang secara otomatis membersihkan tag yang 'kotor' dan menormalkannya di sisi server sebelum dirender. Mendukung penomoran list otomatis (`_ol_`) untuk menghindari penomoran manual yang membosankan.

## 3. Fitur Inti (Core Features)

### A. Template Management & Dynamic Variables
- **Dynamic Field Injection**: Mendeteksi secara otomatis semua tag Jinja2 `{{ }}` di dalam file Word (Body, Header, Footer).
- **Manual vs AI Fields**: Memisahkan field manual (data profil) dengan field AI (`ai_`) untuk alur kerja yang efisien.

### B. AI "Magic Fill" (Sumopod API)
- **Topik-ke-Draf**: User cukup memasukkan topik (misal: "SOP Penanganan Luka") dan AI akan mengisi semua field `ai_` yang dibutuhkan.
- **Konteks Regulasi**: Mendukung input "Pokok Pikiran Akreditasi" untuk memastikan draf AI 100% selaras dengan standar nasional.

### C. Smart SOP Generators
- **Official Table Style**: Mengonversi JSON prosedur langkah demi langkah menjadi gambar PNG tabel formal Puskesmas dan disisipkan ke placeholder `{{ ai_flowchart }}`.
- **Pure Flowchart**: Mendukung render diagram visual berbasis teks (Mermaid) menggunakan engine Kroki.

### D. Bulk Generation (Mail Merge)
- Memproses ratusan baris data dari Excel/CSV ke dalam ratusan file Word yang terisi data unik, dibungkus secara instan menjadi satu file `.zip`.

## 4. Technical Architecture

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Templating Engine**: `docxtpl` + Kustom Logic Robust Patching.
- **AI Service**: Integrasi Sumopod (OpenAI-compatible) via `httpx`.
- **Image Generation**: `Pillow` (untuk tabel SOP formal) & `Kroki.io` (untuk diagram Mermaid).

### Frontend
- **Embedded Dashboard**: Single-page application (Vanilla HTML/JS/CSS) di folder `static/` yang melayani seluruh siklus hidup pembuatan dokumen.

### Deployment
- **Portabilitas**: Dapat dijalankan di server lokal (Windows/Linux) atau dideploy ke platform cloud seperti Railway/Heroku menggunakan `Procfile` atau `nixpacks.toml`.

## 5. Struktur Direktori
```text
minilok-docgen-api/
├── app/
│   ├── api/          # Endpoints FastAPI (routes.py)
│   ├── core/         # Logika utama (docx_processor, config)
│   ├── generators/   # Generator gambar (SOP Table, Flowchart)
│   ├── models/       # Pydantic schemas
│   └── services/     # Integrasi eksternal (AI Service, Profile Service)
├── static/           # UI Dashboard Terintegrasi
├── templates/        # Penyimpanan file master (.docx)
├── main.py           # Entry point aplikasi
└── requirements.txt  # Python dependencies
```

## 6. Roadmap Masa Depan
- **PDF Conversion**: Implementasi LibreOffice Headless untuk konversi instan DOCX ke PDF.
- **Template Builder**: UI untuk membuat/mengedit template Word langsung di browser.
- **Version Control**: Tracking perubahan pada konten yang di-magic fill oleh AI.
