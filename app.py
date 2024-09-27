import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

import geopandas as gpd
import plotly.express as px
import json
import pandas as pd

# Initialize the Dash app with Bootstrap theme and suppress callback exceptions
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True  # Allows callbacks for dynamically generated components
)
server = app.server

app.title = "NC Health Insights Dashboard"  # Updated Title

# Server for deployment (if needed)
server = app.server

# ---------------------------
# Define Health Categories
# ---------------------------

# Define health categories and associated variables
health_categories = {
    "Economic Stability": [
        "Median Household Income",
        "Gender Pay Gap",
        "Income Ratio",
        "% Unemployed",
        "% Household Income Required for Child Care Expenses",
        "% Households with Severe Cost Burden",
        "% Households with Broadband Access",
        "% Homeowners"
    ],
    "Education Access and Quality": [
        "% Completed High School",
        "% Some College",
        "High School Graduation Rate",
        "Average Grade Performance Reading",
        "Average Grade Performance Math",
        "% Enrolled in Free or Reduced Lunch",
        "% Not Proficient in English"
    ],
    "Health Care Access and Quality": [
        "% Uninsured",
        "% Uninsured Adults",
        "% Uninsured Children",
        "Primary Care Physicians Rate",
        "Dentist Rate",
        "Mental Health Provider Rate",
        "Other Primary Care Provider Rate",
        "Preventable Hospitalization Rate",
        "% with Annual Mammogram",
        "% Flu Vaccinated",
        "% Adults with Diabetes",
        "HIV Prevalence Rate",
        "% Adults Reporting Currently Smoking",
        "% Adults with Obesity",
        "% Excessive Drinking",
        "% Physically Inactive",
        "% Insufficient Sleep"
    ],
    "Neighborhood and Built Environment": [
        "Food Environment Index",
        "% With Access to Exercise Opportunities",
        "% Limited Access to Healthy Foods",
        "% Food Insecure",
        "Average Daily PM2.5",
        "Presence of Water Violation",
        "% Severe Housing Problems",
        "Severe Housing Cost Burden",
        "Overcrowding",
        "Inadequate Facilities",
        "% Drive Alone to Work",
        "% Long Commute - Drives Alone",
        "Traffic Volume",
        "% Rural",
        "% Housing Units with Broadband Access"
    ],
    "Social and Community Context": [
        "Social Association Rate",
        "Segregation Index",
        "Residential Segregation Index",
        "% Voter Turnout",
        "% Census Participation",
        "% Black",
        "% American Indian or Alaska Native",
        "% Asian",
        "% Native Hawaiian or Other Pacific Islander",
        "% Hispanic",
        "% Non-Hispanic White",
        "% Female"
    ],
    "Health Outcomes": [
        "Years of Potential Life Lost Rate",
        "% Fair or Poor Health",
        "Life Expectancy",
        "Child Mortality Rate",
        "Infant Mortality Rate",
        "Suicide Rate (Age-Adjusted)",
        "Homicide Rate",
        "Firearm Fatalities Rate",
        "Motor Vehicle Mortality Rate",
        "Drug Overdose Mortality Rate",
        "Age-Adjusted Death Rate"
    ],
    "Behavioral Factors": [
        "% Adults Reporting Currently Smoking",
        "% Adults with Obesity",
        "% Physically Inactive",
        "% Excessive Drinking",
        "% Insufficient Sleep",
        "% Adults with Diabetes",
        "Mental Health Provider Rate"
    ]
}

# ---------------------------
# Data Loading and Processing
# ---------------------------

# Initialize GeoDataFrame and GeoJSON
merged_nc = gpd.GeoDataFrame()
merged_geojson = {}
featureidkey = 'properties.County'  # Default featureidkey

try:
    # Load the GeoJSON file named 'merged_nc.geojson'
    merged_nc = gpd.read_file('merged_nc.geojson')
    print("GeoJSON file 'merged_nc.geojson' loaded successfully.")
except FileNotFoundError:
    print("Error: GeoJSON file 'merged_nc.geojson' not found. Please check the file path.")
except Exception as e:
    print(f"Error loading GeoJSON: {e}")

