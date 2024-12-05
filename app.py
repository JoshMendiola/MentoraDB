from flask import Flask
import os
from pymongo import MongoClient
from flask import jsonify

app = Flask(__name__)

# MongoDB Connection
try:
    mongodb_uri = os.getenv('MONGO_URI', 'mongodb://db_user:superS3cure411@mongodb:27017/mentora?authSource=admin')
    client = MongoClient(mongodb_uri)
    db = client.mentora  # Use the 'mentora' database

    # Test the connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")


@app.route('/api/mentora/login')
def login():
    return 'Hello World!'


@app.route('/api/mentora/register')
def register():
    return 'Hello World!'


@app.route('/api/mentora/log-interests')
def log_interests():  # Fixed duplicate function name
    return 'Hello World!'


@app.route('/api/mentora/student/get-my-classes')
def get_my_classes():  # Fixed duplicate function name
    return 'Hello World!'


@app.route('/api/mentora/student/get-recommended-classes')
def get_recommended_classes():  # Fixed duplicate function name
    return 'Hello World!'


@app.route('/api/mentora/student/register-class')
def register_class():  # Fixed duplicate function name
    return 'Hello World!'


@app.route('/api/mentora/teacher/get-my-classes')
def get_teacher_classes():  # Fixed duplicate function name
    return 'Hello World!'


@app.route('/api/mentora/teacher/create-class')
def create_class():  # Fixed duplicate function name
    return 'Hello World!'


# Add a test endpoint to verify MongoDB connection
@app.route('/api/mentora/test-db')
def test_db():
    try:
        client.admin.command('ping')
        return jsonify({"status": "success", "message": "Connected to MongoDB!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)