import os
import google.generativeai as genai

# قائمة أسماء المفاتيح التي وضعتها في Secrets
key_names = ["GEMINI_KEY_1", "GEMINI_KEY_2", "GEMINI_KEY_3", "GEMINI_KEY_4", "GEMINI_KEY_5"]

print("--- بدء فحص المفاتيح ---")

for name in key_names:
    api_key = os.environ.get(name)

    if not api_key:
        print(f"❌ {name}: غير موجود في Secrets!")
        continue

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        # تجربة بسيطة جداً (أرسل كلمة مرحباً)
        response = model.generate_content("Hi")
        print(f"✅ {name}: يعمل بنجاح!")
    except Exception as e:
        print(f"❌ {name}: لا يعمل. الخطأ: {str(e)}")

print("--- انتهى الفحص ---")