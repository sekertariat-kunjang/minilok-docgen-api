import json
from app.core.config import PROFILE_FILE
from typing import Dict, Any

def load_profile() -> Dict[str, Any]:
    if PROFILE_FILE.exists():
        try:
            with open(PROFILE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "nama_puskesmas": "Puskesmas Kunjang",
        "dinas_kesehatan": "Dinas Kesehatan Kabupaten Kediri",
        "pemerintah_daerah": "Pemerintah Kabupaten Kediri"
    }

def save_profile(data: dict):
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_profile():
    return load_profile()

def update_profile(data: Dict[str, Any]):
    profile = load_profile()
    profile.update(data)
    save_profile(profile)
    return profile
