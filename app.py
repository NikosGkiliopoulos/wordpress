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
def receive_property():
    try:
        data = request.get_json(force=True, silent=True)

        if not data:
            # Forminator sends an empty test request first
            return jsonify({
                "status": "ok",
                "message": "Empty test request received"
            })

        print("Incoming data:", data)

        # TODO: Save to database later
        return jsonify({"status": "success", "received": data})

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/properties', methods=['GET'])
def get_properties():
    properties = Property.query.all()
    return jsonify([p.to_dict() for p in properties])

if __name__ == '__main__':
    app.run(debug=True)
