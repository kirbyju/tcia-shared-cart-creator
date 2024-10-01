import streamlit as st
import pandas as pd
import random
from tcia_utils import nbia

# Display the banner image
st.image("https://www.cancerimagingarchive.net/wp-content/uploads/2021/06/TCIA-Logo-01.png", use_column_width=True)

# Inject CSS to style the background image
st.markdown(
    """
    <style>
    .stApp {
        background-color: #51A6FA;
    }
    .stAlert {
        background-color: #E9E9E9;
        color: #FFFFFF; /* White text */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to generate a random name
def generate_random_name():
    random_numbers = ''.join([str(random.randint(0, 9)) for _ in range(18)])
    return f"nbia-{random_numbers}"

# Streamlit app
st.title("Create Shared Cart")

# Input fields
name = st.text_input("Shared Cart Name", value=generate_random_name())
description = st.text_input("Shared Cart Description (optional)")
description_url = st.text_input("Shared Cart Description URL (optional)")

# File uploader
uploaded_file = st.file_uploader("Upload TXT, CSV or XLSX file of DICOM Series Instance UIDs.", type=["csv", "xlsx", "txt"])

st.markdown("**Note:** If you upload a spreadsheet it will use the **SeriesInstanceUID** column if it exists, otherwise it will assume there are no headers and use the first column.")

if st.button("Create Shared Cart"):
    if uploaded_file is not None:
        # Read the file into a DataFrame
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, delimiter="\t")

        # Check for 'SeriesInstanceUID' column
        if 'SeriesInstanceUID' in df.columns:
            series_list = df['SeriesInstanceUID'].tolist()
        else:
            series_list = df.iloc[:, 0].tolist()  # Assuming the UIDs are in the first column

        # Call the makeSharedCart function
        try:
            nbia.makeSharedCart(series_list, name, description, description_url)

            st.success(f"Shared Cart created successfully!\n\nhttps://nbia.cancerimagingarchive.net/nbia-search/?saved-cart={name}")
            #st.markdown(f"https://nbia.cancerimagingarchive.net/nbia-search/?saved-cart={name}")
        except Exception as e:
            st.error(f"Failed to create Shared Cart: {str(e)}")
    else:
        st.error("Please upload a file.")
