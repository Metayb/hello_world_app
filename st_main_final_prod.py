import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.platypus import Image as im
import pandas as pd
import time
from datetime import date
import cv2
import os
from st_main import load_saved_m, finding_bb_df, calculate_growth_areas, plot_img_with_bb
from zipfile import ZipFile
from PIL import Image

plot_info_df = pd.read_excel('plot_info.xlsx')

plot_name_options = list(plot_info_df['Block No.'])
plot_info_df['Date of Planting'] = pd.to_datetime(plot_info_df['Date of Planting'])
plot_info_df['Crop age'] = (pd.Timestamp('today') - plot_info_df['Date of Planting']).dt.days

def generate_pdf(location, crop_variety, plot_name, area, planting_date, crop_age,cassava_c,weed_c):
    pdf_path = "output.pdf"
    c = canvas.Canvas(pdf_path)
    c.setPageSize((600,780))
    c.drawImage("arpn.png", 0, 650, width=700, height=150)
    text_x = 50
    text_y = 620
    value_offset = 300
    lv_spacing = 150

    p_text_x = 50
    p_text_y = 350


    fields = [("Location", location),("Plot Name/Code", plot_name),
               ("Date of Planting", planting_date),("Crop Variety", crop_variety),
               ("Area", f"{area} Ha"),("Current Crop Age", f"{crop_age} days")]
    
    yield_tons = cassava_c*0.0018
    plot_details = [("Analysis Date",date.today() ),
                    ("Area (Ha)", f"{area} Ha"),
                    ("Plant Count", f"{cassava_c}"),
                    ("Weed Growth (%)", f"{weed_c:.2f}%"),
                    ("Estimated Yield (Tons)", f"{yield_tons}")]

    c.setFillColorRGB(0, 0, 0)
    c.rect(text_x-10 , text_y-190 , value_offset + lv_spacing + 80, len(fields) * 35 + 10, fill=0)

    for i, (label, value) in enumerate(fields):
        c.drawString(text_x if i < 3 else text_x + value_offset, text_y - (i % 3 * 60), f"{label}")
        c.drawString(text_x + lv_spacing if i < 3 else text_x + value_offset+lv_spacing, text_y - (i % 3 * 60), str(value))
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(text_x, text_y - 250, "Plot Details: ")

    for i, (label, value) in enumerate(plot_details):
        c.drawString(p_text_x if i < 3 else p_text_x + value_offset, p_text_y - (i % 3 * 60) - 50, f"\U0001F340 {label}: {value}")
    
    c.save()




st.set_page_config(layout="wide")
title_image = r"Crop and weed growth Prediction.png"
st.image(title_image, use_column_width='auto')
def main():
    # st.set_page_config(layout="wide")
    # title_image = r"Crop and weed growth Prediction.png"
    # st.image(title_image, use_column_width='auto')
    #st.title('Crop and Weed Growth Prediction')
    link = '**STEP 1:** Orthophoto creation [Link to WebODM](http://41.216.170.117:8000/login/)'
    st.markdown(link, unsafe_allow_html=True)
    st.markdown("**STEP 2:** Fill in Block Information")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Plot Name/Code")
        plot_name = st.selectbox("", plot_name_options, key="plot_name", label_visibility="collapsed")

        st.markdown("Location")
        location = st.text_input("", "Farm B", key="location", disabled=True, label_visibility="collapsed")

        st.markdown("Crop Variety")
        crop_variety = st.text_input("", "TME 419", key="crop_variety", disabled=True, label_visibility="collapsed")

    with col2:
        st.markdown("Plot Area (in Ha)")
        area_input = str(plot_info_df.loc[plot_info_df['Block No.'] == plot_name, 'Area (in Ha)'].values[0])
        area = st.text_input("", f"{area_input}", disabled=True, label_visibility="collapsed")

        st.markdown("Date of Planting")
        planting_datetime = str(plot_info_df.loc[plot_info_df['Block No.'] == plot_name, 'Date of Planting'].values[0])
        planting_date_input = pd.to_datetime(planting_datetime).strftime('%Y-%m-%d')
        planting_date = st.text_input("", f"{planting_date_input}", disabled=True, label_visibility="collapsed")

        st.markdown("Current crop age")
        crop_age_input = str(plot_info_df.loc[plot_info_df['Block No.'] == plot_name, 'Crop age'].values[0])
        crop_age = st.text_input("", f"{crop_age_input}", disabled=True, label_visibility="collapsed")

    st.markdown("**STEP 3:**  Crop neighboring block areas (if required)")
    st.markdown("**STEP 4:**  Upload Ortho for prediction")
    # File uploader
    uploaded_file = st.file_uploader('Upload ortho image', type=['tif'])

    if uploaded_file is not None:
        st.write('Upload successful!')
        st.markdown("**STEP 5:** Start Prediction")
        # Generate PDF and download
        if st.button("Predict"):
            #with st.spinner('Generating PDF... Please wait'):
            with st.spinner('Prediction in progress... Take a break!!'):
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
                # label1_count = 1727
                # percentage_weed_growth = 19.27573574
                generate_pdf(location, crop_variety, plot_name, area, planting_date, crop_age,label1_count,percentage_weed_growth)

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



    # st.markdown("Location")
    # location = st.text_input("", "Farm B", key="location", disabled=True, label_visibility="collapsed")
    # st.markdown("Crop Variety")
    # crop_variety = st.text_input("", "TME 419", key="crop_variety", disabled=True, label_visibility="collapsed")
    # st.markdown("Plot Name/Code")
    # plot_name = st.selectbox("", plot_name_options, key="plot_name", label_visibility="collapsed")
    # area_input = str(plot_info_df.loc[plot_info_df['Block No.'] == plot_name, 'Area (in Ha)'].values[0])
    # st.markdown("Plot Area (in Ha)")
    # area = st.text_input("", f"{area_input}", disabled=True, label_visibility="collapsed")
    # st.markdown("Date of Planting")
    # planting_datetime = str(plot_info_df.loc[plot_info_df['Block No.'] == plot_name, 'Date of Planting'].values[0])
    # planting_date_input = pd.to_datetime(planting_datetime).strftime('%Y-%m-%d')
    # planting_date = st.text_input("", f"{planting_date_input}", disabled=True, label_visibility="collapsed")
    # st.markdown("Current crop age")
    # crop_age_input = str(plot_info_df.loc[plot_info_df['Block No.'] == plot_name, 'Crop age'].values[0])
    # crop_age = st.text_input("", f"{crop_age_input}", disabled=True, label_visibility="collapsed")