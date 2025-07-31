from mitmproxy import http
import hashlib
import os
import re
import datetime
import joblib
import pandas as pd
import time
from plyer import notification

# === CACHES & CONSTANTS ===
image_cache = {}
keylog_cache = {}
request_timestamps = {}

# === MODEL LOADING ===
keylog_model = joblib.load("./models/keylogger_model.pkl")

# === IMAGE SIGNATURES ===
IMAGE_SIGNATURES = {
    "JPEG": b"\xFF\xD8\xFF",
    "PNG": b"\x89PNG\r\n\x1a\n",
    "GIF": b"GIF8",
    "BMP": b"BM",
    "WEBP": b"RIFF"
}
DATA_URI_REGEX = re.compile(r"data:image/(png|jpeg|jpg|gif|webp);base64,", re.I)

# === SAVE PATHS ===
SAVE_DIR_IMAGES = "captured_images"
SAVE_DIR_KEYS = "suspected_keys"
os.makedirs(SAVE_DIR_IMAGES, exist_ok=True)
os.makedirs(SAVE_DIR_KEYS, exist_ok=True)

# === UTILS ===
def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

def is_image_payload(content_type, raw):
    content_type = content_type.lower()
    if content_type.startswith("image/"):
        return True
    if "multipart/form-data" in content_type and b"Content-Type: image/" in raw:
        return True
    if DATA_URI_REGEX.search(raw.decode(errors="ignore")):
        return True
    for sig in IMAGE_SIGNATURES.values():
        if raw.startswith(sig):
            return True
    return False

def is_ascii(data):
    try:
        data.decode('ascii')
        return True
    except UnicodeDecodeError:
        return False

def hash_image(raw: bytes) -> str:
    return hashlib.sha1(raw).hexdigest()

def extract_features(flow, request_frequency):
    request = flow.request
    payload_size = len(request.raw_content or b"")
    content_type = request.headers.get("Content-Type", "")
    host = request.host
    method = request.method
    path = request.path

    return pd.DataFrame([{
        "method": method,
        "content_type": content_type,
        "payload_size": payload_size,
        "host": host,
        "path": path,
        "request_frequency": request_frequency
    }])

# === MAIN HOOK ===
def request(flow: http.HTTPFlow) -> None:
    headers = flow.request.headers
    origin = headers.get("Origin", "")
    referer = headers.get("Referer", "")
    method = flow.request.method
    host = flow.request.host
    raw = flow.request.raw_content or b""

    # === TRACK REQUEST FREQUENCY ===
    now = time.time()
    request_timestamps.setdefault(host, []).append(now)
    request_timestamps[host] = [t for t in request_timestamps[host] if now - t < 10]
    request_frequency = len(request_timestamps[host])

    # === IMAGE DETECTION ===
    if origin.startswith("chrome-extension://") or referer.startswith("chrome-extension://"):
        ext_id = origin.split("://")[1].split("/")[0] if origin else referer.split("://")[1].split("/")[0]
        url = flow.request.pretty_url
        content_type = headers.get("Content-Type", "")

        if method in ["POST", "PUT"] and is_image_payload(content_type, raw):
            img_hash = hash_image(raw)
            cache_key = (ext_id, url)

            if image_cache.get(cache_key) != img_hash:
                image_cache[cache_key] = img_hash

                safe_ext_id = sanitize_filename(ext_id)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(SAVE_DIR_IMAGES, f"{safe_ext_id}_{timestamp}_{img_hash}.png")

                try:
                    with open(filename, "wb") as f:
                        f.write(raw)
                    print(f"[+] Saved image to {filename}")
                except Exception as e:
                    print(f"[!] Error saving image: {e}")

    # === KEYLOGGER DETECTION (MODEL-BASED) ===
    features = extract_features(flow, request_frequency)
    try:
        prediction = keylog_model.predict(features)[0]
        probability = keylog_model.predict_proba(features)[0][1]

        if prediction == 1:
            keylog_hash = hashlib.md5(raw).hexdigest()
            keylog_key = (host, flow.request.path, keylog_hash)

            if not keylog_cache.get(keylog_key):
                keylog_cache[keylog_key] = True

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(SAVE_DIR_KEYS, f"{host}_{timestamp}_{keylog_hash}.txt")

                try:
                    with open(filename, "wb") as f:
                        f.write(raw)
                    print(f"[⚠️] Keylogging suspected! Data saved to {filename}")
                except Exception as e:
                    print(f"[!] Error saving keylog data: {e}")

                # Show system notification
                try:
                    notification.notify(
                        title="⚠️ Keylogger Alert",
                        message=f"Host: {host}\nFreq: {request_frequency} reqs/10s\nProb: {probability:.2f}",
                        timeout=5
                    )
                except Exception as e:
                    print(f"[!] Notification error: {e}")

    except Exception as e:
        print(f"[!] Error during model prediction: {e}")
