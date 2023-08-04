import jwt
import datetime

# Your secret key for signing the token (make sure to keep this secret in a real application)
SECRET_KEY = "ZYPSIE"

# Sample user data (you can replace this with data for your specific user)
user_data = {
    "user_id": 1,
    "name": "John Doe",
    "semester": "Spring 2023",
    "faculty": "Computer Science",
}


# Function to generate a JWT token
def generate_jwt_token(user_data):
    # Set the token expiration time (adjust as needed)
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    # Create the payload for the token
    payload = {
        "user_id": user_data["user_id"],
        "name": user_data["name"],
        "semester": user_data["semester"],
        "faculty": user_data["faculty"],
        "exp": expiration_time,
    }

    # Generate the token using the payload and the secret key
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256").decode("utf-8")

    return token


# Call the function to generate the token
fake_token = generate_jwt_token(user_data)

# Print the generated token
print(fake_token)
