import streamlit as st
from reportlab.pdfgen import canvas
import pandas as pd
import time
import cv2
import os
from st_main import load_saved_m, finding_bb_df, calculate_growth_areas, plot_img_with_bb
from zipfile import ZipFile
from PIL import Image

plot_info_df = pd.read_excel('plot_info.xlsx')

plot_name_options = list(plot_info_df['Block No.'])
plot_info_df['Date of Planting'] = pd.to_datetime(plot_info_df['Date of Planting'])
plot_info_df['Crop age'] = (pd.Timestamp('today') - plot_info_df['Date of Planting']).dt.days

def generate_pdf(location, crop_variety, plot_name, area, planting_date, crop_age):
    pdf_path = "output.pdf"
    c = canvas.Canvas(pdf_path)
    c.setPageSize((600,780))
    c.drawImage("arpn.png", 0, 650, width=700, height=150)
    text_x = 50
    text_y = 620
    value_offset = 300
    lv_spacing = 150

    fields = [("Location", location),("Plot Name/Code", plot_name),
               ("Date of Planting", planting_date),("Crop Variety", crop_variety),
               ("Area", f"{area} Ha"),("Current Crop Age", f"{crop_age} days")]

    c.setFillColorRGB(0, 0, 0)
    c.rect(text_x-10 , text_y-190 , value_offset + lv_spacing + 80, len(fields) * 35 + 10, fill=0)

    for i, (label, value) in enumerate(fields):
        c.drawString(text_x if i < 3 else text_x + value_offset, text_y - (i % 3 * 60), f"{label}")
        c.drawString(text_x + lv_spacing if i < 3 else text_x + value_offset+lv_spacing, text_y - (i % 3 * 60), str(value))
    
    c.save()

def main():
    st.title('Crop and Weed Growth Prediction')
    link = 'Step 1: Orthophoto creation [Link to WebODM](http://102.90.2.78:8000/welcome)'
    st.markdown(link, unsafe_allow_html=True)
    st.markdown("Step 2: Fill in Blcok Information")
    st.markdown("Location")
    location = st.text_input("", "Farm B", key="location", disabled=True, label_visibility="collapsed")
    st.markdown("Crop Variety")
    crop_variety = st.text_input("", "TME 419", key="crop_variety", disabled=True, label_visibility="collapsed")
    st.markdown("Plot Name/Code")
    plot_name = st.selectbox("", plot_name_options, key="plot_name", label_visibility="collapsed")
    area_input = str(plot_info_df.loc[plot_info_df['Block No.'] == plot_name, 'Area (in Ha)'].values[0])
    st.markdown("Plot Area (in Ha)")
    area = st.text_input("", f"{area_input}", disabled=True, label_visibility="collapsed")
    st.markdown("Date of Planting")
    planting_datetime = str(plot_info_df.loc[plot_info_df['Block No.'] == plot_name, 'Date of Planting'].values[0])
    planting_date_input = pd.to_datetime(planting_datetime).strftime('%Y-%m-%d')
    planting_date = st.text_input("", f"{planting_date_input}", disabled=True, label_visibility="collapsed")
    st.markdown("Current crop age")
    crop_age_input = str(plot_info_df.loc[plot_info_df['Block No.'] == plot_name, 'Crop age'].values[0])
    crop_age = st.text_input("", f"{crop_age_input}", disabled=True, label_visibility="collapsed")
    st.markdown("Step 3: Crop neighboring block areas (if required)")
    st.markdown("Step 4: Upload Ortho for prediction")
    # File uploader
    uploaded_file = st.file_uploader('Upload ortho image', type=['tif'])

    if uploaded_file is not None:
        st.write('Upload successful!')
        st.markdown("Step 5: Start Prediction")
        # Generate PDF and download
        if st.button("Predict"):
            #with st.spinner('Generating PDF... Please wait'):
            with st.spinner('Prediction in progress... Please wait'):
                # Load model
                deepmodel_load = load_saved_m()               
                with open(uploaded_file.name, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                # Perform prediction
                box_df_mod = finding_bb_df(deepmodel_load, uploaded_file.name)

                # Read image
                read_new_image = cv2.imread(uploaded_file.name)
                img_height, img_width, channels = read_new_image.shape
                image_shape = (img_height, img_width, channels)
                label1_count = len(box_df_mod[box_df_mod['label'] == 'cassava'])
                # Calculate growth areas
                cassava_area, weed_area, percentage_weed_growth = calculate_growth_areas(box_df_mod, image_shape)

                # Display predicted image
                st.image(plot_img_with_bb(uploaded_file.name, box_df_mod, 102, label1_count, percentage_weed_growth),
                        caption='Predicted Image', use_column_width=True)

                # Display results
                st.write(f'Cassava Count: {label1_count}')
                st.write(f'Percentage Weed Growth: {percentage_weed_growth:.2f}%')
                f.close()
                generate_pdf(location, crop_variety, plot_name, area, planting_date, crop_age)

                with ZipFile('output.zip', 'w') as zipf:
                    # Add PDF to zip
                    zipf.write('output.pdf')

                    # Add predicted image to zip
                    img = Image.open(f"sample_output_102.jpg")
                    img.save('predicted_image.png')
                    zipf.write('predicted_image.png')
                    #st.success("Image attached!")
                with open('output.zip', 'rb') as f:
                    st.download_button("Download ZIP", f, file_name="output.zip")


# Call the main function
if __name__ == "__main__":
    main()
