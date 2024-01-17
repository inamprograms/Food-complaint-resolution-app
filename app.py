import streamlit as st
import os
from clarifai.client.model import Model
import cv2
from urllib.request import urlopen
import numpy as np
from clarifai.modules.css import ClarifaiStreamlitCSS
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(layout="wide")
st.title("Food Complaint Resolution System!")

# 1. Function to choose food item for complaint 
def chooseFoodItem():
    global selected_option
    st.subheader("Please select the item for which you want to raise the complaint:")
    options = ['Pita Gyro', 'Coke 250 ml', 'Choco chip cookie']
    selected_option = st.radio("Select an option:", options)
    st.write(f"You selected: {selected_option}")

# 2. Input description and food images from user
def takeComplaintImgs():
    
    st.subheader(f"Enter your complaint and upload the images of damaged {selected_option}:")
    description = st.text_area("Enter your complaint:")
    
    # Function to Read and Manupilate Image
    def load_image(img):
        im = Image.open(img)
        image = np.array(im)
        return image
    
    uploaded_file = st.file_uploader("Choose a image", type = ['jpg', 'png'])
    
    if uploaded_file is not None:   
        food_item_img = load_image(uploaded_file)
        st.image(food_item_img)
        st.write("Image Uploaded Successfully")
    else:
        st.write("Please upload the image in jpg or png formate")
        
def main():

    chooseFoodItem()    
    takeComplaintImgs()
    
    # Clarifai Credentials
    with st.sidebar:
        st.subheader('Add your Clarifai PAT.')
        clarifai_pat = st.text_input('Clarifai PAT:', type='password')
    if not clarifai_pat:
        st.warning('Please enter your PAT to continue!', icon='⚠️')
    else:
        os.environ['CLARIFAI_PAT'] = clarifai_pat

        detector_model = Model("https://clarifai.com/clarifai/main/models/objectness-detector")

        prediction_response = detector_model.predict_by_url(IMAGE_URL, input_type="image")

        # Since we have one input, one output will exist here
        regions = prediction_response.outputs[0].data.regions

        model_url = "https://clarifai.com/openai/chat-completion/models/gpt-4-vision"
        classes = ['Ferrari 812', 'Volkswagen Beetle', 'BMW M5', 'Honda Civic']
        threshold = 0.99

        req = urlopen(IMAGE_URL)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)  # 'Load it as it is'

        for region in regions:
            # Accessing and rounding the bounding box values
            top_row = round(region.region_info.bounding_box.top_row, 3)
            left_col = round(region.region_info.bounding_box.left_col, 3)
            bottom_row = round(region.region_info.bounding_box.bottom_row, 3)
            right_col = round(region.region_info.bounding_box.right_col, 3)

            for concept in region.data.concepts:
                # Accessing and rounding the concept value
                prompt = f"Label the Car in the Bounding Box region: ({top_row}, {left_col}, {bottom_row}, {right_col}) with one word {classes}"

                inference_params = dict(temperature=0.2, max_tokens=100, image_url=IMAGE_URL)

                # Model Predict
                model_prediction = Model(model_url).predict_by_bytes(prompt.encode(), input_type="text", inference_params=inference_params)

                concept_name = model_prediction.outputs[0].data.text.raw
                value = round(concept.value, 4)

                if value > threshold:
                    # Multipy by axis
                    top_row = top_row * img.shape[0]
                    left_col = left_col * img.shape[1]
                    bottom_row = bottom_row * img.shape[0]
                    right_col = right_col * img.shape[1]

                    cv2.rectangle(img, (int(left_col), int(top_row)), (int(right_col), int(bottom_row)), (36, 255, 12), 2)

                    # Display text
                    cv2.putText(img, concept_name, (int(left_col), int(top_row - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                    (36, 255, 12), 2)

        st.image(img, caption='Image with Label', channels='BGR', use_column_width=True)

if __name__ == '__main__':
    main()
