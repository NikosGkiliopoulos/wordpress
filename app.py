from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json, re, os

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
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    transaction_type = db.Column(db.String(50))
    property_type = db.Column(db.String(50))
    price = db.Column(db.Float)
    area_size = db.Column(db.Float)
    bathrooms = db.Column(db.Integer)
    bedrooms = db.Column(db.Integer)
    city = db.Column(db.String(100))
    region = db.Column(db.String(100))
    google_maps_link = db.Column(db.String(255))
    main_image = db.Column(db.String(1024))
    gallery_images = db.Column(db.Text)  # JSON array
    furnished = db.Column(db.Boolean)
    parking = db.Column(db.Boolean)
    elevator = db.Column(db.Boolean)
    pets_allowed = db.Column(db.Boolean)
    air_conditioning = db.Column(db.Boolean)
    balcony = db.Column(db.Boolean)
    storage_room = db.Column(db.Boolean)
    sea_view = db.Column(db.Boolean)
    floor = db.Column(db.String(50))
    year_built = db.Column(db.String(50))
    renovated_year = db.Column(db.String(50))
    created_at = db.Column(db.String(50))
    status = db.Column(db.String(50))

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
            "region": self.region,
            "google_maps_link": self.google_maps_link,
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
def normalize_key(k: str) -> str:
    """Lowercase, remove punctuation, replace spaces and dashes with underscores"""
    k = k.strip().lower()
    k = re.sub(r'[\-\s/]+', '_', k)
    k = re.sub(r'[^a-z0-9_\u0370-\u03ff]', '', k)  # keep basic latin + greek block chars
    return k


def boolify(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ('1', 'true', 'yes', 'on', 'y', 'ναι', 'yes '):
        return True
    if s in ('0', 'false', 'no', 'off', 'n', 'όχι'):
        return False
    return None


def parse_number(v, cast=float, default=None):
    try:
        if v is None or v == '':
            return default
        # remove commas, currency symbols
        s = str(v).strip().replace(',', '').replace('€', '').replace('EUR', '')
        return cast(s)
    except Exception:
        return default


def parse_images_field(v):
    """
    Accept many possible formats:
    - list of URLs
    - single URL string
    - comma-separated filenames
    - list of filenames
    - strings of filenames separated by newline
    We return a list of strings.
    """
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if x is not None and str(x).strip()]
    s = str(v).strip()
    if s == '':
        return []
    # JSON list encoded as string?
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if x]
    except Exception:
        pass
    # split by commas or newlines
    parts = re.split(r'[\r\n,]+', s)
    parts = [p.strip() for p in parts if p.strip()]
    return parts


# Mapping of canonical fields to possible incoming keys
FIELD_KEYS = {
    "title": ["title", "title_field", "τίτλος", "όνομα"],
    "description": ["description", "Περιγραφή", "description_field", "desc"],
    "transaction_type": ["transaction_type", "transaction-type", "transaction type", "transaction", "Transaction Type",
                         "Transaction"],
    "property_type": ["property_type", "property-type", "property type", "Property Type"],
    "price": ["price", "τιμή", "Τιμή Ευρώ", "price_eur"],
    "area_size": ["area_size", "area size (sqm)", "area_size_(sqm)", "area", "Area Size (sqm)"],
    "bathrooms": ["bathrooms", "Bathrooms"],
    "bedrooms": ["bedrooms", "Bedrooms"],
    "city": ["city", "location_city", "Location", "City"],
    "region": ["region", "region_area", "Region / Area", "Region"],
    "google_maps_link": ["google_maps_link", "google maps link", "Google Maps Link"],
    "main_image": ["main_image", "main image", "Main Image (file upload)", "Main Image", "main-image"],
    "gallery_images": ["gallery_images", "gallery images", "Gallery Images (multi-file upload)", "gallery-images"],
    "furnished": ["furnished", "Furnished"],
    "parking": ["parking", "Parking"],
    "elevator": ["elevator", "Elevator"],
    "pets_allowed": ["pets_allowed", "Pets Allowed"],
    "air_conditioning": ["air_conditioning", "Air Conditioning"],
    "balcony": ["balcony", "Balcony"],
    "storage_room": ["storage_room", "Storage Room"],
    "sea_view": ["sea_view", "Sea View"],
    "floor": ["floor", "Floor"],
    "year_built": ["year_built", "Year Built"],
    "renovated_year": ["renovated_year", "Renovated Year (optional)"],
    "created_at": ["created_at", "Date Submitted", "created"],
    "status": ["status"]
}


