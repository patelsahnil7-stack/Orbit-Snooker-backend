from flask import Flask, request, jsonify

app = Flask(__name__)

# Basic route test
@app.route("/")
def home():
    return "Orbit Snooker Backend Running"

# Test API route
@app.route("/get-data", methods=["GET"])
def get_data():
    return jsonify({"message": "Welcome User"})

# Admin update route
@app.route("/admin-update", methods=["POST"])
def admin_update():
    data = request.get_json()
    message = data.get("message")
    return jsonify({"status": "Updated", "new_message": message})

if __name__ == "__main__":
    app.run()
