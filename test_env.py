import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'minilok', '.env')
print(f"Looked at path: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

load_dotenv(dotenv_path=env_path)

print(f"SUMOPOD_API_KEY from os: {os.environ.get('SUMOPOD_API_KEY')}")
print(f"VITE_SUMOPOD_API_KEY from os: {os.environ.get('VITE_SUMOPOD_API_KEY')}")