def find_value(data_normalized, keys):
    for k in keys:
        nk = normalize_key(k)
        if nk in data_normalized:
            return data_normalized[nk]
        # also try raw key
        if k in data_normalized:
            return data_normalized[k]
    return None


# ------------------------
# POST handler
# ------------------------
@app.route('/api/property', methods=['POST'])
def receive_property():
    try:
        # try parse JSON (silent so no exception on bad content-type)
        incoming = request.get_json(force=False, silent=True)
        if incoming is None:
            # sometimes Forminator sends form-encoded; try request.form
            if request.form:
                incoming = request.form.to_dict(flat=True)
            else:
                incoming = {}
        # normalize keys map: normalized_key -> value
        data_normalized = {}
        for k, v in incoming.items():
            nk = normalize_key(k)
            data_normalized[nk] = v

        # debug log: print the incoming raw payload and normalized keys
        print("=== Incoming raw payload ===")
        print(incoming)
        print("=== Normalized keys ===")
        print(list(data_normalized.keys()))

        # If empty test request from Forminator (no fields) -> return OK
        if not incoming:
            return jsonify({"status": "ok", "message": "Empty test request received"})

        # Build property fields using tolerant mapping
        get = lambda canonical: find_value(data_normalized, FIELD_KEYS.get(canonical, []))

        title = get("title") or get("title")
        description = get("description") or ""
        transaction_type = get("transaction_type") or ""
        property_type = get("property_type") or ""
        price = parse_number(get("price"), float, default=None)
        area_size = parse_number(get("area_size"), float, default=None)
        bathrooms = parse_number(get("bathrooms"), int, default=None)
        bedrooms = parse_number(get("bedrooms"), int, default=None)
        city = get("city") or ""
        region = get("region") or ""
        google_maps_link = get("google_maps_link") or ""
        main_image_raw = get("main_image")
        gallery_raw = get("gallery_images")

        main_image_list = parse_images_field(main_image_raw) if main_image_raw else []
        main_image = main_image_list[0] if main_image_list else (str(main_image_raw).strip() if main_image_raw else "")

        gallery_images = parse_images_field(gallery_raw) if gallery_raw else []

        furnished = boolify(get("furnished"))
        parking = boolify(get("parking"))
        elevator = boolify(get("elevator"))
        pets_allowed = boolify(get("pets_allowed"))
        air_conditioning = boolify(get("air_conditioning"))
        balcony = boolify(get("balcony"))
        storage_room = boolify(get("storage_room"))
        sea_view = boolify(get("sea_view"))

        floor = get("floor") or ""
        year_built = get("year_built") or ""
        renovated_year = get("renovated_year") or ""
        created_at = get("created_at") or ""
        status = get("status") or "available"

        # create and save
        prop = Property(
            title=str(title) if title else "Untitled property",
            description=str(description),
            transaction_type=str(transaction_type),
            property_type=str(property_type),
            price=price,
            area_size=area_size,
            bathrooms=bathrooms,
            bedrooms=bedrooms,
            city=str(city),
            region=str(region),
            google_maps_link=str(google_maps_link),
            main_image=str(main_image),
            gallery_images=json.dumps(gallery_images),
            furnished=furnished,
            parking=parking,
            elevator=elevator,
            pets_allowed=pets_allowed,
            air_conditioning=air_conditioning,
            balcony=balcony,
            storage_room=storage_room,
            sea_view=sea_view,
            floor=str(floor),
            year_built=str(year_built),
            renovated_year=str(renovated_year),
            created_at=str(created_at),
            status=str(status)
        )
        db.session.add(prop)
        db.session.commit()

        return jsonify({"status": "success", "property_id": prop.id})

    except Exception as e:
        print("Error in /api/property:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ------------------------
# GET endpoints (unchanged)
# ------------------------
@app.route('/api/properties', methods=['GET'])
def get_properties():
    props = Property.query.order_by(Property.id.desc()).all()
    return jsonify([p.to_dict() for p in props])


@app.route('/api/property/<int:prop_id>', methods=['GET'])
def get_property(prop_id):
    prop = Property.query.get_or_404(prop_id)
    return jsonify(prop.to_dict())


if __name__ == "__main__":
    app.run(debug=True)