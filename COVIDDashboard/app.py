# Author: Priyank Shroff
# Description: A web app/dashboard to track COVID 19 Data.

# Importing libraries
import pandas as pd
from pandas import DataFrame
import plotly.graph_objects as go
import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import datetime
import calendar
import os
import pathlib
import re

# -------------------------------------------------------------------
# Download data
APP_PATH = str(pathlib.Path(__file__).parent.resolve())

covid_url = r"https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"
lat_long_url = r"https://raw.githubusercontent.com/plotly/dash-sample-apps/master/apps/dash-opioid-epidemic/data/lat_lon_counties.csv"
mask_url = r"https://raw.githubusercontent.com/nytimes/covid-19-data/master/mask-use/mask-use-by-county.csv"

# Reading the data files
covid_data = pd.read_csv(covid_url, error_bad_lines=False)
lat_lon = pd.read_csv(lat_long_url, error_bad_lines=False)
mask_data = pd.read_csv(mask_url, error_bad_lines=False)
state_lat_lon = pd.read_csv(os.path.join(APP_PATH, os.path.join("data", "StateLatLon.csv")))
state_lat_lon = state_lat_lon.rename(columns={"latitude": "state_latitude", "longitude": "state_longitude"})

# Combining the COVID and Lat and Long data sets
covid_data = covid_data.merge(lat_lon, left_on=['county', 'fips'], right_on=['County ', 'FIPS '], how='inner')
covid_data = covid_data.merge(state_lat_lon, left_on=['state'], right_on=['name'], how='inner')
covid_data['YEAR'] = pd.DatetimeIndex(covid_data['date']).year
covid_data = covid_data.loc[covid_data['YEAR'] == 2020, :]
covid_data['MONTH'] = pd.DatetimeIndex(covid_data['date']).month
covid_data['DATE'] = pd.to_datetime(covid_data['date'])
covid_data = covid_data.drop(columns=["State", "County ", "LandAreakm2 ", "LandAreami2 ", "WaterAreakm2 "
    , "WaterAreami2 ", "TotalAreakm2 ", "TotalAreami2 ", "name"])
covid_data = covid_data.rename(columns={"state_x": "State", "state_y": "State_Abb"})

MONTH = covid_data['MONTH'].unique().astype(int)


# Get last day of each month
def last_day_of_the_month(day):
    next_month = day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


date_list = []

for month in range(1, 13):
    date_list.append(last_day_of_the_month(datetime.date(2020, month, 1)))

date_df = DataFrame(date_list, columns=['date'])
date_df['date'] = pd.to_datetime(date_df['date'])

# Filter to just the last day of the months
covid_data_filter = date_df.merge(covid_data, left_on=['date'], right_on=['DATE'], how='inner')

# Combining Mask and Lat and Long Data along with county names and states
county_data = covid_data_filter[['county', 'State', 'FIPS ']]
county_data = county_data.drop_duplicates()
mask_data = mask_data.merge(county_data, left_on=['COUNTYFP'], right_on=['FIPS '], how='inner')
mask_data_state = mask_data.groupby(['State'], as_index=False).mean()
mask_data_state = mask_data_state.drop(columns=['COUNTYFP', 'FIPS '])

us_average = mask_data.mean()
us_average = us_average.drop(labels=['COUNTYFP', 'FIPS '])
state_list = covid_data_filter['State'].unique()


# Instantiate the app
app = dash.Dash(__name__
                , meta_tags=[{"name": "viewport", "content": "width=device-width"}]
                , external_stylesheets=[dbc.themes.BOOTSTRAP]
                )
server = app.server
app.config["suppress_callback_exceptions"] = True

# Plotly mapbox token
mapbox_access_token = "pk.eyJ1IjoicHNocm9mZjUiLCJhIjoiY2toZGx2Y2k2MGp5NjJ5czJoZThxMGt2OCJ9.h0dENffhXuLWli97HOlxPw"

