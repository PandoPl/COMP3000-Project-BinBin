# backend/api.py
from flask import Blueprint, request, jsonify
from db import db
from models import Bin, Event
from datetime import datetime, timezone

api_bp = Blueprint("api", __name__)

@api_bp.route("/health", methods = ["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@api_bp.route("/bins", methods = ["GET"])
def get_bins():
    bins = Bin.query.all()
    return jsonify([b.to_dict() for b in bins]), 200


@api_bp.route("/bins", methods = ["POST"])
def create_bin():
    data = request.get_json()
    b = Bin(
        name = data.get("name", "Unnamed Bin"),
        bin_type = data.get("bin_type", "general"),
        location = data.get("location"),
        full_threshold_cm = data.get("full_threshold_cm", 15.0),
    )
    db.session.add(b)
    db.session.commit()
    return jsonify(b.to_dict()), 201


@api_bp.route("/bin-event", methods = ["POST"])
def bin_event():
    data = request.get_json(silent = True)

    # validation
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    if "bin_id" not in data:
        return jsonify({"error": "bin_id is required"}), 400

    b = Bin.query.get(data["bin_id"])
    if not b:
        return jsonify({"error": "Unknown bin_id"}), 404
    

    ts = data.get("timestamp")
    if ts:
        try:
            timestamp = datetime.fromisoformat(ts)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo = timezone.utc)
        except ValueError:
            return jsonify({"error": "Invalid timestamp format"}), 400
    else:
        timestamp = datetime.now(timezone.utc)

    ev = Event(
        bin_id = data["bin_id"],
        timestamp = timestamp,
        event_type = data.get("event_type"),
        distance_cm = data.get("distance_cm"),
        label = data.get("label"),
        confidence = data.get("confidence"),
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
