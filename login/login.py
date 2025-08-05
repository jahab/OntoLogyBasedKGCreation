from flask import Flask, jsonify, request, make_response
import pymongo
import jwt
import datetime
import traceback

SECRET_KEY = "this_is_my_db"  # TODO: FIXME: use env in production

# creating a Flask app
app = Flask(__name__)

# MongoDB connection
myclient = pymongo.MongoClient("mongodb://mongodb:27017")
mydb = myclient["db"]
mycol = mydb["users"]

try:
    mycol.create_index([('username', 1)], unique=True)
except Exception as e:
    pass
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'ping': 'pong from login service'})

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json

        if not data or "username" not in data or "password" not in data:
            return make_response(jsonify({'error': 'Username and password required'}), 400)

        existing_user = mycol.find_one({"username": data["username"]})
        if existing_user:
            return make_response(jsonify({'error': 'Username already exists'}), 409)

        user_data = {
            "username": data["username"],
            "password": data["password"]  # In production: hash this!
        }

        mycol.insert_one(user_data)

        return make_response(jsonify({'message': 'User registered successfully'}), 201)
    except Exception as e:
        return make_response(jsonify({'error': f"sercer error: {traceback.format_exc()}"}), 400)


@app.route('/signin', methods=['POST'])
def signin():
    data = request.json

    if not data or "username" not in data or "password" not in data:
        return make_response(jsonify({'error': 'Username and password required'}), 400)

    user = mycol.find_one({"username": data["username"]})
    if not user:
        return make_response(jsonify({'error': 'User not found'}), 404)

    if user["password"] != data["password"]:
        return make_response(jsonify({'error': 'Incorrect password'}), 401)

    payload = {
        "user_id": str(user["_id"]),  # Mongo ObjectId to string
        "exp": datetime.datetime.now() + datetime.timedelta(days=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return jsonify({'message': 'Login successful', 'token': token})



@app.route('/forgetpwd', methods=['POST'])
def forgetpwd():
    data = request.json

    if not data or "username" not in data or "new_password" not in data:
        return make_response(jsonify({'error': 'Username and new password required'}), 400)

    user = mycol.find_one({"username": data["username"]})
    if not user:
        return make_response(jsonify({'error': 'User not found'}), 404)

    mycol.update_one({"username": data["username"]}, {"$set": {"password": data["new_password"]}})

    return make_response(jsonify({'message': 'Password updated successfully'}), 200)

if __name__ == '__main__':
    user_data = {
        "username": "test_user",
        "password": "test_password"  # In production: hash this!
    }
    try:
        mycol.insert_one(user_data)
    except Exception as e:
        print("User already exists")
    app.run(debug=True, host='0.0.0.0', port=5000)
