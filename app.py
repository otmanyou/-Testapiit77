from flask import Flask, request, jsonify
import json
import asyncio
from datetime import datetime
import aiohttp

app = Flask(__name__)

# بيانات Cloudinary (استبدل هذه القيم بمعلومات حسابك)
CLOUDINARY_CLOUD_NAME = "duu2fy7bq"

# تنزيل الملف من Cloudinary (غير متزامن)
async def download_file_from_cloudinary():
    url = f"https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/raw/upload/v1/keys/ky.txt"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                file_content = await response.text()
                print("Downloaded File Content:", file_content)
                return json.loads(file_content)
            else:
                raise Exception("Failed to download file from Cloudinary")

# التحقق من صلاحية الأكواد (غير متزامن)
async def is_valid_key(key):
    try:
        keys = await download_file_from_cloudinary()

        key_data = keys.get(key)
        print(f"Checking key: {key}")
        print(f"Key Data: {key_data}")

        if not key_data:
            print("Key not found in the file.")
            return False

        # التحقق من تاريخ انتهاء الصلاحية
        expiry_time = datetime.strptime(key_data["expiry"], "%Y-%m-%d %H:%M:%S")
        print(f"Expiry Time: {expiry_time}, Current Time: {datetime.now()}")

        if datetime.now() > expiry_time:
            print("Key has expired.")
            return False

        # التحقق من عدد الاستخدامات
        if len(key_data["used_by"]) >= key_data["limit"]:
            print("Key usage limit reached.")
            return False

        print("Key is valid.")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# نقطة النهاية للتحقق من المفتاح (غير متزامن)
@app.route('/cod', methods=['GET'])
async def check_code():
    code = request.args.get('code')

    if not code:
        return jsonify({"valid": False, "message": "يرجى تقديم الكود."}), 400

    valid = await is_valid_key(code)
    return jsonify({"valid": valid})

# تشغيل التطبيق
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    app.run(debug=True, use_reloader=False)
