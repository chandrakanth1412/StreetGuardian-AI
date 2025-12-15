import base64
import json
from firebase_admin import messaging, credentials, initialize_app
from upload_image import upload_to_imgbb

cred = credentials.Certificate("serviceAccountKey.json")
initialize_app(cred)

# FCM Topic
TOPIC = "police_zone_a"

def send_emergency(keyword, image_path):
    # Upload image
    image_url = upload_to_imgbb(image_path)

    if not image_url:
        print("❌ No image URL, aborting FCM send.")
        return

    # ---- FIX: High-priority, data-only message ----
    message = messaging.Message(
        topic=TOPIC,
        data={
            "keyword": keyword.upper(),
            "location": "Police Zone A",
            "image": image_url,
            "time": "Now"
        },
        android=messaging.AndroidConfig(
            priority="high",   # 🔥 Forces wake-up even if app is closed
        )
    )

    try:
        response = messaging.send(message)
        print("🚨 Emergency alert sent:", response)
    except Exception as e:
        print("❌ FCM send failed:", e)


# Test send
send_emergency("HELP", "snapshot.jpg")
