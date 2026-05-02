import google.generativeai as genai

# Paste your API key here
genai.configure(api_key="AIzaSyDZVKYg9J1YMXN8V8d4pTnfvZQOtI-aj6A")

print("Checking available models for your account...")
print("-" * 40)

try:
    for m in genai.list_models():
        # We only want models that can generate text (generateContent)
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error connecting: {e}")