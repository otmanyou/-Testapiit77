from flask import Flask, request, jsonify
import json
import asyncio
from datetime import datetime
import aiohttp
import hmac
import hashlib
import time

app = Flask(__name__)

# بيانات Cloudinary (استبدل هذه القيم بمعلومات حسابك)
CLOUDINARY_CLOUD_NAME = "duu2fy7bq"
CLOUDINARY_API_KEY = "459654532934462"
CLOUDINARY_API_SECRET = "WMWrndmiqcot_20p0rc50odjPTw"

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

# تحديث الملف في Cloudinary باستخدام API REST (غير متزامن)
async def update_file_in_cloudinary(keys):
    # إنشاء توقيع للرفع المُوقع
    timestamp = int(time.time())
    public_id = "keys/ky.txt"
    params = {
        "timestamp": timestamp,
        "public_id": public_id,
        "overwrite": True,
        "resource_type": "raw",
    }

    # ترتيب المفاتيح أبجديًا (مطلوب لتوقيع Cloudinary)
    sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    signature = hmac.new(
        CLOUDINARY_API_SECRET.encode("utf-8"),
        f"{sorted_params}{CLOUDINARY_API_SECRET}".encode("utf-8"),
        hashlib.sha1
    ).hexdigest()

    # إضافة التوقيع إلى البيانات
    params["api_key"] = CLOUDINARY_API_KEY
    params["signature"] = signature
    params["file"] = json.dumps(keys)

    upload_url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/raw/upload"

    async with aiohttp.ClientSession() as session:
        async with session.post(upload_url, data=params) as response:
            print(f"Response Status: {response.status}")
            print(f"Response Body: {await response.text()}")
            if response.status != 200:
                raise Exception(f"Failed to update file in Cloudinary: {await response.text()}")

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

        expiry_time = datetime.strptime(key_data["expiry"], "%Y-%m-%d %H:%M:%S")
        print(f"Expiry Time: {expiry_time}, Current Time: {datetime.now()}")

        if datetime.now() > expiry_time:
            print("Key has expired.")
            del keys[key]
            await update_file_in_cloudinary(keys)
            return False

        if len(key_data["used_by"]) >= key_data["limit"]:
            print("Key usage limit reached.")
            return False

        # تحديث قائمة المستخدمين الذين استخدموا المفتاح
        key_data["used_by"].append("anonymous")  # إضافة مستخدم مجهول
        keys[key] = key_data
        await update_file_in_cloudinary(keys)

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

# تشغيل التطبيق (فقط عند التشغيل محليًا)
if __name__ == "__main__":
    # استخدام asyncio لتشغيل التطبيق بشكل غير متزامن
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run(debug=True))
