
import os
import google.generativeai as genai
import toml
from PIL import Image
import io

try:
    secrets = toml.load(".streamlit/secrets.toml")
    api_key = secrets["GEMINI_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    exit(1)

model = genai.GenerativeModel('gemini-3-pro-image-preview')
prompt = "Draw a dot."

try:
    response = model.generate_content(prompt)
    part = response.parts[0]
    if hasattr(part, 'inline_data'):
        print(f"Inline Data Found. Mime: {part.inline_data.mime_type}")
        print(f"Data Type: {type(part.inline_data.data)}")
        # Verify we can make an image
        img = Image.open(io.BytesIO(part.inline_data.data))
        print(f"Image created: {img.size}")
except Exception as e:
    print(f"Error: {e}")
