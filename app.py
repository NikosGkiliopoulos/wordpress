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

# ------------------------
# POST handler: receive Forminator webhook
# ------------------------
@app.route('/api/property', methods=['POST'])
def api_property_post():
    try:
        # try JSON first, otherwise form data
        incoming = request.get_json(force=False, silent=True)
        if incoming is None:
            # try form-encoded
            if request.form:
                incoming = request.form.to_dict(flat=True)
            else:
                incoming = {}
        # If Forminator sends an array wrapper, handle it (some Forminator exports show an array)
        if isinstance(incoming, list) and len(incoming) > 0 and isinstance(incoming[0], dict):
            # take first object
            incoming = incoming[0]

        # If empty test request, return OK
        if not incoming:
            return jsonify({"status": "ok", "message": "Empty test request received"}), 200

        # normalize keys
        normalized = normalize_incoming(incoming)

        # parse fields
        title = normalized.get("title") or "Untitled property"
        description = normalized.get("description") or ""
        transaction_type = normalized.get("transaction_type") or ""
        property_type = normalized.get("property_type") or ""
        price = parse_float(normalized.get("price"))
        area_size = parse_float(normalized.get("area_size"))
        bathrooms = parse_int(normalized.get("bathrooms"))
        bedrooms = parse_int(normalized.get("bedrooms"))
        city = normalized.get("city") or ""
        google_maps_link = normalized.get("google_maps_link") or ""
        region = normalized.get("region") or ""

        main_image_raw = normalized.get("main_image")
        main_images = parse_gallery_field(main_image_raw)
        main_image = main_images[0] if main_images else (str(main_image_raw).strip() if main_image_raw else "")

        gallery_raw = normalized.get("gallery_images")
        gallery_list = parse_gallery_field(gallery_raw)

        furnished = parse_bool(normalized.get("furnished"))
        parking = parse_bool(normalized.get("parking"))
        elevator = parse_bool(normalized.get("elevator"))
        pets_allowed = parse_bool(normalized.get("pets_allowed"))
        air_conditioning = parse_bool(normalized.get("air_conditioning"))
        balcony = parse_bool(normalized.get("balcony"))
        storage_room = parse_bool(normalized.get("storage_room"))
        sea_view = parse_bool(normalized.get("sea_view"))

        floor = normalized.get("floor") or ""
        year_built = normalized.get("year_built") or ""
        renovated_year = normalized.get("renovated_year") or ""
        created_at = normalized.get("created_at") or ""
        status = normalized.get("status") or "available"

        # create and save
        prop = Property(
            title=title,
            description=description,
            transaction_type=transaction_type,
            property_type=property_type,
            price=price,
            area_size=area_size,
            bathrooms=bathrooms,
            bedrooms=bedrooms,
            city=city,
            google_maps_link=google_maps_link,
            region=region,
            main_image=main_image,
            gallery_images=json.dumps(gallery_list),
            furnished=furnished,
            parking=parking,
            elevator=elevator,
            pets_allowed=pets_allowed,
            air_conditioning=air_conditioning,
            balcony=balcony,
            storage_room=storage_room,
            sea_view=sea_view,
            floor=floor,
            year_built=year_built,
            renovated_year=renovated_year,
            created_at=created_at,
            status=status
        )
        db.session.add(prop)
        db.session.commit()

        # debug log
        print("Saved property id:", prop.id)
        print("Normalized payload:", normalized)

        return jsonify({"status": "success", "property_id": prop.id}), 200

    except Exception as e:
        print("Error in /api/property:", repr(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# ------------------------
# GET endpoints
# ------------------------
@app.route('/api/properties', methods=['GET'])
def api_get_properties():
    props = Property.query.order_by(Property.id.desc()).all()
    return jsonify([p.to_dict() for p in props])

@app.route('/api/property/<int:prop_id>', methods=['GET'])
def api_get_property(prop_id):
    prop = Property.query.get_or_404(prop_id)
    return jsonify(prop.to_dict())

if __name__ == "__main__":
    app.run(debug=True)