from flask import Flask, request, jsonify
import jwt
from geopy.distance import geodesic
import datetime
import sqlite3

app = Flask(__name__)
key = "ZYPSIE"

# Sample user_data dictionary for demonstration purposes
user_data = {"user_id": 1, "role": "student"}
# Predefined coordinates of the classroom (you can change these according to your needs)
CLASSROOM_COORDINATES = (27.724150506409902, 85.35707659949882)

# SQLite database file name
DB_FILE = "attendance.db"


# Function to initialize the database and create the required table
def initialize_database():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def get_user_info(token):
    payload = jwt.decode(token, key, algorithms=["HS256"])
    user_info = {"user_id": payload["user_id"]}
    return user_info


def authorize_user(required_role):
    def decorator(func):
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization")
            token = token.replace("Bearer ", "")
            if not token:
                return jsonify({"message": "Missing token"}), 401

            try:
                payload = jwt.decode(token, key, algorithms=["HS256"])
                user_info = {
                    "user_id": payload["user_id"],
                    "role": payload["role"],  # Add other user information as needed
                }
            except jwt.ExpiredSignatureError:
                return jsonify({"message": "Invalid or expired token"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"message": "Invalid token"}), 401

            # Check if user has the required role or permission
            if user_info["role"] != required_role:
                return jsonify({"message": "Not authorized"}), 403

            # If authorized, continue with the original request
            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


@app.route("/api/verify-attendance", methods=["POST"])
def verify_attendance():
    token = request.headers.get("Authorization")
    token = token.replace("Bearer ", "")
    if not token:
        return jsonify({"message": "Missing token"}), 401

    user_info = get_user_info(token)
    if user_info is None:
        return jsonify({"message": "Invalid or expired token"}), 40

    # Get the geo-location information from the request payload
    user_latitude = request.json.get("latitude")
    user_longitude = request.json.get("longitude")

    # Perform the geo-location verification here
    user_coordinates = (float(user_latitude), float(user_longitude))
    distance_to_classroom = geodesic(user_coordinates, CLASSROOM_COORDINATES).meters

    # Adjust the maximum allowed distance based on your scenario
    max_allowed_distance = 100  # in meters, change it according to your needs

    attendance_verified = distance_to_classroom <= max_allowed_distance

    # Return the verification result along with user information
    if attendance_verified:
        # Check attendance for the day
        user_info = get_user_info(token)
        user_id = user_info["user_id"]
        device_id = request.json.get("device_id")

        # Check if user has already had attendance for the day
        if not has_attendance_for_day(user_id):
            # Check if the device has already recorded attendance for the day
            if not has_attendance_for_device(device_id):
                save_attendance(user_id, device_id)
                return f"Attendance verified successfully for {user_info['user_id']}"
            else:
                return f"Attendance already recorded for another user on this device today."
        else:
            return (
                f"Attendance already recorded for {user_info['user_id']} on this day."
            )
    else:
        return f"Attendance verification failed for {user_info['user_id']}"


# Function to check if a user has attendance for the current day
def has_attendance_for_day(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        today = datetime.date.today()
        c.execute(
            "SELECT * FROM attendance WHERE user_id=? AND DATE(timestamp)=?",
            (user_id, today),
        )
        return c.fetchone() is not None


# Function to check if a device has recorded attendance for the current day
def has_attendance_for_device(device_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        today = datetime.date.today()
        c.execute(
            "SELECT * FROM attendance WHERE device_id=? AND DATE(timestamp)=?",
            (device_id, today),
        )
        return c.fetchone() is not None


# Function to save the attendance in the database
def save_attendance(user_id, device_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO attendance (user_id, device_id) VALUES (?, ?)",
            (user_id, device_id),
        )
        conn.commit()


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