# Proceed only if GeoDataFrame is not empty
if not merged_nc.empty:
    # Ensure CRS is WGS84
    if merged_nc.crs != "EPSG:4326":
        merged_nc = merged_nc.to_crs(epsg=4326)
        print("CRS converted to EPSG:4326.")

    # Simplify geometry for performance
    try:
        merged_nc['geometry'] = merged_nc['geometry'].simplify(tolerance=0.01, preserve_topology=True)
        print("Geometry simplified.")
    except Exception as e:
        print(f"Error simplifying geometry: {e}")

    # Convert to GeoJSON
    try:
        merged_geojson = json.loads(merged_nc.to_json())
        print("Converted GeoDataFrame to GeoJSON.")
    except Exception as e:
        print(f"Error converting to GeoJSON: {e}")
        merged_geojson = {}

    # Check uniqueness of 'County'
    if 'County' in merged_nc.columns:
        unique_counties = merged_nc['County'].nunique()
        total_counties = len(merged_nc)
        print(f"Unique counties: {unique_counties} out of {total_counties} total entries.")

        if unique_counties != total_counties:
            merged_nc['County_ID'] = merged_nc['County'].astype(str) + "_" + merged_nc.index.astype(str)
            featureidkey = 'properties.County_ID'
            merged_geojson = json.loads(merged_nc.to_json())
            print("Created unique County_ID.")
        else:
            print("County names are unique.")
    else:
        print("Error: 'County' column not found in GeoDataFrame.")
        featureidkey = 'properties.County'

    # Convert health indicator columns to numeric
    for category, variables in health_categories.items():
        for var in variables:
            if var in merged_nc.columns:
                merged_nc[var] = pd.to_numeric(merged_nc[var], errors='coerce')
    print("Converted health indicator columns to numeric where applicable.")
else:
    print("GeoDataFrame is empty. Please check your GeoJSON file.")

# ---------------------------
# Layout Definition
# ---------------------------

# Define the app layout with Navbar, Header, Tabs, Dropdown, Map, Bar Charts, Readme Tab, and Footer
app.layout = dbc.Container([
    # Navigation Bar
    dbc.NavbarSimple(
        brand="NC Health Insights Dashboard",  # Updated Title
        brand_href="#",
        color="primary",
        dark=True,
        className="mb-4"
    ),
    # Header and Description
    dbc.Row([
        dbc.Col([
            html.H2("Health and Socioeconomic Indicators in North Carolina", className='text-center'),
            html.P(
                "Explore various health and socioeconomic indicators across North Carolina counties. "
                "Select a category and an indicator to visualize the spatial distribution and gain insights into the factors affecting health outcomes.",
                className='text-center'
            )
        ])
    ], className='mb-4'),
    # Main Tabs for Readme and Categories
    dbc.Row([
        dbc.Col([
            dcc.Tabs(id='main-tabs', value='Readme', children=[  # Readme as first tab and default
                dcc.Tab(label="Readme", value='Readme', className='custom-tab', selected_className='custom-tab--selected'),
                dcc.Tab(label="Economic Stability", value='Economic Stability', className='custom-tab', selected_className='custom-tab--selected'),
                dcc.Tab(label="Education Access and Quality", value='Education Access and Quality', className='custom-tab', selected_className='custom-tab--selected'),
                dcc.Tab(label="Health Care Access and Quality", value='Health Care Access and Quality', className='custom-tab', selected_className='custom-tab--selected'),
                dcc.Tab(label="Neighborhood and Built Environment", value='Neighborhood and Built Environment', className='custom-tab', selected_className='custom-tab--selected'),
                dcc.Tab(label="Social and Community Context", value='Social and Community Context', className='custom-tab', selected_className='custom-tab--selected'),
                dcc.Tab(label="Health Outcomes", value='Health Outcomes', className='custom-tab', selected_className='custom-tab--selected'),
                dcc.Tab(label="Behavioral Factors", value='Behavioral Factors', className='custom-tab', selected_className='custom-tab--selected')
            ], className='custom-tabs', parent_className='custom-tabs-container')
        ])
    ], className='mb-4'),
    # Content Area for Tabs
    dbc.Row([
        dbc.Col([
            # Dynamic content based on selected tab
            html.Div(id='tab-content')
        ])
    ]),
    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P(
                "Data Source: 2024 County Health Rankings & Roadmaps",
                className='text-center'
            ),
            html.P(
                "Developed with ❤️ using Dash and Plotly.",
                className='text-center'
            )
        ])
    ], className='mt-4')
], fluid=True)

# ---------------------------
# Callbacks
# ---------------------------

