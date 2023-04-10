import streamlit as st
import pandas as pd
import plotly.express as px


# Load the CSV file
df = pd.read_csv('cleaned_data_with_predictions.csv')

# Set the page title
st.title('Immunization Expenditure Prediction')

# Set the background color by modifying the style attribute of the root element, body
st.markdown(
    """
    <style>
    body {
        background-color: #0B3C5D;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Filter the data based on year and country
years = st.multiselect('Select year(s)', df['Year'].unique())
all_countries = st.checkbox('Select all countries')
if all_countries:
    countries = df['Country'].unique()
else:
    countries = st.multiselect('Select country(ies)', df['Country'].unique())

filtered_df = df[df['Year'].isin(years) & df['Country'].isin(countries)]

# Allow the user to choose which columns to show in the data table
columns = st.multiselect('Select column(s) to display', options=filtered_df.columns)

# Display the filtered data in a table with the selected columns
st.subheader('Data Table')
st.dataframe(filtered_df[columns])

# Allow the user to choose which type of plot to display
plot_type = st.selectbox('Select a plot type', ('Scatter Plot', 'Bar Chart', 'Line Chart', 'Box Plot'))

# Allow the user to choose which columns to show in the plot
x_column = st.selectbox('Select a column for the x-axis', options=filtered_df.columns)
y_column = st.selectbox('Select a column for the y-axis', options=filtered_df.columns)

# Format the subheader text with the selected column names
subheader_text = f'{plot_type} ({x_column} vs. {y_column})'
st.subheader(subheader_text)

# Display the selected type of plot with the selected columns
if plot_type == 'Scatter Plot':
    fig = px.scatter(filtered_df, x=x_column, y=y_column)
elif plot_type == 'Bar Chart':
    fig = px.bar(filtered_df, x=x_column, y=y_column)
elif plot_type == 'Line Chart':
    fig = px.line(filtered_df, x=x_column, y=y_column)
else:
    fig = px.box(filtered_df, x=x_column, y=y_column)
    
st.plotly_chart(fig)
