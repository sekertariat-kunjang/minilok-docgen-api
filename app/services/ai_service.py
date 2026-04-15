import json
import httpx
from fastapi import HTTPException
from app.models.schemas import AIRequest
from app.core.config import SUMOPOD_API_KEY, SUMOPOD_BASE_URL

async def generate_ai_content(request: AIRequest) -> dict:
    if not SUMOPOD_API_KEY:
        raise HTTPException(status_code=500, detail="SUMOPOD_API_KEY or VITE_SUMOPOD_API_KEY not configured on server")

    context_prompt = f"\n    Konteks/Pokok Pikiran Khusus:\n    {request.context}\n    (Pastikan SOP/dokumen yang Anda buat merujuk dan selaras 100% dengan Pokok Pikiran di atas.)" if request.context else ""

    doc_type = (request.doc_type or "sop").lower()
    persona = "ahli tata naskah regulasi/SK" if doc_type == "sk" else "ahli operasional/SOP"
    
    field_counts_prompt = ""
    if request.field_counts:
        field_counts_prompt = "\n    INSTRUKSI JUMLAH POIN (SANGAT PENTING):\n"
        for field, count in request.field_counts.items():
            field_counts_prompt += f"    - '{field}' WAJIB berisi TEPAT {count} poin/item.\n"

    structure_prompt = ""
    if request.structure:
        structure_prompt = "\n    INSTRUKSI STRUKTUR FLOWCHART (WAJIB DIIKUTI):\n"
        for field, steps in request.structure.items():
            structure_prompt += f"    - Untuk field '{field}', ikuti alur logis berikut ini:\n"
            for step in steps:
                s_type = step.get('type', 'process')
                s_id = step.get('id')
                if s_type == 'decision':
                    label = step.get('label', 'Pertanyaan keputusan')
                    structure_prompt += f"      {s_id}. [KEPUTUSAN: {label}] -> Jika Ya ke {step.get('yes')}, Jika Tidak ke {step.get('no')}\n"
                else:
                    structure_prompt += f"      {s_id}. [PROSES] -> Lanjut ke {step.get('next')}\n"

    system_prompt = f"""
    Anda adalah asisten administrasi Puskesmas yang {persona}.
    Tugas Anda adalah mengisi field-field berikut berdasarkan instruksi user.
    
    Target Fields: {", ".join(request.fields)}
    
    Metadata: {json.dumps(request.metadata or {{}})}
    {context_prompt}
    {field_counts_prompt}
    {structure_prompt}
    
    ATURAN KHUSUS BERDASARKAN DOKUMEN ({doc_type.upper()}):
    1. Output HARUS dalam format JSON murni.
    2. JIKA SK: Gunakan bahasa hukum/regulasi Indonesia yang sangat formal dan hierarkis.
       - 'ai_menimbang': Alasan hukum/pentingnya kebijakan.
       - 'ai_mengingat': Daftar UU/Permenkes (minimal 3-5).
       - 'ai_menetapkan': Diktum keputusan (Kesatu, Kedua, dst).
       - 'ai_lampiran': Isi teks lampiran secara mendetail. Bisa berupa uraian panjang, poin-poin struktur, kualifikasi, atau rincian prosedur operasional yang relevan secara utuh.
    3. JIKA SOP: Gunakan bahasa instruksional yang jelas dan runut.
       - 'ai_flowchart': Minimal 5-10 langkah kerja. 
         Format: "Langkah deskripsi [Waktu: <Estimasi>] [Output: <Hasil>] [Syarat: <Dokumen>]"
    4. PENTING: Untuk field yang merupakan daftar atau poin-poin (misalnya field yang memiliki INSTRUKSI JUMLAH POIN), berikan output sebagai **ARRAY Teks (JSON Array)**.
    5. Untuk field lainnya: Berikan teks narasi yang profesional.
    6. Jangan berikan penjelasan atau teks apapun di luar JSON.
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
