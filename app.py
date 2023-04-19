import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from scipy import stats
import pycountry

def get_country_iso_alpha3(country_name):
    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except:
        return None

# Load the CSV file
df = pd.read_csv('cleaned_data_with_predictions.csv')
df["Year"] = pd.to_datetime(df["Year"], format='%Y').dt.strftime('%Y')



# Add ISO country codes to the dataset
df['iso_alpha'] = df['Country'].apply(get_country_iso_alpha3)

# Grouping the DataFrame by Year and Country to aggregate the predicted countries
grouped_df = df.groupby(['Year']).agg({'Country': pd.Series.nunique})

# Initializing an empty string to hold the output
output_str = ""

count = 0
# Looping through each unique year to add the number of unique countries predicted to the output string
for year, num_countries in grouped_df.iterrows():
    output_str += "In year " + str(year) + ", we predicting " + str(num_countries['Country']) + " countries. "

# Printing the output string

# Set the page title
st.title('Total Immunization Expenditure Prediction')
mean_mape = round(df['mape'].mean(), 0)
st.markdown(f"""This is visualization for total immunization expenditure prediction. We based our prediction on
immunization coverage, land area, population, vaccine cost, total vaccine cost, and government immunization cost. Our 
mean absolute percentage error for our prediction is {mean_mape}%. {output_str}""")
            



# Filter the data based on year, country, and prediction
years = st.multiselect('Select year(s)', df['Year'].unique(), default=[df['Year'].max()]))
all_countries = st.checkbox('Select all countries', value=True)
if all_countries:
    countries = df['Country'].unique()
else:
    countries = st.multiselect('Select country(ies)', df['Country'].unique())

outlier_tresh = st.selectbox('Select outlier threshold', [0.5, 1, 1.5, 2, 2.5, 3], index=1)
# Detect outlier country based on mape column
df_out_pre = df.dropna(subset=['mape'])
z_scores_pre = np.abs(stats.zscore(df_out_pre['mape']))
threshold = outlier_tresh
outliers_pre = df_out_pre[(z_scores_pre > threshold) | (z_scores_pre < -threshold)]

df['is_outlier'] = df.index.isin(outliers_pre.index)
df['is_outlier'] = df['is_outlier'].apply(lambda x: 'Yes' if x else 'No')


outlier_check = st.checkbox('Exclude outlier', value=False)
if outlier_check:
    ex_outlier = ['No']
else:
    ex_outlier = ['Yes','No']
# all_predictions = st.checkbox('Select all predictions', value=True)
# if all_predictions:
#     predictions = df['prediction'].unique()
# else:
#     predictions = st.multiselect('Select prediction(s)', df['prediction'].unique())

#filtered_df = df[df['Year'].isin(years) & df['Country'].isin(countries) & df['prediction'].isin(predictions)]
filtered_df = df[df['Year'].isin(years) & df['Country'].isin(countries) & df['is_outlier'].isin(ex_outlier) ]
# Allow the user to choose which columns to show in the data table
default_columns = ['Country', 'Year', 'Immunization USD Mil', 'Immunization USD Mil_predicted', 'mape', 'prediction']
columns = st.multiselect('Select column(s) to display', options=filtered_df.columns, default=default_columns)

# Display the filtered data in a table with the selected columns
st.subheader('Data Table')
mean_mape_filt = round(filtered_df['mape'].mean(), 0)
st.markdown(f"""Filtered data mean absolute percentage error is {mean_mape_filt}%""")
st.dataframe(filtered_df[columns])

# Detect outlier country based on mape column
df_out = filtered_df.dropna(subset=['mape'])
z_scores = np.abs(stats.zscore(df_out['mape']))
if outlier_check:
    threshold = 1000000
else:
    threshold = outlier_tresh
outliers = df_out[(z_scores > threshold) | (z_scores < -threshold)]

