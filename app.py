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
        return {"id": self.id, "title": self.title, "gallery_images": json.loads(self.gallery_images or "[]")}

with app.app_context():
    db.create_all()

@app.route('/api/property', methods=['POST'])
def add_property():
    data = request.json
    prop = Property(title=data.get("title"), gallery_images=json.dumps(data.get("gallery_images", [])))
    db.session.add(prop)
    db.session.commit()
    return jsonify({"status": "success", "property_id": prop.id})

@app.route('/api/properties', methods=['GET'])
def get_properties():
    return jsonify([p.to_dict() for p in Property.query.all()])

if __name__ == '__main__':
    app.run(debug=True)
