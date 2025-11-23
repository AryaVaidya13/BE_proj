# import google.generativeai as genai

# genai.configure(api_key="AIzaSyBOnWJkESNAwFK1QJCZq_kzVM77DMHcwPg")   # replace YOUR_KEY

# models = genai.list_models()

# for m in models:
#     print(m.name, " | supported:", m.supported_generation_methods)

from google import genai

client = genai.Client(api_key="AIzaSyBOnWJkESNAwFK1QJCZq_kzVM77DMHcwPg")

test_models = [
    "models/gemini-2.5-pro",
    "models/gemini-3-pro-preview",
    "models/gemini-2.5-flash"
]

for m in test_models:
    print(f"\n🔍 Testing model: {m}")
    try:
        r = client.models.generate_content(
            model=m,
            contents="Hello! Can you generate a short sentence?"
        )
        print("  ✅ SUCCESS:", r.text[:50], "...")
    except Exception as e:
        print("  ❌ FAIL:", e)
