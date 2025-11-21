from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json, re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///properties.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------------
# Model
# ------------------------
class Property(db.Model):
    __tablename__ = 'properties'
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
    main_image = db.Column(db.String(1024))        # store full URL
    gallery_images = db.Column(db.Text)            # JSON list of URLs
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

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "transaction_type": self.transaction_type,
            "property_type": self.property_type,
            "price": self.price,
            "area_size": self.area_size,
            "bathrooms": self.bathrooms,
            "bedrooms": self.bedrooms,
            "city": self.city,
            "google_maps_link": self.google_maps_link,
            "region": self.region,
            "main_image": self.main_image,
            "gallery_images": json.loads(self.gallery_images) if self.gallery_images else [],
            "furnished": self.furnished,
            "parking": self.parking,
            "elevator": self.elevator,
            "pets_allowed": self.pets_allowed,
            "air_conditioning": self.air_conditioning,
            "balcony": self.balcony,
            "storage_room": self.storage_room,
            "sea_view": self.sea_view,
            "floor": self.floor,
            "year_built": self.year_built,
            "renovated_year": self.renovated_year,
            "created_at": self.created_at,
            "status": self.status
        }

with app.app_context():
    db.create_all()

# ------------------------
# Helpers
# ------------------------
def parse_bool(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ('1','true','yes','on','y','ναι','yes '):
        return True
    if s in ('0','false','no','off','n','όχι'):
        return False
    return None

def parse_float(v):
    try:
        if v is None or str(v).strip() == "":
            return None
        s = str(v).strip().replace(',', '').replace('€','').replace('EUR','')
        return float(s)
    except Exception:
        return None

def parse_int(v):
    try:
        if v is None or str(v).strip() == "":
            return None
        s = str(v).strip().split('.')[0]
        return int(s)
    except Exception:
        return None

def parse_gallery_field(v):
    """
    Accepts:
      - an actual list (already parsed)
      - comma-separated string of URLs
      - string with URLs separated by commas/spaces/newlines
    Returns list of strings (URLs / filenames)
    """
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    if s == "":
        return []
    # Try JSON parse (sometimes Forminator sends JSON array as string)
    try:
        j = json.loads(s)
        if isinstance(j, list):
            return [str(x).strip() for x in j if str(x).strip()]
    except Exception:
        pass
    parts = re.split(r'[\r\n,]+', s)
    parts = [p.strip() for p in parts if p.strip()]
    return parts

# Map the exact CSV column labels to canonical keys
CSV_TO_KEY = {
    "Title": "title",
    "Περιγραφή": "description",
    "Transaction Type": "transaction_type",
    "Property Type": "property_type",
    "Τιμή Ευρώ": "price",
    "Area Size (sqm)": "area_size",
    "Bathrooms": "bathrooms",
    "Bedrooms": "bedrooms",
    "Location - City": "city",
    "Location - Google Maps Link": "google_maps_link",
    "Location - Region / Area": "region",
    "Photos / Media - Main Image (file upload)": "main_image",
    "Photos / Media - Gallery Images (multi-file upload)": "gallery_images",
    "Key Features - Furnished": "furnished",
    "Key Features - Parking": "parking",
    "Key Features - Elevator": "elevator",
    "Key Features - Pets Allowed": "pets_allowed",
    "Key Features - Air Conditioning": "air_conditioning",
    "Key Features - Balcony": "balcony",
    "Key Features - Storage Room": "storage_room",
    "Key Features - Sea View": "sea_view",
    "Extra Property Details - Floor": "floor",
    "Extra Property Details - Year Built": "year_built",
    "Extra Property Details - Renovated Year (optional)": "renovated_year",
    "created_at": "created_at",
    "status": "status",
    "id": "incoming_id"
}

def normalize_incoming(incoming):
    """
    Build a dict with canonical keys (CSV_TO_KEY values) from incoming payload.
    Accepts JSON or form-encoded dicts.
    """
    result = {}
    # incoming may have keys exactly as CSV header, or normalized keys. handle both
    for raw_k, raw_v in incoming.items():
        # try direct match
        if raw_k in CSV_TO_KEY:
            result[CSV_TO_KEY[raw_k]] = raw_v
            continue
        # try some normalized versions (strip spaces, case)
        nk = raw_k.strip()
        for header, target in CSV_TO_KEY.items():
            if nk.lower() == header.lower():
                result[target] = raw_v
                break
        else:
            # fallback: simple normalized key (remove punctuation/space)
            key_norm = re.sub(r'[\s\-_]+', ' ', raw_k).strip().lower()
            for header, target in CSV_TO_KEY.items():
                if key_norm == header.lower():
                    result[target] = raw_v
                    break
            # otherwise ignore unknown fields (or you can store raw payload if needed)
    return result

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

# Convert Forminator Yes/No (radio) to boolean
YES_NO_MAP = {
    "one": True,
    "two": False
}

# ------------------------
# POST handler: receive Forminator webhook
# ------------------------
@app.route('/api/property', methods=['POST'])
def api_property_post():
    data = request.get_json()
    print("RAW incoming data:", request.data)

    normalized = {}

    # Map fields
    for form_key, model_key in FIELD_MAPPING.items():
        if form_key in data:
            value = data[form_key]
            # Convert Yes/No radios to boolean
            if model_key in ["furnished", "parking", "elevator", "pets_allowed", "air_conditioning", "balcony", "storage_room", "sea_view"]:
                normalized[model_key] = YES_NO_MAP.get(value, None)
            # Handle gallery_images as list
            elif model_key == "gallery_images":
                if "forminator_multifile_hidden" in data and f"upload_2" in data["forminator_multifile_hidden"]:
                    files = data["forminator_multifile_hidden"]["upload_2"]
                    normalized[model_key] = ",".join([f["file_name"] for f in files])
                else:
                    normalized[model_key] = value
            else:
                normalized[model_key] = value

    # Save to DB
    prop = Property(**normalized)
    db.session.add(prop)
    db.session.commit()

    print("Saved property id:", prop.id)
    print("Normalized payload:", normalized)

    return jsonify({"success": True, "id": prop.id})
# ------------------------
# GET endpoints
# ------------------------
@app.route('/api/properties', methods=['GET'])
def get_properties():
    props = Property.query.all()
    result = []
    for p in props:
        result.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "property_type": p.property_type,
            "transaction_type": p.transaction_type,
            "price": p.price,
            "area_size": p.area_size,
            "bathrooms": p.bathrooms,
            "bedrooms": p.bedrooms,
            "city": p.city,
            "region": p.region,
            "google_maps_link": p.google_maps_link,
            "main_image": p.main_image,
            "gallery_images": p.gallery_images.split(",") if p.gallery_images else [],
            "furnished": p.furnished,
            "parking": p.parking,
            "elevator": p.elevator,
            "pets_allowed": p.pets_allowed,
            "air_conditioning": p.air_conditioning,
            "balcony": p.balcony,
            "storage_room": p.storage_room,
            "sea_view": p.sea_view,
            "floor": p.floor,
            "year_built": p.year_built,
            "renovated_year": p.renovated_year,
            "created_at": p.created_at,
            "status": p.status
        })
    return jsonify(result)

@app.route('/api/property/<int:prop_id>', methods=['GET'])
def api_get_property(prop_id):
    prop = Property.query.get_or_404(prop_id)
    return jsonify(prop.to_dict())

if __name__ == "__main__":
    app.run(debug=True)