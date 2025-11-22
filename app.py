from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os, json, re
from collections import OrderedDict

app = Flask(__name__)

# ----------------------------
# DATABASE (RENDER POSTGRES)
# ----------------------------
db_url = os.getenv("DATABASE_URL")

# Render gives postgres:// but SQLAlchemy needs postgresql://
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['JSON_SORT_KEYS'] = False
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ----------------------------
# MODEL
# ----------------------------
class Property(db.Model):
    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    transaction_type = db.Column(db.String(64))
    property_type = db.Column(db.String(64))
    price = db.Column(db.Float)
    area_size = db.Column(db.Float)
    bathrooms = db.Column(db.Integer)
    bedrooms = db.Column(db.Integer)
    city = db.Column(db.String(128))
    google_maps_link = db.Column(db.String(1024))
    region = db.Column(db.String(128))
    main_image = db.Column(db.String(1024))
    gallery_images = db.Column(db.Text)  # stored as JSON string
    furnished = db.Column(db.Boolean)
    parking = db.Column(db.Boolean)
    elevator = db.Column(db.Boolean)
    pets_allowed = db.Column(db.Boolean)
    air_conditioning = db.Column(db.Boolean)
    balcony = db.Column(db.Boolean)
    storage_room = db.Column(db.Boolean)
    sea_view = db.Column(db.Boolean)
    floor = db.Column(db.String(64))
    year_built = db.Column(db.String(64))
    renovated_year = db.Column(db.String(64))
    created_at = db.Column(db.String(64))
    status = db.Column(db.String(64))

    def to_json(self):
        return OrderedDict([
            ("id", self.id),
            ("title", self.title),
            ("description", self.description),
            ("transaction_type", self.transaction_type),
            ("property_type", self.property_type),
            ("price", self.price),
            ("area_size", self.area_size),
            ("bedrooms", self.bedrooms),
            ("bathrooms", self.bathrooms),
            ("region", self.region),
            ("city", self.city),
            ("google_maps_link", self.google_maps_link),
            ("main_image", self.main_image),
            ("gallery_images", json.loads(self.gallery_images) if self.gallery_images else []),
            ("floor", self.floor),
            ("furnished", self.furnished),
            ("parking", self.parking),
            ("elevator", self.elevator),
            ("pets_allowed", self.pets_allowed),
            ("air_conditioning", self.air_conditioning),
            ("balcony", self.balcony),
            ("storage_room", self.storage_room),
            ("sea_view", self.sea_view),
            ("year_built", self.year_built),
            ("renovated_year", self.renovated_year),
            ("created_at", self.created_at),
            ("status", self.status),
        ])

# Create table if not exists
with app.app_context():
    db.create_all()

YES_NO_MAP = {
    "one": True,
    "two": False
}

FIELD_MAPPING = {
    "text_1": "title",
    "textarea_2": "description",
    "radio_1": "property_type",
    "radio_2": "transaction_type",
    "currency_1": "price",
    "number_1": "area_size",
    "number_2": "bathrooms",
    "number_3": "bedrooms",
    "textarea_3": "region",
    "url_1": "google_maps_link",
    "text_2": "city",
    "upload_1": "main_image",
    "upload_2": "gallery_images",
    "radio_3": "furnished",
    "radio_4": "parking",
    "radio_5": "elevator",
    "radio_6": "pets_allowed",
    "radio_7": "air_conditioning",
    "radio_8": "balcony",
    "radio_9": "storage_room",
    "radio_10": "sea_view",
    "number_4": "floor",
    "number_5": "year_built",
    "number_6": "renovated_year",
    "hidden_2": "created_at",
    "hidden_3": "status"
}

# ----------------------------
# POST HANDLER
# ----------------------------
@app.route("/api/property", methods=["POST"])
def create_property():
    data = request.get_json()
    print("Incoming data:", data)

    normalized = {}

    for form_key, model_key in FIELD_MAPPING.items():
        if form_key not in data:
            continue

        value = data[form_key]

        # Boolean fields
        if model_key in [
            "furnished", "parking", "elevator", "pets_allowed",
            "air_conditioning", "balcony", "storage_room", "sea_view"
        ]:
            normalized[model_key] = YES_NO_MAP.get(value, None)

        # Gallery images (multiple)
        elif model_key == "gallery_images":
            if "forminator_multifile_hidden" in data and "upload_2" in data["forminator_multifile_hidden"]:
                files = data["forminator_multifile_hidden"]["upload_2"]
                normalized[model_key] = json.dumps([f["file_name"] for f in files])
            else:
                normalized[model_key] = json.dumps(value if isinstance(value, list) else [])

        else:
            normalized[model_key] = value

    prop = Property(**normalized)
    db.session.add(prop)
    db.session.commit()

    return jsonify({"success": True, "id": prop.id})

# ----------------------------
# GET ALL
# ----------------------------
@app.route("/api/properties")
def list_properties():
    result = [p.to_json() for p in Property.query.all()]
    return jsonify(result)

# ----------------------------
# GET ONE
# ----------------------------
@app.route("/api/property/<int:id>")
def get_property(id):
    prop = Property.query.get_or_404(id)
    return jsonify(prop.to_json())

if __name__ == "__main__":
    app.run(debug=True)
