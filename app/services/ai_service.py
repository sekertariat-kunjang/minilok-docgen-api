import json
import httpx
from fastapi import HTTPException
from app.models.schemas import AIRequest
from app.core.config import SUMOPOD_API_KEY, SUMOPOD_BASE_URL

async def generate_ai_content(request: AIRequest) -> dict:
    if not SUMOPOD_API_KEY:
        raise HTTPException(status_code=500, detail="SUMOPOD_API_KEY or VITE_SUMOPOD_API_KEY not configured on server")

    context_prompt = f"\n    Konteks/Pokok Pikiran Khusus:\n    {request.context}\n    (Pastikan SOP/dokumen yang Anda buat merujuk dan selaras 100% dengan Pokok Pikiran di atas.)" if request.context else ""

    system_prompt = f"""
    Anda adalah asisten administrasi Puskesmas yang ahli.
    Tugas Anda adalah mengisi field-field berikut berdasarkan instruksi user.
    
    Target Fields: {", ".join(request.fields)}
    
    Metadata: {json.dumps(request.metadata or {{}})}
    {context_prompt}
    
    ATURAN:
    1. Output HARUS dalam format JSON murni.
    2. Isi data sesuai konteks Puskesmas Indonesia dan tata naskah dinas yang berlaku (format PermenpanRB/Akreditasi).
    3. Untuk field 'ai_flowchart', berikan minimal 5-10 langkah kerja yang detail dan berurutan (prosedur) dalam bentuk teks berbaris atau array string. Ini akan digunakan untuk membuat tabel SOP resmi. 
       PENTING: Di akhir SETIAP langkah, tambahkan tag informasi pendukung dalam format: [Waktu: <Estimasi Waktu>] [Output: <Hasil Langkah>] [Syarat: <Dokumen/Persyaratan>]. Contoh: "Petugas mendaftar pasien [Waktu: 5 Menit] [Output: Pasien terdaftar] [Syarat: KTP/BPJS]"
    4. Jabatan pelaksana harus realistis (misal: Petugas Pendaftaran, Dokter, Perawat, Apoteker).
    5. Jangan berikan penjelasan atau teks apapun di luar JSON.
    """

    async with httpx.AsyncClient() as client:
        try:
            print(f"[AI] Calling SUMOPOD at {SUMOPOD_BASE_URL}...")
            response = await client.post(
                f"{SUMOPOD_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {SUMOPOD_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": request.instruction}
                    ],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"}
                },
                timeout=60.0
            )
            print(f"[AI] Response Status: {response.status_code}")
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"AI Provider Error: {response.text}")
            
            resp_data = response.json()
            if "choices" in resp_data and len(resp_data["choices"]) > 0:
                content = resp_data["choices"][0]["message"]["content"]
                try:
                    return json.loads(content)
                except Exception:
                    return {"error": "Failed to parse json content from AI", "raw_content": content}
            
            return resp_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to AI provider: {str(e)}")
