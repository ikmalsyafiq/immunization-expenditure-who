import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from scipy import stats

# Load the CSV file
df = pd.read_csv('cleaned_data_with_predictions.csv')
df["Year"] = pd.to_datetime(df["Year"], format='%Y').dt.strftime('%Y')

# Set the page title
st.title('Immunization Expenditure Prediction')

# Filter the data based on year, country, and prediction
years = st.multiselect('Select year(s)', df['Year'].unique(), default=df['Year'].unique())
all_countries = st.checkbox('Select all countries', value=True)
if all_countries:
    countries = df['Country'].unique()
else:
    countries = st.multiselect('Select country(ies)', df['Country'].unique())

all_predictions = st.checkbox('Select all predictions', value=True)
if all_predictions:
    predictions = df['prediction'].unique()
else:
    predictions = st.multiselect('Select prediction(s)', df['prediction'].unique())

filtered_df = df[df['Year'].isin(years) & df['Country'].isin(countries) & df['prediction'].isin(predictions)]

# Detect outlier country based on mape column
df_out = filtered_df.dropna(subset=['mape'])
z_scores = np.abs(stats.zscore(df_out['mape']))
threshold = 1
outliers = df_out[(z_scores > threshold) | (z_scores < -threshold)]

# Display the outlier country if exists
if not outliers.empty:
    st.subheader("Outlier Countries")
    st.dataframe(outliers[["Country", "Year", "mape"]].reset_index(drop=True))

# Allow the user to choose which columns to show in the data table
default_columns = ['Country', 'Year', 'Immunization USD Mil', 'Immunization USD Mil_predicted', 'mape', 'prediction']
columns = st.multiselect('Select column(s) to display', options=filtered_df.columns, default=default_columns)

# Display the filtered data in a table with the selected columns
st.subheader('Data Table')
st.dataframe(filtered_df[columns])

# Allow the user to choose which type of plot to display
plot_types = ('Scatter Plot', 'Bar Chart', 'Line Chart', 'Box Plot')
default_plot_type = 'Scatter Plot'
plot_type = st.selectbox('Select a plot type', options=plot_types, index=plot_types.index(default_plot_type))

# Allow the user to choose which columns to show in the plot
default_x_column = 'Immunization USD Mil'
default_y_column = 'Immunization USD Mil_predicted'
x_column = st.selectbox('Select a column for the x-axis', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_x_column))
y_column = st.selectbox('Select a column for the y-axis', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_y_column))

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
