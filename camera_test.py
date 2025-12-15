import cv2

print("Opening camera...")
cap = cv2.VideoCapture(0)


if not cam.isOpened():
    print("❌ ERROR: Cannot access webcam")
else:
    print("Camera opened successfully ✔️")

ret, frame = cam.read()

if ret:
    cv2.imwrite("snapshot.jpg", frame)
    print("📸 Image captured successfully → snapshot.jpg")
else:
    print("❌ ERROR: Failed to capture image")

cam.release()
