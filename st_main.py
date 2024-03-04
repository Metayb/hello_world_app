import streamlit as st
import cv2
import pandas as pd
import os
import time
import numpy as np
from deepforest import main
import tempfile

def load_saved_m():
  model_after = main.deepforest.load_from_checkpoint("./chkpt25_01032024.pl")
  return model_after

def plot_img_with_bb(raster_path,box_df,num,label1_count,weed_percentage):
    original_image = cv2.imread(raster_path)
    for index, row in box_df.iterrows():
        xmin, ymin, xmax, ymax = map(int, [row['xmin'], row['ymin'], row['xmax'], row['ymax']])
        label = row['label']
        #color = (0, 165, 255)
        color = get_label_color(label)
        thickness = 1
        cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), color, thickness)
        cv2.putText(original_image, f"{label}", (xmin, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)

    cv2.putText(original_image, f"Cassava Count: {label1_count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX,3 , (255, 255, 255), 3)
    cv2.putText(original_image, f"Weed %: {weed_percentage:.2f}%", (60, 120), cv2.FONT_HERSHEY_SIMPLEX,3 , (255, 255, 255), 3)
    output_path = f"newplot/newplot_output/sample_output_{num}.jpg"#new_images_output_Y1
    cv2.imwrite(output_path, original_image)
    print(f"Image with bounding boxes saved at: {output_path}")
    return

def get_label_color(label):
    # Define a dictionary mapping labels to colors
    label_colors = {'cassava': (0, 255, 0),  # Green
                    'weed': (0, 0, 255),  # Red
                    }
    return label_colors.get(label, (255, 255, 255))


def predict_(m,new_image_name):
    patch_size = 100
    patch_overlap = 0
    iou_threshold=0.05
    box_df = m.predict_tile(new_image_name, return_plot=False, patch_size=patch_size, patch_overlap=patch_overlap)
    return box_df

def finding_bb_df(deepmodel_load,image_to_predict):
  box_df = predict_(deepmodel_load,image_to_predict)
  print('box_df: cassava',len(box_df[box_df['label']=='cassava']))
  print('box_df: weed',len(box_df[box_df['label']=='weed']))
  #box_df_mod = box_df[box_df["score"]>0.2]
  box_df_mod = box_df
  print('box_df_mod: cassava',len(box_df_mod[box_df_mod['label']=='cassava']))
  print('box_df_mod: weed',len(box_df_mod[box_df_mod['label']=='weed']))
  return box_df_mod

def calculate_area(bbox):
    # Calculate area based on bounding box coordinates
    return (bbox['xmax'] - bbox['xmin']) * (bbox['ymax'] - bbox['ymin'])

def calculate_growth_areas(df, image_shape):
    total_image_area = image_shape[0] * image_shape[1]  # height * width

    cassava_area = 0
    weed_area = 0

    for index, row in df.iterrows():
        label = row['label']
        area = calculate_area(row)

        if label == 'cassava':
            cassava_area += area
        elif label == 'weed':
            weed_area += area

    # Calculate percentage of weed growth
    percentage_weed_growth = (weed_area / total_image_area) * 100

    return cassava_area, weed_area, percentage_weed_growth

def main():
    st.title('Crop and Weed Growth Prediction')

    # File uploader
    uploaded_file = st.file_uploader('Upload an image', type=['tif'])

    if uploaded_file is not None:
        print('upload successful!')
        # Load model
        deepmodel_load = load_saved_m()

        # Perform prediction
        box_df_mod = finding_bb_df(deepmodel_load, uploaded_file)

        # Read image
        read_new_image = cv2.imread(uploaded_file.name)
        img_height, img_width, channels = read_new_image.shape
        image_shape = (img_height, img_width, channels)

        # Calculate growth areas
        cassava_area, weed_area, percentage_weed_growth = calculate_growth_areas(box_df_mod, image_shape)

        # Display predicted image
        st.image(plot_img_with_bb(uploaded_file.name, box_df_mod, 102), caption='Predicted Image', use_column_width=True)

        # Display results
        st.write(f'Percentage Weed Growth: {percentage_weed_growth}%')

if __name__ == '__main__':
    main()