# Callback to render content based on selected main tab
@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'value')]
)
def render_tab_content(selected_tab):
    if selected_tab == 'Readme':
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dcc.Markdown(
                        """
                        ## Overview

                        The **NC Health Insights Dashboard** provides a comprehensive view of various health and socioeconomic indicators across North Carolina counties. By leveraging the 2024 County Health Rankings & Roadmaps datasets, this dashboard offers insights into the factors influencing health outcomes within the state.

                        ## Data Source

                        - **Dataset:** 2024 County Health Rankings & Roadmaps
                        - **Description:** This dataset encompasses a wide range of health factors and outcomes that are critical in assessing the overall health status of counties in North Carolina.

                        ## Methodology

                        To analyze the data through the lens of Social Determinants of Health (SDOH), the following steps were undertaken:

                        1. **Data Extraction:**
                           - Extracted **87** of health factors and outcomes relevant to the study.

                        2. **Topic Modeling:**
                           - Utilized a **Large Language Model (LLM): ChatGPT 01-mini** to perform topic modeling.
                           - Classified the extracted health outcomes and factors into established SDOH categories, facilitating a structured analysis.

                        ## Features

                        - **Interactive Map:** Visualizes the spatial distribution of selected health indicators across North Carolina counties.
                        - **Bar Charts:** Displays the Top 10 and Bottom 10 counties based on the chosen indicator, allowing for quick comparative analysis.
                        - **Readme Tab:** Provides detailed information about the dashboard, data sources, and methodologies used.

                        ## Usage

                        1. **Select a Category:** Navigate to one of the category tabs (e.g., Economic Stability, Education Access and Quality).
                        2. **Choose an Indicator:** Within a category, select a specific health indicator from the dropdown menu.
                        3. **View Visualizations:** Explore the choropleth map and bar charts to gain insights into the performance of different counties.

                        ## Contact

                        For any inquiries or feedback, please contact Yared Hurisa at yaredlema@gmail.com.
                        """
                    )
                ])
            ])
        ], fluid=True)
    else:
        # Category Tabs Content
        category = selected_tab
        return [
            # Dropdown for Indicator Selection
            dbc.Row([
                dbc.Col([
                    html.Label("Select Indicator:", className='font-weight-bold'),
                    dcc.Dropdown(
                        id='indicator-dropdown',
                        options=[{'label': indicator, 'value': indicator} for indicator in health_categories[category]],
                        value=health_categories[category][0] if health_categories[category] else None,
                        multi=False,
                        clearable=False,
                        placeholder="Choose an indicator..."
                    )
                ], width=6, md=4)
            ], className='mb-4'),
            # Map Display with Loading Indicator
            dbc.Row([
                dbc.Col([
                    dcc.Loading(
                        id="loading-map",
                        type="circle",
                        children=dcc.Graph(id='indicator-map')
                    )
                ])
            ]),
            # Top and Bottom Bar Charts Display with Loading Indicators
            dbc.Row([
                dbc.Col([
                    html.H4("Top 10 Counties", className='text-center mb-2'),
                    dcc.Loading(
                        id="loading-bar-top",
                        type="circle",
                        children=dcc.Graph(id='bar-chart-top')
                    )
                ], md=6),
                dbc.Col([
                    html.H4("Bottom 10 Counties", className='text-center mb-2'),
                    dcc.Loading(
                        id="loading-bar-bottom",
                        type="circle",
                        children=dcc.Graph(id='bar-chart-bottom')
                    )
                ], md=6)
            ], className='mt-4')
        ]

