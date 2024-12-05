from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    get_jwt_identity, jwt_required
)
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=int(os.getenv('JWT_TOKEN_EXPIRE_DAYS', '7')))
jwt = JWTManager(app)

# MongoDB Connection
try:
    mongodb_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongodb_uri)
    db = client[os.getenv('MONGO_DB_NAME')]

    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")


@app.route('/api/mentora/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400

    user = db.users.find_one({'username': data['username']})

    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401

    access_token = create_access_token(identity=str(user['_id']))

    return jsonify({
        'token': access_token,
        'user': {
            'id': str(user['_id']),
            'username': user['username'],
            'fullName': user['fullName'],
            'email': user['email'],
            'role': user['role'],
            'interests': user.get('interests', [])
        }
    }), 200


@app.route('/api/mentora/register', methods=['POST'])
def register():
    data = request.get_json()

    required_fields = ['username', 'password', 'email', 'fullName', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    # Check if username or email already exists
    if db.users.find_one({'$or': [
        {'username': data['username']},
        {'email': data['email']}
    ]}):
        return jsonify({'message': 'Username or email already exists'}), 409

    # Create new user
    new_user = {
        'username': data['username'],
        'password': generate_password_hash(data['password']),
        'email': data['email'],
        'fullName': data['fullName'],
        'role': data['role'],
        'interests': [],
        'created_at': datetime.datetime.utcnow()
    }

    result = db.users.insert_one(new_user)
    access_token = create_access_token(identity=str(result.inserted_id))

    return jsonify({
        'token': access_token,
        'user': {
            'id': str(result.inserted_id),
            'username': new_user['username'],
            'fullName': new_user['fullName'],
            'email': new_user['email'],
            'role': new_user['role'],
            'interests': new_user['interests']
        }
    }), 201


@app.route('/api/mentora/update-interests', methods=['POST'])
@jwt_required()
def update_interests():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'interests' not in data:
        return jsonify({'message': 'No interests provided'}), 400

    db.users.update_one(
        {'_id': ObjectId(current_user_id)},
        {'$set': {'interests': data['interests']}}
    )

    return jsonify({
        'message': 'Interests updated successfully',
        'interests': data['interests']
    }), 200


@app.route('/api/mentora/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user_id = get_jwt_identity()
    user = db.users.find_one({'_id': ObjectId(current_user_id)})

    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify({
        'user': {
            'id': str(user['_id']),
            'username': user['username'],
            'fullName': user['fullName'],
            'email': user['email'],
            'role': user['role'],
            'interests': user.get('interests', [])
        }
    }), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')