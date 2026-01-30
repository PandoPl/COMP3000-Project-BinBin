from flask import Blueprint, request, jsonify
from db import db
from models import Bin, Event
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from pathlib import Path

api_bp = Blueprint("api", __name__)

def parse_timestamp(ts):
    if ts is None:
        return datetime.now(timezone.utc)

    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)

        ts_str = str(ts).strip()

        try:
            return datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
        except ValueError:
            pass

        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"

        timestamp = datetime.fromisoformat(ts_str)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return timestamp

    except (ValueError, TypeError, OSError):
        raise ValueError("Invalid timestamp format")

@api_bp.route("/health", methods = ["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@api_bp.route("/bins", methods = ["GET"])
def get_bins():
    bins = Bin.query.all()
    return jsonify([b.to_dict() for b in bins]), 200


@api_bp.route("/bins", methods = ["POST"])
def create_bin():
    data = request.get_json(silent=True) or {}
    b = Bin(
        name = data.get("name", "Unnamed Bin"),
        bin_type = data.get("bin_type", "general"),
        location = data.get("location"),
        full_threshold_cm = float(data.get("full_threshold_cm", 15.0)),
    )
    db.session.add(b)
    db.session.commit()
    return jsonify(b.to_dict()), 201


@api_bp.route("/bin-event", methods = ["POST"])
def bin_event():
    data = request.get_json(silent = True)

    if not data:
        return jsonify({"error": "JSON body required"}), 400

    if "bin_id" not in data:
        return jsonify({"error": "bin_id is required"}), 400


    try:
        bin_id = int(data["bin_id"])
    except (TypeError, ValueError):
        return jsonify({"error": "bin_id must be an integer (e.g. 1)"}), 400

    b = Bin.query.get(bin_id)
    if not b:
        return jsonify({"error": "Unknown bin_id"}), 404


    try:
        timestamp = parse_timestamp(data.get("timestamp"))
    except ValueError:
        return jsonify({"error": "Invalid timestamp format"}), 400


    ev = Event(
        bin_id = bin_id,
        timestamp = timestamp,
        event_type = data.get("event_type"),
        distance_cm = data.get("distance_cm"),
        label = data.get("label"),
        confidence = data.get("confidence"),
    )

    db.session.add(ev)
    db.session.commit()
    return jsonify(ev.to_dict()), 201


@api_bp.route("/bin-event-image", methods = ["POST"])
def bin_event_image():
    if "bin_id" not in request.form:
        return jsonify({"error": "bin_id is required"}), 400

    try:
        bin_id = int(request.form.get("bin_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "bin_id must be an integer (e.g. 1)"}), 400

    b = Bin.query.get(bin_id)
    if not b:
        return jsonify({"error": "Unknown bin_id"}), 404

    if "image" not in request.files:
        return jsonify({"error": "image file is required"}), 400

    image = request.files["image"]
    if not image or image.filename == "":
        return jsonify({"error": "empty image filename"}), 400

    try:
        timestamp = parse_timestamp(request.form.get("timestamp"))
    except ValueError:
        return jsonify({"error": "Invalid timestamp format"}), 400

    base_dir = Path(__file__).resolve().parent
    static_dir = base_dir / "static"
    upload_dir = static_dir / "uploads" / f"bin_{bin_id}"
    upload_dir.mkdir(parents = True, exist_ok = True)

    safe_name = secure_filename(image.filename)
    stamped = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{stamped}_{safe_name}"
    save_path = upload_dir / filename

    image.save(save_path)

    image_path = f"uploads/bin_{bin_id}/{filename}"

    distance_raw = request.form.get("distance_cm")
    confidence_raw = request.form.get("confidence")

    ev = Event(
        bin_id = bin_id,
        timestamp = timestamp,
        event_type = request.form.get("event_type"),
        distance_cm = float(distance_raw) if distance_raw else None,
        label = request.form.get("label"),
        confidence = float(confidence_raw) if confidence_raw else None,
        image_path = image_path
    )

    db.session.add(ev)
    db.session.commit()
    return jsonify(ev.to_dict()), 201


@api_bp.route("/events", methods = ["GET"])
def list_events():
    bin_id = request.args.get("bin_id", type = int)
    query = Event.query
    if bin_id is not None:
        query = query.filter_by(bin_id = bin_id)
    events = query.order_by(Event.timestamp.desc()).limit(100).all()
    return jsonify([e.to_dict() for e in events]), 200