# Display the outlier country if exists
if not outliers.empty:
    try:
        st.subheader("Outlier Countries")
        st.markdown("""These are the countries that are considered outliers due to their predicted total immunization cost over 1 standard deviation in the Z-score scale.
        In other words, outliers with Z-scores over 1 standard deviation are values that are much 
        further away from the typical values in a dataset, and may warrant further investigation to understand why they differ so much.
        """)
        st.dataframe(outliers[["Country", "Year", 'Immunization USD Mil', 'Immunization USD Mil_predicted', "mape",'is_outlier']].reset_index(drop=True))

        st.subheader('Choropleth Map for Outlier Countries')
        value_col_options = filtered_df.columns
        default_x_column = 'mape'
        value_col_outliers = st.selectbox('Select a value column', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_x_column))
        fig_outliers = px.choropleth(outliers, locations='iso_alpha', color=value_col_outliers, hover_name='Country',hover_data=['Immunization USD Mil', 'Immunization USD Mil_predicted', 'mape'], projection='natural earth', title=f'{value_col_outliers} by Outlier Country')
        st.plotly_chart(fig_outliers)
    except:
        mm = True

st.subheader('Self Service Visualization')
st.markdown("""Choose from Choropleth Map, Scatter Plot, Bar Chart, Line Chart and Box Plot to 
visualize immunization data.""")
            
# Allow the user to choose which type of plot to display
plot_types = ('Choropleth Map', 'Scatter Plot', 'Bar Chart', 'Line Chart', 'Box Plot')
default_plot_type = 'Choropleth Map'
plot_type = st.selectbox('Select a plot type', options=plot_types, index=plot_types.index(default_plot_type))


# Display the selected type of plot with the selected columns
if plot_type == 'Choropleth Map':
    st.subheader('Choropleth Map')
    value_col_options = filtered_df.columns
    default_x_column = 'Immunization USD Mil'
    value_col = st.selectbox('Select a value column',options=filtered_df.columns, index=filtered_df.columns.get_loc(default_x_column))
    fig = px.choropleth(filtered_df, locations='iso_alpha', color=value_col, hover_name='Country', projection='natural earth', title=f'{value_col} by Country')
    #st.plotly_chart(fig)
elif plot_type == 'Scatter Plot':
    default_x_column = 'Immunization USD Mil'
    default_y_column = 'Immunization USD Mil_predicted'
    x_column = st.selectbox('Select a column for the x-axis', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_x_column))
    y_column = st.selectbox('Select a column for the y-axis', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_y_column))

    # Format the subheader text with the selected column names
    subheader_text = f'{plot_type} ({x_column} vs. {y_column})'
    st.subheader(subheader_text)

    fig = px.scatter(filtered_df, x=x_column, y=y_column,hover_data=['Country','Year','Immunization USD Mil', 'Immunization USD Mil_predicted', 'mape'])

elif plot_type == 'Bar Chart':
    default_x_column = 'Immunization USD Mil'
    default_y_column = 'Immunization USD Mil_predicted'
    x_column = st.selectbox('Select a column for the x-axis', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_x_column))
    y_column = st.selectbox('Select a column for the y-axis', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_y_column))

    # Format the subheader text with the selected column names
    subheader_text = f'{plot_type} ({x_column} vs. {y_column})'
    st.subheader(subheader_text)

    fig = px.bar(filtered_df, x=x_column, y=y_column,hover_data=['Country','Year','Immunization USD Mil', 'Immunization USD Mil_predicted', 'mape'])

elif plot_type == 'Line Chart':
    default_x_column = 'Immunization USD Mil'
    default_y_column = 'Immunization USD Mil_predicted'
    x_column = st.selectbox('Select a column for the x-axis', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_x_column))
    y_column = st.selectbox('Select a column for the y-axis', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_y_column))
    # Format the subheader text with the selected column names
    subheader_text = f'{plot_type} ({x_column} vs. {y_column})'
    st.subheader(subheader_text)

    fig = px.line(filtered_df, x=x_column, y=y_column,hover_data=['Country','Year','Immunization USD Mil', 'Immunization USD Mil_predicted', 'mape'])

else: # Box Plot
    default_x_column = 'Immunization USD Mil'
    default_y_column = 'Immunization USD Mil_predicted'
    x_column = st.selectbox('Select a column for the x-axis', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_x_column))
    y_column = st.selectbox('Select a column for the y-axis', options=filtered_df.columns, index=filtered_df.columns.get_loc(default_y_column))
    # Format the subheader text with the selected column names
    subheader_text = f'{plot_type} ({x_column} vs. {y_column})'
    st.subheader(subheader_text)

    fig = px.box(filtered_df, x=x_column, y=y_column,hover_data=['Country','Year','Immunization USD Mil', 'Immunization USD Mil_predicted', 'mape'])

st.plotly_chart(fig)