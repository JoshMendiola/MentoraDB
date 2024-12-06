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

    try:
        interests = data['interests']
        if not isinstance(interests, list) or not all(isinstance(i, str) for i in interests):
            return jsonify({'message': 'Invalid interests format'}), 400

        result = db.users.find_one_and_update(
            {'_id': ObjectId(current_user_id)},
            {'$set': {'interests': interests}},
            return_document=True
        )

        if not result:
            return jsonify({'message': 'User not found'}), 404

        return jsonify({
            'message': 'Interests updated successfully',
            'user': {
                'id': str(result['_id']),
                'username': result['username'],
                'fullName': result['fullName'],
                'email': result['email'],
                'role': result['role'],
                'interests': result['interests']
            }
        }), 200

    except Exception as e:
        print(f"Error updating interests: {e}")
        return jsonify({'message': 'Server error updating interests'}), 500


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


@app.route('/api/mentora/interests', methods=['GET'])
def get_interests():
    try:
        # Get all interests from the interests collection
        interests = list(db.interests.find({}, {'_id': 0, 'name': 1}))
        # Convert the cursor to a list of interest names
        interest_list = [interest['name'] for interest in interests]
        return jsonify(interest_list), 200
    except Exception as e:
        print(f"Error fetching interests: {e}")
        return jsonify({'message': 'Error fetching interests'}), 500


@app.route('/api/mentora/interests/batch', methods=['POST'])
def add_interests():
    data = request.get_json()

    if not data or 'interests' not in data:
        return jsonify({'message': 'No interests provided'}), 400

    try:
        interests = data['interests']
        if not isinstance(interests, list) or not all(isinstance(i, str) for i in interests):
            return jsonify({'message': 'Invalid interests format'}), 400

        # Convert interests to documents
        interest_docs = [{'name': name} for name in interests]

        # Insert interests, ignore duplicates
        result = db.interests.insert_many(interest_docs, ordered=False)

        return jsonify({
            'message': 'Interests added successfully',
            'added_count': len(result.inserted_ids)
        }), 201
    except Exception as e:
        print(f"Error adding interests: {e}")
        return jsonify({'message': 'Error adding interests'}), 500


@app.route('/api/mentora/user/interests', methods=['GET'])
@jwt_required()
def get_user_interests():
    current_user_id = get_jwt_identity()
    user = db.users.find_one({'_id': ObjectId(current_user_id)})

    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify({
        'interests': user.get('interests', [])
    }), 200


@app.route('/api/mentora/courses', methods=['POST'])
@jwt_required()
def create_course():
    current_user_id = get_jwt_identity()

    # Verify user is a teacher
    user = db.users.find_one({'_id': ObjectId(current_user_id)})
    if not user or user['role'] != 'Teacher':
        return jsonify({'message': 'Unauthorized - Teachers only'}), 403

    data = request.get_json()
    required_fields = ['title', 'description', 'sections', 'difficulty_level',
                       'estimated_hours', 'prerequisites', 'learning_objectives',
                       'category', 'tags']

    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    # Validate sections format
    if not isinstance(data['sections'], list):
        return jsonify({'message': 'Sections must be an array'}), 400

    for section in data['sections']:
        if not all(key in section for key in ['title', 'content', 'order']):
            return jsonify({'message': 'Invalid section format'}), 400

    new_course = {
        'title': data['title'],
        'description': data['description'],
        'sections': data['sections'],
        'difficulty_level': data['difficulty_level'],
        'estimated_hours': data['estimated_hours'],
        'prerequisites': data['prerequisites'],
        'learning_objectives': data['learning_objectives'],
        'category': data['category'],
        'tags': data['tags'],
        'teacher_id': current_user_id,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'status': 'draft',
        'enrollment_count': 0,
        'completion_count': 0,
        'average_rating': 0.0,
        'total_reviews': 0
    }

    result = db.courses.insert_one(new_course)
    new_course['_id'] = str(result.inserted_id)

    return jsonify(new_course), 201


@app.route('/api/mentora/courses/<course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    current_user_id = get_jwt_identity()

    # Verify user is a teacher and owns the course
    course = db.courses.find_one({'_id': ObjectId(course_id)})
    if not course or course['teacher_id'] != current_user_id:
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    updateable_fields = ['title', 'description', 'sections', 'difficulty_level',
                         'estimated_hours', 'prerequisites', 'learning_objectives',
                         'status', 'category', 'tags']

    update_data = {
        'updated_at': datetime.utcnow()
    }

    for field in updateable_fields:
        if field in data:
            update_data[field] = data[field]

    result = db.courses.find_one_and_update(
        {'_id': ObjectId(course_id)},
        {'$set': update_data},
        return_document=True
    )

    if result:
        result['_id'] = str(result['_id'])
        return jsonify(result), 200

    return jsonify({'message': 'Course not found'}), 404


@app.route('/api/mentora/courses', methods=['GET'])
@jwt_required()
def get_teacher_courses():
    current_user_id = get_jwt_identity()

    # Optional query parameters
    status = request.args.get('status')
    category = request.args.get('category')

    # Build query
    query = {'teacher_id': current_user_id}
    if status:
        query['status'] = status
    if category:
        query['category'] = category

    courses = list(db.courses.find(query))

    # Convert ObjectId to string
    for course in courses:
        course['_id'] = str(course['_id'])

    return jsonify(courses), 200


@app.route('/api/mentora/courses/<course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    try:
        course = db.courses.find_one({'_id': ObjectId(course_id)})
        if course:
            course['_id'] = str(course['_id'])
            return jsonify(course), 200
        return jsonify({'message': 'Course not found'}), 404
    except Exception as e:
        return jsonify({'message': 'Invalid course ID'}), 400


@app.route('/api/mentora/courses/<course_id>/publish', methods=['POST'])
@jwt_required()
def publish_course(course_id):
    current_user_id = get_jwt_identity()

    # Verify user is a teacher and owns the course
    course = db.courses.find_one({'_id': ObjectId(course_id)})
    if not course or course['teacher_id'] != current_user_id:
        return jsonify({'message': 'Unauthorized'}), 403

    result = db.courses.find_one_and_update(
        {'_id': ObjectId(course_id)},
        {'$set': {'status': 'published', 'updated_at': datetime.utcnow()}},
        return_document=True
    )

    if result:
        result['_id'] = str(result['_id'])
        return jsonify(result), 200

    return jsonify({'message': 'Course not found'}), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0'
            )