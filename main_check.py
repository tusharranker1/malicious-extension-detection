# main_script.py

import os
import time
import base64
import json
import ctypes
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from plyer import notification
from PIL import Image
from io import BytesIO

# Paths
captured_folder = "captured_images"
decoded_folder = "captured_images_decoded"
model_path = "./models/desktop_screenshot_detector.h5"

# Ensure output folder exists
os.makedirs(decoded_folder, exist_ok=True)

# Load trained model
model = load_model(model_path)

# Label map
label_map = {1: 'Non-Screenshot', 0: 'Desktop Screenshot'}

# Preprocess for model
def preprocess_image(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0
    return img_array

# Predict function
def predict(img_path):
    img_array = preprocess_image(img_path)
    prediction = model.predict(img_array, verbose=0)
    predicted_class = 1 if prediction[0][0] >= 0.5 else 0
    confidence = prediction[0][0] if predicted_class == 1 else 1 - prediction[0][0]
    return label_map[predicted_class], confidence

# Extract Extension ID and (optional) URL from filename
def extract_metadata(filename):
    parts = filename.split('_')
    if len(parts) >= 2:
        ext_id = parts[0]
        return ext_id, "URL Not Available"
    return "Unknown", "Unknown"

# Popup Notification
def show_notification(ext_id, url, confidence):
    message = f"Extension ID: {ext_id}\nDestination URL: {url}\nConfidence: {confidence:.2f}%"
    title = "⚡ Screenshot Detected!"
    
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=5
        )
    except Exception:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)

# Decode JSON file and extract base64 PNG
def decode_json_image(filepath, output_folder):
    try:
        with open(filepath, "r") as file:
            json_data = json.load(file)

        data_url = json_data.get("dataUrl", "")
        if not data_url.startswith("data:image/png;base64,"):
            raise ValueError("Invalid dataUrl format")

        base64_data = data_url.split(",", 1)[1]

        # Fix padding if necessary
        missing_padding = len(base64_data) % 4
        if missing_padding:
            base64_data += '=' * (4 - missing_padding)

        decoded_bytes = base64.b64decode(base64_data)
        img = Image.open(BytesIO(decoded_bytes))

        output_filename = os.path.splitext(os.path.basename(filepath))[0] + ".png"
        output_path = os.path.join(output_folder, output_filename)

        img.save(output_path)
        print(f"✅ Decoded and saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Failed to decode {filepath}: {e}")
        return None

# Watchdog Event Handler
class ImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.png'):
            time.sleep(1)  # Small wait
            filename = os.path.basename(event.src_path)
            print(f"📥 New file detected: {filename}")

            decoded_path = decode_json_image(event.src_path, decoded_folder)

            if decoded_path:
                os.remove(event.src_path)  # Delete original JSON file
                print(f"🗑️ Deleted raw base64 file: {event.src_path}")

                label, confidence = predict(decoded_path)
                print(f"🔎 Prediction: {label} ({confidence * 100:.2f}%)")

                if label == "Desktop Screenshot":
                    ext_id, url = extract_metadata(filename)
                    show_notification(ext_id, url, confidence * 100)

# Main Runner
if __name__ == "__main__":
    observer = Observer()
    event_handler = ImageHandler()
    observer.schedule(event_handler, path=captured_folder, recursive=False)
    observer.start()

    print(f"🚀 Watching '{captured_folder}' for new files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
