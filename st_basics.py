import streamlit as st

# Title
st.title('My First Streamlit App')

# Header/Subheader
st.header('This is a header')
st.subheader('This is a subheader')

# Text
st.text('This is some text.')

# Markdown
st.markdown('**This** is some *markdown*.')

# Button
if st.button('Click me!'):
    st.write('Button clicked!')

# Checkbox
checkbox_state = st.checkbox('Check me out')
if checkbox_state:
    st.write('Checkbox is checked!')

# Selectbox
option = st.selectbox('Select a number', range(1, 11))
st.write('You selected:', option)

# Slider
slider_value = st.slider('Select a value', 0.0, 100.0, 50.0)
st.write('Slider value:', slider_value)

# Text input
text_input = st.text_input('Enter some text')
st.write('You entered:', text_input)

# File uploader
uploaded_file = st.file_uploader('Upload a file')
if uploaded_file is not None:
    st.write('File uploaded!')

# Date input
import datetime
today = st.date_input('Today is', datetime.datetime.now())

# Time input
appointment = st.time_input('Your appointment is at')

# Color picker
color = st.color_picker('Pick a color', '#00f900')
st.write('The selected color is', color)