# Callback to update the Map and both Bar Charts based on selected Indicator
@app.callback(
    [Output('indicator-map', 'figure'),
     Output('bar-chart-top', 'figure'),
     Output('bar-chart-bottom', 'figure')],
    [Input('indicator-dropdown', 'value')]
)
def update_visualizations(selected_indicator):
    # Initialize empty figures with messages
    empty_figure = {
        "data": [],
        "layout": {
            "title": "Please select an indicator to display the visualizations.",
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [
                {
                    "text": "No indicator selected.",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20}
                }
            ]
        }
    }

    if not selected_indicator:
        return empty_figure, empty_figure, empty_figure

    # Check if the indicator exists in the DataFrame
    if selected_indicator not in merged_nc.columns:
        error_figure = {
            "data": [],
            "layout": {
                "title": f"Indicator '{selected_indicator}' not found in the data.",
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "annotations": [
                    {
                        "text": f"Indicator '{selected_indicator}' not found.",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20}
                    }
                ]
            }
        }
        return error_figure, error_figure, error_figure

    # Handle missing data by filling with the median
    merged_nc_clean = merged_nc.copy()
    if merged_nc_clean[selected_indicator].isnull().any():
        median_val = merged_nc_clean[selected_indicator].median()
        merged_nc_clean[selected_indicator] = merged_nc_clean[selected_indicator].fillna(median_val)

    # Create choropleth map
    try:
        map_fig = px.choropleth_mapbox(
            merged_nc_clean,
            geojson=merged_geojson,
            locations='County' if 'County' in merged_nc_clean.columns else 'County_ID',
            color=selected_indicator,
            color_continuous_scale="Viridis",
            range_color=(merged_nc_clean[selected_indicator].min(), merged_nc_clean[selected_indicator].max()),
            mapbox_style="carto-positron",
            zoom=6,
            center={"lat": 35.7596, "lon": -79.0193},  # Center on NC
            opacity=0.7,
            labels={selected_indicator: selected_indicator},
            featureidkey=featureidkey,
            hover_data=['County', selected_indicator]  # Add more fields as needed
        )
        map_fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            coloraxis_colorbar=dict(
                title=selected_indicator,
                ticksuffix="%"
            )
        )
    except Exception as e:
        map_fig = {
            "data": [],
            "layout": {
                "title": "Error creating the choropleth map.",
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "annotations": [
                    {
                        "text": "An error occurred while creating the map.",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20}
                    }
                ]
            }
        }

    # Prepare data for Top 10 Bar Chart
    try:
        top_n = 10
        merged_nc_top = merged_nc_clean.nlargest(top_n, selected_indicator)
        bar_top_fig = px.bar(
            merged_nc_top,
            x='County' if 'County' in merged_nc_top.columns else 'County_ID',
            y=selected_indicator,
            orientation='v',  # Vertical bars
            title=f"Top {top_n} Counties by {selected_indicator}",
            labels={'County': 'County', selected_indicator: selected_indicator},
            height=600,
            color=selected_indicator,
            color_continuous_scale="Viridis"
        )
        bar_top_fig.update_layout(
            margin={"r":50,"t":50,"l":100,"b":300},  # Increased bottom margin for label readability
            xaxis_title="County",
            yaxis_title=selected_indicator,
            xaxis=dict(
                tickangle=-45,          # Rotate x-axis labels for readability
                tickmode='array',       # Ensures that only the Top 10 counties are labeled
                tickvals=merged_nc_top['County'],  # Specific tick values
                ticktext=merged_nc_top['County']   # Specific tick labels
            ),
            yaxis=dict(
                tickmode='auto',        # Let Plotly decide tick placement
                nticks=5,               # Limit number of Y-axis ticks
                zeroline=False,         # Remove the zeroline
                showgrid=True,          # Show gridlines for better readability
                ticks='outside',        # Position ticks outside the axis
                ticklen=5,              # Length of the ticks
                tickwidth=1,            # Width of the ticks
                tickcolor='black',      # Color of the ticks
                showticklabels=True    # Ensure tick labels are shown
            )
        )
    except Exception as e:
        bar_top_fig = {
            "data": [],
            "layout": {
                "title": f"Error creating the Top {top_n} bar chart.",
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "annotations": [
                    {
                        "text": f"An error occurred while creating the Top {top_n} bar chart.",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20}
                    }
                ]
            }
        }

    # Prepare data for Bottom 10 Bar Chart
    try:
        bottom_n = 10
        merged_nc_bottom = merged_nc_clean.nsmallest(bottom_n, selected_indicator)
        bar_bottom_fig = px.bar(
            merged_nc_bottom,
            x='County' if 'County' in merged_nc_bottom.columns else 'County_ID',
            y=selected_indicator,
            orientation='v',  # Vertical bars
            title=f"Bottom {bottom_n} Counties by {selected_indicator}",
            labels={'County': 'County', selected_indicator: selected_indicator},
            height=600,
            color=selected_indicator,
            color_continuous_scale="Viridis"
        )
        bar_bottom_fig.update_layout(
            margin={"r":50,"t":50,"l":100,"b":300},  # Increased bottom margin for label readability
            xaxis_title="County",
            yaxis_title=selected_indicator,
            xaxis=dict(
                tickangle=-45,          # Rotate x-axis labels for readability
                tickmode='array',       # Ensures that only the Bottom 10 counties are labeled
                tickvals=merged_nc_bottom['County'],  # Specific tick values
                ticktext=merged_nc_bottom['County']   # Specific tick labels
            ),
            yaxis=dict(
                tickmode='auto',        # Let Plotly decide tick placement
                nticks=5,               # Limit number of Y-axis ticks
                zeroline=False,         # Remove the zeroline
                showgrid=True,          # Show gridlines for better readability
                ticks='outside',        # Position ticks outside the axis
                ticklen=5,              # Length of the ticks
                tickwidth=1,            # Width of the ticks
                tickcolor='black',      # Color of the ticks
                showticklabels=True    # Ensure tick labels are shown
            )
        )
    except Exception as e:
        bar_bottom_fig = {
            "data": [],
            "layout": {
                "title": f"Error creating the Bottom {bottom_n} bar chart.",
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "annotations": [
                    {
                        "text": f"An error occurred while creating the Bottom {bottom_n} bar chart.",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20}
                    }
                ]
            }
        }

    return map_fig, bar_top_fig, bar_bottom_fig

# ---------------------------
# Run the Dash App
# ---------------------------
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    app.run_server(debug=True, host='0.0.0.0', port=port)
