from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///properties.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    gallery_images = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "gallery_images": json.loads(self.gallery_images or "[]")
        }

with app.app_context():
    db.create_all()

@app.route('/api/property', methods=['POST'])
def add_property():
    # Accept JSON, Form Data, or Multipart
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    title = data.get("title")
    gallery_images = data.get("gallery_images", "[]")

    # If gallery_images is a string from Forminator, convert it to a list
    try:
        if isinstance(gallery_images, str):
            gallery_images = json.loads(gallery_images)
    except:
        gallery_images = [gallery_images]

    prop = Property(
        title=title,
        gallery_images=json.dumps(gallery_images)
    )

    db.session.add(prop)
    db.session.commit()

    return jsonify({
        "status": "success",
        "property_id": prop.id
    })

@app.route('/api/properties', methods=['GET'])
def get_properties():
    properties = Property.query.all()
    return jsonify([p.to_dict() for p in properties])

if __name__ == '__main__':
    app.run(debug=True)
