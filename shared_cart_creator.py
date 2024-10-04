import streamlit as st
import pandas as pd
import random
from tcia_utils import nbia

# Inject CSS to style for both light and dark mode
st.markdown(
    """
    <style>
    .stApp {
        background-color: #51A6FA;
    }
    .stAlert {
        background-color: #E9E9E9;
        color: black;
    }

    @media (prefers-color-scheme: dark) {
        .stAlert {
            background-color: #333333;
            color: white;
        }
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
st.image("https://www.cancerimagingarchive.net/wp-content/uploads/2021/06/TCIA-Logo-01.png", use_column_width=True)
st.title("Create Shared Cart")

# User login
st.sidebar.header('Login')
user = st.sidebar.text_input('Username')
pw = st.sidebar.text_input('Password', type='password')

# Input fields
name = st.text_input("Shared Cart Name", value=generate_random_name())
description = st.text_input("Shared Cart Description (optional)")
description_url = st.text_input("Shared Cart Description URL (optional)")

# Define the allowed file extensions
allowed_extensions = ['tcia', 'txt', 'xlsx', 'csv']  # Add other extensions as needed

# File uploader
uploaded_file = st.file_uploader("Upload TXT, CSV, XLSX, or TCIA manifest file containing your DICOM Series Instance UIDs.", type=allowed_extensions)

st.markdown("**Note:** If you upload a spreadsheet it will use the **SeriesInstanceUID** column if it exists, otherwise it will assume there are no headers and use the first column.")

if st.button("Create Shared Cart"):
    if uploaded_file is not None:
        series_list = []
        # create df based on file type
        if uploaded_file.name.endswith("xlsx"):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith("csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, delimiter="\t")
        # create uid list based on df contents
        if 'Series UID' in df.columns and 'SeriesInstanceUID' in df.columns:
            raise ValueError("Invalid spreadsheet: both 'Series UID' and 'SeriesInstanceUID' are present.")
        elif 'SeriesInstanceUID' in df.columns:
            series_list = df['SeriesInstanceUID'].tolist()
        elif 'Series UID' in df.columns:
            series_list = df['Series UID'].tolist()
        elif uploaded_file.name.endswith("tcia"):
            # drop config params and keep series list
            series_list = df.iloc[5:, 0].tolist()
        else:
            series_list = df.iloc[:, 0].tolist()
        # submit list for shared list creation
        try:
            nbia.getToken(user, pw)
            nbia.makeSharedCart(series_list, name, description, description_url)
            st.success(f"Shared Cart created successfully!\n\nhttps://nbia.cancerimagingarchive.net/nbia-search/?saved-cart={name}")
        except Exception as e:
            st.error(f"Failed to create Shared Cart: {str(e)}")
    else:
        st.error("Please upload a file.")
