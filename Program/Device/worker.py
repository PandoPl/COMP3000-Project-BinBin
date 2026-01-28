import time
import requests
import yaml

from sensor import BinDistanceSensor

def load_config(path="device/config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def post_event(base_url: str, payload: dict) -> bool:
    try:
        r = requests.post(f"{base_url}/api/bin-event", json=payload, timeout=5)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"[POST ERROR] {e}")
        return False

def main():
    cfg = load_config()
    bin_id = cfg["bin_id"]
    base_url = cfg["backend_base_url"].rstrip("/")
    threshold_cm = float(cfg["full_threshold_cm"])
    poll_s = int(cfg.get("distance_poll_seconds", 2))
    cooldown_s = int(cfg.get("post_full_event_cooldown_seconds", 30))

    sensor = BinDistanceSensor(trigger_pin=23, echo_pin=24)

    last_full_post = 0.0

    while True:
        dist_cm = sensor.get_distance_cm()
        print(f"[DIST] {dist_cm:.2f} cm")

        now = time.time()
        is_full = dist_cm < threshold_cm

        post_event(base_url, {
            "bin_id": bin_id,
            "event_type": "fill_level",
            "distance_cm": float(dist_cm),
            "timestamp": now
        })

        if is_full and (now - last_full_post) > cooldown_s:
            ok = post_event(base_url, {
                "bin_id": bin_id,
                "event_type": "bin_full",
                "distance_cm": float(dist_cm),
                "timestamp": now
            })
            print("[FULL EVENT]", "sent" if ok else "failed")
            last_full_post = now

        time.sleep(poll_s)

if __name__ == "__main__":
    main()
