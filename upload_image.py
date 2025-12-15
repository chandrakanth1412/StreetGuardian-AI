import base64
import requests

IMGBB_API_KEY = "2d23aea76d0c6d16d9b4b57347379c2f"

def upload_to_imgbb(image_path: str) -> str:
    """
    Uploads an image to imgbb.com and returns a public URL.
    """

    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read())

    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": IMGBB_API_KEY,
        "image": img_data,
    }

    print("📤 Uploading snapshot to imgbb...")

    try:
        response = requests.post(url, payload)
        result = response.json()

        if result.get("success"):
            image_url = result["data"]["url"]
            print("✅ Uploaded successfully:", image_url)
            return image_url
        else:
            print("❌ imgbb error:", result)
            return ""
    except Exception as e:
        print("❌ Upload failed:", e)
        return ""
