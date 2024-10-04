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

# tcia logo
st.image("https://www.cancerimagingarchive.net/wp-content/uploads/2021/06/TCIA-Logo-01.png", use_column_width=True)

# Streamlit app
st.title("Create Shared Cart")

# User login
st.sidebar.header('Login (optional)')
st.sidebar.markdown("Enter credentials before pressing 'Create Shared Cart' if your dataset contains restricted series.")
user = st.sidebar.text_input('Username')
pw = st.sidebar.text_input('Password', type='password')

st.markdown("If you upload a spreadsheet it will search for **Series UID** or **SeriesInstanceUID** column headers and use that column, otherwise it will assume there are no headers and use the first column.")

st.markdown("If you upload a text file, it should be one Series Instance UID per line.")

# Input fields
name = st.text_input("**Shared Cart Name** -- This can be customized, but must be a unique name that nobody else has used previously.", value=generate_random_name())
description = st.text_input("Shared Cart Description (optional)")
description_url = st.text_input("Shared Cart Description URL (optional)")

# Define the allowed file extensions
allowed_extensions = ['tcia', 'txt', 'xlsx', 'csv']  # Add other extensions as needed

# File uploader
uploaded_file = st.file_uploader("Upload TXT, CSV, XLSX, or TCIA manifest file containing your DICOM Series Instance UIDs.", type=allowed_extensions)

if st.button("Create Shared Cart"):
    if uploaded_file is not None:
        try:
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
                st.error("Invalid spreadsheet: both 'Series UID' and 'SeriesInstanceUID' are present.")
            elif 'SeriesInstanceUID' in df.columns:
                series_list = df['SeriesInstanceUID'].tolist()
            elif 'Series UID' in df.columns:
                series_list = df['Series UID'].tolist()
            elif uploaded_file.name.endswith("tcia"):
                # drop config params and keep series list
                series_list = df.iloc[5:, 0].tolist()
            else:
                series_list = df.iloc[:, 0].tolist()

            # Attempt login if user provided credentials
            if user and pw:
                token_status = nbia.getToken(user, pw)
                if token_status != 200:
                    st.error(f"Login failed: Status code {token_status}. Check your credentials.")
                    st.stop()

            # Attempt to create the cart
            result = nbia.makeSharedCart(series_list, name, description, description_url)
            # Handle result status codes
            if result == 200:
                st.success(f"Shared Cart created successfully!\n\nhttps://nbia.cancerimagingarchive.net/nbia-search/?saved-cart={name}")
            elif result == 400:
                st.error("There was an issue with your request. Possible reasons: permission issues (try logging in!), bad formatting (see guidance above) or invalid Series UID.")
            elif result == 401:
                st.error("Unauthorized. Please check your login credentials.")
            elif result == 403:
                st.error("Access denied. Your account does not have permission to access some of the requested data.")
            elif result == 404:
                st.error("Resource not found. One or more Series UIDs may be invalid.")
            elif result == 408:
                st.error("Request timed out. Please try again.")
            elif result == 502:
                st.error("Connection error. Unable to reach the server. Please try again later.")
            else:
                st.error(f"Unknown error. Status code: {result}")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
