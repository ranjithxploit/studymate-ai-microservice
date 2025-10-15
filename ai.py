import os
import dotenv
import google.generativeai as genai

dotenv.load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("GEMINI_API_KEY not set. Set it in the environment or a .env file.")
    raise SystemExit(1)

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
resp = model.generate_content("Hello.")
print(getattr(resp, "text", None) or str(resp))