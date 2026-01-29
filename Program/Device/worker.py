import time
import requests
import yaml
from pathlib import Path

from sensor import BinDistanceSensor
from camera import capture_jpeg_bytes

def load_config(path = None):
    if path is None:
        path = Path(__file__).resolve().parent / "config.yaml"

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def post_event(base_url: str, payload: dict) -> bool:
    try:
        r = requests.post(f"{base_url}/api/bin-event", json=payload, timeout=5)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"[POST ERROR] {e}")
        return False

def post_event_with_image(base_url: str, payload: dict, image_bytes: bytes) -> bool:
    try:
        files = {
            "image": ("deposit.jpg", image_bytes, "image/jpeg")
        }
        data = {k: str(v) for k, v in payload.items() if v is not None}

        r = requests.post(
            f"{base_url}/api/bin-event-image",
            data = data,
            files = files,
            timeout = 30
        )
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")
        return False

def main():
    cfg = load_config()

    bin_id = cfg["bin_id"]
    base_url = cfg["backend_base_url"].rstrip("/")
    threshold_cm = float(cfg["full_threshold_cm"])
    poll_s = int(cfg.get("distance_poll_seconds", 2))
    cooldown_s = int(cfg.get("post_full_event_cooldown_seconds", 30))

    deposit_drop_cm = float(cfg.get("deposit_drop_cm", 6.0))
    deposit_stable_samples = int(cfg.get("deposit_stable_samples", 2))
    deposit_cooldown_s = int(cfg.get("deposit_cooldown_seconds", 8))

    try:
        sensor = BinDistanceSensor(trigger_pin=23, echo_pin=24)
    except Exception as e:
        print(f"[INIT ERROR] Could not setup sensor: {e}")
        return

    last_full_post = 0.0
    last_deposit_post = 0.0

    prev_dist = None
    candidate_drop = False
    stable_count = 0
    candidate_low_dist = None

    print(f"Worker started for Bin ID: {bin_id} -> {base_url}")

    while True:
        try:
            dist_cm = float(sensor.get_distance_cm())
            print(f"[DIST] {dist_cm:.2f} cm")

            now = time.time()
            is_full = dist_cm < threshold_cm

            post_event(base_url, {
                "bin_id": bin_id,
                "event_type": "fill_level",
                "distance_cm": dist_cm,
                "timestamp": now
            })

            if prev_dist is not None:
                drop = prev_dist - dist_cm

                if not candidate_drop:
                    if drop >= deposit_drop_cm and (now - last_deposit_post) > deposit_cooldown_s:
                        candidate_drop = True
                        stable_count = 0
                        candidate_low_dist = dist_cm

                else:

                    if abs(dist_cm - candidate_low_dist) <= 1.5:
                        stable_count += 1
                    else:

                        candidate_drop = False
                        stable_count = 0
                        candidate_low_dist = None

                    if candidate_drop and stable_count >= deposit_stable_samples:

                        img = capture_jpeg_bytes()

                        ok = post_event_with_image(base_url, {
                            "bin_id": bin_id,
                            "event_type": "deposit",
                            "distance_cm": dist_cm,
                            "timestamp": now
                        }, img)

                        print("[DEPOSIT + IMAGE]", "sent" if ok else "failed")

                        last_deposit_post = now
                        candidate_drop = False
                        stable_count = 0
                        candidate_low_dist = None

            prev_dist = dist_cm

            if is_full and (now - last_full_post) > cooldown_s:
                ok = post_event(base_url, {
                    "bin_id": bin_id,
                    "event_type": "bin_full",
                    "distance_cm": dist_cm,
                    "timestamp": now
                })
                print("[FULL EVENT]", "sent" if ok else "failed")
                last_full_post = now

        except Exception as e:
            print(f"[WORKER LOOP ERROR] {e}")

        time.sleep(poll_s)

if __name__ == "__main__":
    main()