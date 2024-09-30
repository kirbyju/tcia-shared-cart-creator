import pandas as pd
import numpy as np
import streamlit as st
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import altair as alt
from tcia_utils import nbia
from tcia_utils import wordpress

@st.cache_data
def load_demographic_snapshot():
    df = pd.read_excel('tcia_demographics_snapshot.xlsx')

    ### add steps to incorporate any extra restricted or new data since load_demographic_snapshot
    # for new public data, get new series since snapshot date
    # for restricted data,
    #   create token
    #   get unique list of collections from excel
    #   get full list of collections from api
    #   download metadata for any missing restricted collections

    return df


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].str.contains(user_text_input)]

    return df

st.title("TCIA-Streamlit Cohort Builder")
st.write(
    """This app allows users to build a custom TCIA DICOM
    dataset using a combination of participant demographics
    and metadata from the images.
    Learn more about accessing TCIA datasets at https://www.cancerimagingarchive.net/access-data.
    """
)


### Load demographic data
demographics = load_demographic_snapshot()


st.title('Subject Demographics')

# Sidebar for filtering options
st.sidebar.header('Filter Options')
collection_filter = st.sidebar.multiselect('Select Collection', demographics['Collection'].unique())
sex_filter = st.sidebar.multiselect('Select Patient Sex', demographics['PatientSex'].unique())
ethnicity_filter = st.sidebar.multiselect('Select Patient Ethnicity', demographics['EthnicGroup'].unique())
species_filter = st.sidebar.multiselect('Select Species', demographics['SpeciesDescription'].unique())

# Apply filters to the dataframe
filtered_demographics = demographics
if collection_filter:
    filtered_demographics = filtered_demographics[filtered_demographics['Collection'].isin(collection_filter)]
if sex_filter:
    filtered_demographics = filtered_demographics[filtered_demographics['PatientSex'].isin(sex_filter)]
if ethnicity_filter:
    filtered_demographics = filtered_demographics[filtered_demographics['EthnicGroup'].isin(ethnicity_filter)]
if species_filter:
    filtered_demographics = filtered_demographics[filtered_demographics['SpeciesDescription'].isin(species_filter)]

# Calculate metrics
metrics = pd.DataFrame({
    'Metric': ['Patients', 'Studies', 'Series'],
    'Value': [
        filtered_demographics['PatientID'].nunique(),
        filtered_demographics['StudyInstanceUID'].nunique(),
        filtered_demographics['SeriesCount'].sum()
    ]
})

# Bar chart using Altair
st.subheader('Metrics Bar Chart')
chart = alt.Chart(metrics).mark_bar().encode(
    x='Metric',
    y='Value',
    tooltip=['Metric', 'Value']
)
st.altair_chart(chart, use_container_width=True)


# Display the filtered dataframe
st.write(filtered_demographics)


# Store collection_filter in session state
if 'collection_filter' not in st.session_state:
    st.session_state['collection_filter'] = []

# Update session state with current collection_filter
st.session_state['collection_filter'] = collection_filter

# Button to go to the next page
if st.button('Next Page'):
    series_data = pd.DataFrame()
    for collection in st.session_state['collection_filter']:
        series_data = pd.concat([series_data, nbia.getSeries(collection, format='df')])

    # Display the series data
    st.write(series_data)

    # Sidebar for filtering series_data
    st.sidebar.header('Series Data Filter Options')
    modality_filter = st.sidebar.multiselect('Select Modality', series_data['Modality'].unique())
    body_part_filter = st.sidebar.multiselect('Select Body Part', series_data['BodyPartExamined'].unique())

    # Apply filters to the series_data dataframe
    filtered_series_data = series_data
    if modality_filter:
        filtered_series_data = filtered_series_data[filtered_series_data['Modality'].isin(modality_filter)]
    if body_part_filter:
        filtered_series_data = filtered_series_data[filtered_series_data['BodyPartExamined'].isin(body_part_filter)]

    # Display the filtered series data
    st.write(filtered_series_data)

### import demographic results and allow further filtering
# st.dataframe(filter_dataframe(df))


### implement buttons to export manifest or download with API
