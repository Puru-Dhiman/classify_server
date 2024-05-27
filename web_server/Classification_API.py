from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import numpy as np
import requests
from keras._tf_keras.keras.applications import InceptionV3
from keras._tf_keras.keras.applications.inception_v3 import preprocess_input
from keras._tf_keras.keras.applications import imagenet_utils               #decode the predicted output
from keras._tf_keras.keras.preprocessing.image import img_to_array          #PIL->Numpy
from PIL import Image
from io import BytesIO                                                      #HTTP->Image stream

app = Flask(__name__)
api = Api(app)

#Load the pretrained model
pretrained_model = InceptionV3(weights="imagenet")

# Initialize mongo db client
client = MongoClient("mongodb://db:27017")

#create a db and a collection
db = client.ImageClassification
users = db["Users"]

def user_exists(username):
    if users.count_documents({"Username":username}) == 0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        #get the user data
        posted_data = request.get_json()

        username = posted_data["username"]
        password = posted_data["password"]

        #check if user exists in db already
        if user_exists(username):
            ret_json = {
                "message":"Username already exists",
                "status code":301
            }
            return jsonify(ret_json)
        
        #if user is new, hash the pwd
        hashed_pwd = bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())

        #add the new user in db
        users.insert_one({
            "Username":username,
            "Password":hashed_pwd,
            "Tokens":4 
        })

        ret_json = {
                "message":"You have successfully signed up for the API",
                "status code":200
            }
        return jsonify(ret_json)
    

def generate_ret_dict(message, status_code):
    ret_json = {
        "message":message,
        "status_code":status_code
    }
    return ret_json    
    
def verify_pwd(username, password):

    if not user_exists(username):
        return False

    hashed_pwd = users.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pwd) != hashed_pwd:
        return False
    else:
        return True

    
def verify_credentials(username, password):
    if not user_exists(username):
        return generate_ret_dict("Invalid Username", 301), True
    
    correct_pwd = verify_pwd(username, password)
    if not correct_pwd:
        return generate_ret_dict("Invalid Password", 302), True
 
    return None, False



class Classify(Resource):
    def post(self):
        
        #get user data
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["password"]
        url = posted_data["url"]

        #check the credentials & url
        ret_json, error = verify_credentials(username, password)
        if error:
            return jsonify(ret_json)

        #check token status
        available_tokens = users.find({"Username": username})[0]["Tokens"]
        if available_tokens <= 0:
            return jsonify(generate_ret_dict("Not enough tokens", 303))
        
        if not url:
            return jsonify(generate_ret_dict("URL not provided", 400))
        
        #preprocess
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img = img.resize((299,299))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        #Predict
        prediction = pretrained_model.predict(img_array)
        actual_prediction = imagenet_utils.decode_predictions(prediction, top=5)

        ret_json = {}
        for predict in actual_prediction[0]:
            ret_json[predict[1]] = float(predict[2]*100)
        

        #reduce token
        users.update_one(
            {
                "Username":username
            }, {
                "$set": {
                    "Tokens":available_tokens-1
                }
            }
        )

        return jsonify(ret_json)

class Refill(Resource):
    def post(self):
        #get admin data
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["admin password"]
        tokens_refill = posted_data["Amount"]

        #check user exists or not
        if not user_exists(username):
            return jsonify(generate_ret_dict("Invalid Username", 301))

        admin_pwd = "sting!123"
        if password != admin_pwd:
            return jsonify(generate_ret_dict("Invalid Admin Password", 302))
        
        users.update_one(
            {
                "Username":username
            }, {
                "$set": {
                    "Tokens": tokens_refill
                }
            }
        )

        return jsonify(generate_ret_dict("Tokens refilled", 200))


api.add_resource(Register, "/register")
api.add_resource(Classify, "/classify")
api.add_resource(Refill, "/refill")


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)