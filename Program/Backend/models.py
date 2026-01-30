from datetime import datetime, timezone
from db import db

def now_utc():
    return datetime.now(timezone.utc)

class Bin(db.Model):
    __tablename__ = "bins"

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable = False)      # e.g. "Kitchen Bin"
    bin_type = db.Column(db.String(30), nullable = False)  # (general, plastic, paper, etc)
    location = db.Column(db.String(100))                   # optional
    full_threshold_cm = db.Column(db.Float, default = 15)  # distance threshold until the bin is considered full

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "bin_type": self.bin_type,
            "location": self.location,
            "full_threshold_cm": self.full_threshold_cm,
        }


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key = True)
    bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"), nullable=False)
    timestamp = db.Column(db.DateTime(timezone = True), default = now_utc)
    event_type = db.Column(db.String(30))  # e.g. "fill_level", "classification", "deposit"
    distance_cm = db.Column(db.Float)      # for fill_level / deposit events
    label = db.Column(db.String(50))       # e.g. "plastic_bottle"
    confidence = db.Column(db.Float)
    image_path = db.Column(db.String(255)) 
    human_label = db.Column(db.String(30)) # "recyclable" or "non_recyclable"
    verified = db.Column(db.Boolean, default = False)

    bin = db.relationship("Bin", backref = "events")

    def to_dict(self):
        image_url = f"/static/{self.image_path}" if self.image_path else None

        return {
            "id": self.id,
            "bin_id": self.bin_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "distance_cm": self.distance_cm,
            "label": self.label,
            "confidence": self.confidence,
            "image_url": image_url,
            "human_label": self.human_label,
            "verified": self.verified
        }