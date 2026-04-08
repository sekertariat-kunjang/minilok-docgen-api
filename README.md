# Minilok DocGen API Service

Service ini digunakan untuk membuat dokumen (.docx) berbasis template secara dinamis menggunakan FastAPI, Python, dan integrasi AI (Sumopod). Dirancang khusus untuk mempermudah pembuatan SK dan SOP di Puskesmas dengan stabilitas format yang tinggi.

## 🚀 Fitur Utama

- **Dynamic Template Rendering**: Menggunakan `docxtpl` (Jinja2) untuk mengisi placeholder di file Word (.docx).
- **AI Magic Fill**: Otomatisasi pengisian draf dokumen menggunakan AI (Sumopod API).
- **Official SOP Table Generator**: Otomatis membuat tabel prosedur resmi (PNG) dan menyisipkannya ke dalam dokumen.
- **Pure Flowchart Generator**: Membuat diagram alir visual sederhana menggunakan Mermaid & Kroki.
- **Bulk Mail Merge**: Generate ratusan dokumen sekaligus dari file Excel/CSV dalam bentuk ZIP.
- **Smart Tagging**: Fitur penomoran otomatis (KESATU, 1., a.) cukup dengan satu tag di Word.
- **Dynamic Variable Detection**: API untuk mendeteksi variabel apa saja yang ada di dalam template secara otomatis.
- **Profile Management**: Menyimpan data identitas Puskesmas agar tidak perlu diinput berulang kali.

## 🛠️ Cara Menjalankan (Lokal)

1.  **Persiapan**: Pastikan Python 3.10+ sudah terinstal.
2.  **Clone & Masuk ke Folder**:
    ```bash
    cd minilok-docgen-api
    ```
3.  **Virtual Environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Konfigurasi .env**: Pastikan file `.env` berisi API Key Sumopod:
    ```env
    SUMOPOD_API_KEY=your_key_here
    SUMOPOD_BASE_URL=https://ai.sumopod.com/v1
    ```
6.  **Jalankan Server**:
    ```bash
    python main.py
    ```
    Server akan aktif di: `http://localhost:8000`

## 📝 Aturan Penamaan Tag (Template)

Aplikasi ini memiliki kecerdasan buatan dalam memproses tag di dalam Word:

| Pola Tag | Fungsi | Deskripsi |
| :--- | :--- | :--- |
| `{{ variabel }}` | **Manual/Profil** | Diisi dari data manual atau profil Puskesmas. |
| `{{ ai_nama_tag }}` | **AI Magic** | Field yang akan otomatis dicarikan draf isinya oleh AI. |
| `{{ ai_flowchart }}` | **SOP Table** | Wadah otomatis untuk tabel prosedur formal/diagram alir. |
| `{{ tag_ol_1 }}` | **Auto-Number** | Otomatis membuat list angka (1. 2. 3.) dari satu baris tag. |
| `{{ tag_ol_a }}` | **Auto-Letter** | Otomatis membuat list huruf (a. b. c.) dari satu baris tag. |
| `{{ tag_ol_kesatu }}` | **Auto-Dictum** | Otomatis membuat list diktum (KESATU: KEDUA:) untuk SK. |

## 📡 API Reference

### 1. Generate Document
`POST /generate-docx`
Menerima JSON data variabel dan merender file .docx.

### 2. AI Magic Fill
`POST /generate-ai`
Menerima instruksi (topik) dan konteks, mengembalikan draf JSON untuk mengisi field `ai_`.

### 3. Bulk Generation
`POST /generate-bulk`
Menerima file `.docx` dan `.xlsx/.csv`, mengembalikan `.zip` berisi dokumen yang sudah diproses per baris data.

### 4. Get Variables
`GET /get-template-variables/{template_name}`
Mendeteksi semua tag `{{ }}` dan `{% %}` di dalam template, termasuk yang ada di Header & Footer.

---
## 📂 Struktur Folder
- `app/`: Logika inti aplikasi (API, Core, Services, Generators).
- `static/`: Dashboard UI berbasis web untuk pengoperasian user.
- `templates/`: Folder penyimpanan file master `.docx`.
- `main.py`: Entry point aplikasi.

