from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

app = Flask(__name__)
CORS(app)  # Mengizinkan akses API dari perangkat lain

# Koneksi ke MongoDB Atlas
uri = "mongodb+srv://haritsadu16:XoTqAt81zavw3VuX@cluster-haritsa.8tv8a.mongodb.net/?appName=Cluster-haritsa"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["iot_database"]
collection = db["sensor_data"]

# Cek apakah MongoDB Atlas bisa diakses
try:
    client.admin.command('ping')
    print("Connected to MongoDB Atlas!")
except Exception as e:
    print("MongoDB Connection Failed:", str(e))

# Endpoint untuk menerima data dari ESP32
@app.route("/sensor", methods=["POST"])
def receive_data():
    data = request.json  # Ambil data dari ESP32
    if data:
        collection.insert_one(data)  # Simpan ke MongoDB
        return jsonify({"message": "Data saved to MongoDB", "status": "success"}), 201
    return jsonify({"message": "No data received", "status": "failed"}), 400

# Endpoint untuk melihat data yang tersimpan di MongoDB
@app.route("/sensor", methods=["GET"])
def get_data():
    data = list(collection.find({}, {"_id": 0}))  # Ambil semua data dari MongoDB
    return jsonify(data), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)