app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            className="row",
            children=[
                # Column for filters
                html.Div(
                    className="five columns div-first-column",
                    id="first-column",
                    children=[
                        html.Img(className="logo"
                                 , src=app.get_asset_url("dash-logo-new.png")),
                        html.H2(children="US COVID Cases By State-County"),
                        html.H5("Select the month and state you want to view"),
                        html.Div(
                            className="div-for-filter",
                            children=[
                                dcc.Slider(
                                    id="months-slider",
                                    min=min(MONTH),
                                    max=max(MONTH),
                                    value=min(MONTH),
                                    marks={
                                        str(month): {
                                            "label": calendar.month_abbr[month],
                                            "style": {'color': "#7fafdf", "fontsize": 12}
                                        }
                                        for month in MONTH
                                    }
                                )
                            ]
                        ),
                        html.Div(
                            className="row",
                            children=[
                                html.Div(
                                    className="div-for-filter",
                                    children=[
                                        dcc.Dropdown(
                                            id="state-select",
                                            options=[{"label": i, "value": i} for i in state_list],
                                            value="Illinois"
                                        )
                                    ]
                                )
                            ]
                        ),
                        html.Div(
                            className="div-for-charts",
                            children=[
                                html.Div(
                                    id="table-container",
                                    children=[
                                        dcc.Graph(
                                            id="state-table",
                                            figure=dict(
                                                layout=dict(
                                                    autosize=True
                                                )
                                            )
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                # Column for app plots
                html.Div(
                    className="seven columns div-for-charts bg-grey",
                    children=[
                        dcc.Loading(
                            id="loading",
                            children=dcc.Graph(
                                id="state-chart",
                                figure={
                                    "data": [],
                                    "layout": dict(
                                        plot_bgcolor="#171b26",
                                        paper_bgcolor="#171b26"
                                    )
                                }
                            )
                        ),
                        html.Div(
                            id="mask-container",
                            children=[
                                dcc.Graph(
                                    id="mask-chart",
                                    figure=dict(
                                        layout=dict(
                                            autosize=True
                                        )
                                    )
                                )
                            ]
                        )
                    ]
                ),
                html.Div(
                    id="Text",
                    children=[
                        html.P("If the dashboard doesnt update for a month-state combination, it means there were no COVID cases recored. For example Massachusetts-January."
                               , style=dict(font_style='italic')),
                        html.P("COVID data and Mask Compliance data is sourced from The New York Times, based on reports from state and local health agencies")
                    ]
                )
            ]
        )
    ]
)

@app.callback(
    Output("state-chart", "figure"),
    [Input("months-slider", "value"),
     Input("state-select", "value")]
)
def update_state_chart(months, state):
    state_data = covid_data_filter.loc[
                 (covid_data_filter['State'] == state) & (covid_data_filter['MONTH'].astype(int) == months), :]
    if state_data.empty:
        raise PreventUpdate
    else:
        colors = ["#00FF00", "#FFE400", '#FF6900', "#FF0000"]
        color_scale = [
            [0, "#00FF00"],
            [0.33, "#FFE400"],
            [0.66, "#FF6900"],
            [1, "#FF0000"]
        ]

        lat = state_data["Latitude "].to_list()
        lon = state_data["Longitude"].to_list()
        county = state_data["county"].to_list()
        value = state_data["cases"].to_list()

        cases_data = {}
        cases_data['min'] = min(value)
        cases_data['max'] = max(value)
        cases_data['mid'] = (cases_data['max'] - cases_data['min']) / 2
        cases_data['low-mid'] = (cases_data['mid'] - cases_data['min']) / 2
        cases_data['high-mid'] = (cases_data['max'] - cases_data['mid']) / 2

        fig = go.Figure()
        for i in range(len(lat)):
            region = county[i]
            val = value[i]
            if val <= cases_data['low-mid']:
                color = colors[0]
            elif cases_data['low-mid'] < val <= cases_data['mid']:
                color = colors[1]
            elif cases_data['mid'] < val <= cases_data['high-mid']:
                color = colors[2]
            else:
                color = colors[3]

            fig.add_trace(go.Scattermapbox(
                lat=[lat[i]],
                lon=[lon[i]],
                mode="markers",
                marker=dict(
                    color=color,
                    showscale=True,
                    colorscale=color_scale,
                    cmin=cases_data['min'],
                    cmax=cases_data['max'],
                    size=15 * (1+(val + cases_data['min'])/cases_data['max']),
                    colorbar=dict(
                        title="Number of Covid Cases",
                        x=0.93,
                        xpad=0,
                        tickfont=dict(color='#d8d8d8'),
                        titlefont=dict(color='#d8d8d8'),
                        thicknessmode='pixels',
                    )
                ),
                opacity=0.8,
                hoverinfo="text",
                text=region + "<br>" + "Covid Cases: {}".format(val)
            ))

        fig.update_layout(
            plot_bgcolor="#171b26",
            paper_bgcolor="#171b26",
            clickmode="event+select",
            hovermode="closest",
            showlegend=False,
            margin=go.layout.Margin(l=0, r=35, t=0, b=0),
            mapbox=go.layout.Mapbox(
                accesstoken=mapbox_access_token,
                center=go.layout.mapbox.Center(
                    lat=state_data["Latitude "].mean(), lon=state_data["Longitude"].mean()
                ),
                pitch=5,
                zoom=5,
                style="mapbox://styles/pshroff5/ckigtn4d003b119oaaejldifl" #"mapbox://styles/plotlymapbox/cjvppq1jl1ips1co3j12b9hex",
            ),
            autosize=True
        )
        return fig

    return fig


@app.callback(
    Output("mask-chart", "figure"),
    [Input("state-select", "value")]
)
def update_mask_chart(state):
    mask_filtered = mask_data_state.loc[mask_data_state['State'] == state, :]
    mask_usage = ['NEVER', 'RARELY', 'SOMETIMES', 'FREQUENTLY', 'ALWAYS']
    y_axis = mask_filtered.drop(columns=['State'])*100
    yaxis = {
        state: [y_axis.iloc[0, :], 'rgb(125,183,203)'],
        'US Average': [us_average*100, 'rgb(145,147,148)']
    }

    fig = go.Figure()
    for i in yaxis:
        fig.add_trace(go.Bar(
            x=mask_usage,
            y=yaxis[i][0],
            name=i,
            marker_color=yaxis[i][1],
            text=yaxis[i][0]
        ))
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig.update_layout(
        autosize=True,
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        margin=go.layout.Margin(l=10, r=0, t=0, b=50),
        font=dict(color="#d8d8d8"),
        xaxis_tickfont_size=14,
        yaxis=dict(
            title='% Respondants',
            titlefont_size=16,
            tickfont_size=14,
            showgrid=False
        ),
        legend=dict(
            x=0,
            y=1.0,
            bgcolor='rgba(255,255,255,0)',
        ),
        barmode='group',
        bargap=0.15,
        bargroupgap=0.1,
        plot_bgcolor="#171b26",
        paper_bgcolor="#171b26",
    )

    return fig

@app.callback(
    Output('state-table', 'figure'),
    [Input("months-slider", "value"),
     Input("state-select", "value")]
)
def update_table(months, state):
    display_table = covid_data_filter.loc[
                 (covid_data_filter['State'] == state) & (covid_data_filter['MONTH'].astype(int) == months), :]
    display_table = display_table.sort_values(by=['cases'], ascending=False)
    filtered_table = display_table[['MONTH', 'State', 'county', 'cases']]
    if display_table.empty:
        raise PreventUpdate
    else:
        fig = go.Figure(
            data=[go.Table(
                header=dict(values=[['<b>MONTH</b>'], ['<b>STATE</b>'], ['<b>COUNTY</b>'],['<b>Number of Cases</b>']],
                            fill_color='#252e3f',
                            line_color='#FFFFFF',
                            line_width=0.5,
                            align='left',
                            height=40,
                            font=dict(color='white')),
                cells=dict(values=[display_table.MONTH, display_table.State, display_table.county, display_table.cases],
                           fill_color='#252e3f',
                           align='left',
                           height=40,
                           line_width=0.5,
                           font=dict(color="white"),
                           font_size=12)
            )]
        )
        fig.update_layout(
            showlegend=False,
            autosize=True,
            margin=go.layout.Margin(l=10, r=0, t=35, b=0),
            paper_bgcolor='#171b26',
        )
        return fig

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

