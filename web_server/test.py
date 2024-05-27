import numpy as np
import requests
from keras.applications import InceptionV3
from keras.applications.inception_v3 import preprocess_input
from keras.applications import imagenet_utils               #decode the predicted output
from keras.preprocessing.image import img_to_array          #PIL->Numpy
from PIL import Image
from io import BytesIO   

url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS7mnbQSNGvz-A0rGFwljLPsKqOL4PGOE8tDs0H8JjaDg&s"
#Load the pretrained model
pretrained_model = InceptionV3(weights="imagenet")

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

print(ret_json)