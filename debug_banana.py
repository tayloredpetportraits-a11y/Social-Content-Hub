
import os
import google.generativeai as genai
import toml

# Load secrets
try:
    secrets = toml.load(".streamlit/secrets.toml")
    api_key = secrets["GEMINI_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error loading secrets: {e}")
    exit(1)

model = genai.GenerativeModel('gemini-3-pro-image-preview')
prompt = "Draw a cute dog."

print("Generating...")
try:
    response = model.generate_content(prompt)
    print("Response Parts:", response.parts)
    print("Part 0 dir:", dir(response.parts[0]))
    # Try different accessors if possible
except Exception as e:
    print(f"Error: {e}")
