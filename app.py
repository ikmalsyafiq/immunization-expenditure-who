import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from scipy import stats
import pycountry
from sklearn.metrics import r2_score

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
median_mape = round(df['mape'].median(), 0)
r2 = round(r2_score(df['Immunization USD Mil'], df['Immunization USD Mil_predicted']),2)
r2_100 = r2*100

st.markdown(f"""This is visualization for total immunization expenditure prediction. We based our prediction on
previous years total immunization cost, immunization coverage, land area and population.""") 

st.markdown(f"""Our 
mean absolute percentage error for our prediction is {mean_mape}%. This is high due to the outlier countries. However our
median absolute percentage error for our prediction is {median_mape}%.""")

st.markdown(f"""Our R2 Score is {r2}, means that 72% of the 
variability in the dependent variable (i.e., the variable being predicted by the model)
can be explained by the independent variables (i.e., the variables used to make the prediction)
in the regression model. In other words, the model explains {r2_100}% of the variation
in the data, and the remaining {100-r2_100}% of the variation is unexplained.""")

st.markdown(f"""{output_str}""")
            
# Filter the data based on year, country, and prediction
years = st.multiselect('Select year(s)', df['Year'].unique(), default=[df['Year'].max()])
all_countries = st.checkbox('Select all countries', value=True)
if all_countries:
    countries = df['Country'].unique()
else:
    countries = st.multiselect('Select country(ies)', df['Country'].unique())

st.markdown("""Using a higher threshold will result in fewer 
outliers being detected, while using a lower threshold 
will result in more outliers being detected. """)
            
outlier_tresh = st.selectbox('Select outlier threshold', [ 1, 1.5, 2], index=1)


#filtered_df = df[df['Year'].isin(years) & df['Country'].isin(countries) & df['prediction'].isin(predictions)]
filtered_df = df[df['Year'].isin(years) & df['Country'].isin(countries)  ]
# Allow the user to choose which columns to show in the data table
default_columns = ['Country', 'Year', 'Immunization USD Mil', 'Immunization USD Mil_predicted', 'mape', 'prediction']
columns = st.multiselect('Select column(s) to display', options=filtered_df.columns, default=default_columns)

# Display the filtered data in a table with the selected columns
st.subheader('Data Table')
mean_mape_filt = round(filtered_df['mape'].mean(), 0)
median_mape_filt = round(filtered_df['mape'].median(), 0)
st.markdown(f"""Filtered data mean absolute percentage error is {mean_mape_filt}%
 and median absolute percentage error is {median_mape_filt}%.""")
st.dataframe(filtered_df[columns])

# Detect outlier country based on mape column
df_out = filtered_df.dropna(subset=['mape'])
q1 = df_out['mape'].quantile(0.25)
q3 = df_out['mape'].quantile(0.75)

iqr = q3 - q1
outliers = df_out[(df_out['mape'] < q1 - outlier_tresh*iqr) | (df_out['mape'] > q3 + outlier_tresh*iqr)]

# Display the outlier country if exists
if not outliers.empty:
    try:
        st.subheader("Outlier Countries")
        st.markdown("""These are the countries that are considered outliers based on their predicted total immunization cost.
         The outlier method we are using here is based on the interquartile range (IQR). 
         The IQR is a measure of variability that is defined as the
         difference between the third quartile (Q3) and the first quartile (Q1) of a dataset. 
         The IQR represents the spread of the middle 50% of the data and is less sensitive to 
         extreme values than other measures of variability such as the range or standard deviation.
         To detect outliers using the IQR method, we typically use a threshold of 1.5 times the IQR. 
         According to Tukey's rule for outlier detection, any data points that fall below Q1-1.5IQR
         or above Q3+1.5IQR are considered outliers.
        """)
        st.dataframe(outliers[["Country", "Year", 'Immunization USD Mil', 'Immunization USD Mil_predicted', "mape"]].reset_index(drop=True))

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