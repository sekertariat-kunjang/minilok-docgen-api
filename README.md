# Minilok Document Generator Service

Service ini digunakan untuk membuat dokumen (.docx) berdasarkan template menggunakan FastAPI dan Python.

## Cara Menjalankan (Lokal)

1.  **Buka Terminal** di folder ini (`c:\Users\star\3D Objects\minlok\docgen-service`).
2.  **Buat Virtual Environment** (Opsional tapi disarankan):
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  **Install Library**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Jalankan Server**:
    ```bash
    python main.py
    ```
    Atau:
    ```bash
    uvicorn main:app --reload
    ```

Server akan jalan di: `http://localhost:8000`

## Cara Penggunaan

Kirim `POST` request ke `/generate-docx` dengan JSON body:

```json
{
  "template_name": "sk_sample",
  "data": {
    "nomor_sk": "123/SK/2024",
    "nama_instansi": "Puskesmas Minilok",
    "tanggal": "26 Februari 2024"
  }
}
```

Pastikan file `sk_sample.docx` ada di dalam folder `templates/`.

## Struktur Folder
- `main.py`: Logic API FastAPI.
- `requirements.txt`: Daftar library yang dibutuhkan.
- `templates/`: Simpan file `.docx` template kamu di sini.
