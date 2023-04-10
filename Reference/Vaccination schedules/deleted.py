png_renderer = pio.renderers["png"]
png_renderer.width = 1600
png_renderer.height = 2400
pio.renderers.default = "png"
pio.renderers.default = "browser"



fig2 = px.strip(vaccine_schedule[(vaccine_schedule['type'] == 1)].sort_values(by=['ISO_3_CODE'], ascending=False),
                x='Age_earliest_schedule_inyears', y='COUNTRYNAME', hover_name='VACCINE_DESCRIPTION',
                custom_data=['type', 'gender', 'Context'],
                color='VACCINE_DESCRIPTION',
                facet_row='WHO_REGION',
                range_x=(0, 70),
                labels={"COUNTRYNAME": "Member State", "Age_earliest_schedule_inyears": "Earliest Age (Years)",
                        "VACCINE_DESCRIPTION": "Vaccine Name", "SCHEDULEROUNDS": "Schedule Rounds",
                        "WHO_REGION": "WHO Region", },
                title="Global Immunizations Schedules (2020): Age-based eligibility only",
                template="plotly_dark",
                )

for trace in fig2.select_traces():
    trace.marker.update(size=4)
    trace.marker.update(opacity=0.7)
    trace.marker.update(symbol='triangle')

fig2.add_scatter()

fig2.update_yaxes(matches=None)

fig2.update_layout(
    showlegend=False,
    font_family="Segoe UI",
    xaxis=dict(
        tickmode='array',
        tickvals=[0, 1, 5, 12, 18, 30, 40, 50, 60, 70],
        titlefont=dict(size=16), tickfont=dict(size=12)
    )
)

fig2.for_each_xaxis(lambda x: x.update(tickvals=[0, 1, 5, 12, 18, 30, 40, 50, 60, 70]))

fig2.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

for axis in fig2.layout:
    if type(fig2.layout[axis]) == go.layout.YAxis:
        fig2.layout[axis].title.text = ''

fig2.show()

fig1.for_each_shape(lambda x: print(x))

symbols = ['circle', 'circle-open', 'square', 'square-open', 'diamond', 'diamond-open', 'cross', 'x']
fig.data[0].update(marker_color=color)
fig.data[0].update(marker_symbol=symbol)
#     fig.data[0].update(marker_size=size)
width = 400,
height = 800
# Mark out the FEMALE only

for trace in fig1.select_traces(selector=1):
    print(trace["name"])

for shape in fig1.select_shapes():
    print(shape["name"])

    ## Figure 2:

#xaxis = dict(titlefont=dict(family='Segoe UI', size=16), tickfont=dict(family='Segoe UI', size=12)),

#hover_data = 'SCHEDULEROUNDS',
#color = 'Context',

#ticktext = ['One', 'Three', 'Five', 'Seven', 'Nine', 'Eleven']
#titlefont = dict(family='Segoe UI', size=16), tickfont = dict(family='Segoe UI', size=12)
# Color for context, female,
# Labels for non MCH vaccines types
# Shade Covid-19 age bands
# Add pregnant women, 
# Opacity and size


# vaccines1 = vaccine_schedule[vaccine_schedule['type']==1]


fig = px.strip(vaccine_schedule[vaccine_schedule['type'] == 1], x='Age_earliest_schedule_inyears', y='ISO_3_CODE',
               color='Context',
               range_x=(0, 70),
               labels={"ISO_3_CODE": "Member State", "Age_earliest_schedule_inyears": "Earliest Age (Years)",
                       "Context": "Context", },
               title="SEAR Vaccination Schedule (2020): Eligibility based on age"
               )
for trace in fig.select_traces():
    trace.marker.update(size=10)
    trace.marker.update(opacity=0.7)
fig.show()
fig.show(renderer="png")

# vaccines_searo_type1['ones'] = 1
# vaccines_searo_type1_grouped = vaccines_searo_type1.groupby(['ISO_3_CODE','Age_earliest_schedule_inyears'], as_index=False).count()
# vaccines_searo_type1_grouped['Member_State'] = pd.factorize(vaccines_searo_type1_grouped['ISO_3_CODE'], sort = True)[0]
layout = go.Layout(
    title='SEARO Vaccination schedules (Age-based)',
    yaxis=dict(title='Member State', titlefont=dict(size=yaxis_font_size)
               , tickfont=dict(size=yaxis_font_size)),
    xaxis=dict(title='Age (Years)', titlefont=dict(size=xaxis_font_size)
               , tickfont=dict(size=yaxis_font_size)),
    showlegend=False
)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=vaccines_searo_type1_grouped['Age_earliest_schedule_inyears'],
    y=vaccines_searo_type1_grouped['ISO_3_CODE'],
    mode='markers',
    marker=dict(
        color=['red'],
        size=5 * vaccines_searo_type1_grouped['ones'],
        opacity=0.50
    )
)
)
fig.update_layout(
    title='SEARO Vaccination Schedules (Age-based)',
    plot_bgcolor="#FFFFFF",
    yaxis=dict(title='Member State', titlefont=dict(family='Segoe UI', size=12),
               tickfont=dict(family='Segoe UI', size=10)),
    xaxis=dict(title='Age (Years)', titlefont=dict(family='Segoe UI', size=12),
               tickfont=dict(family='Segoe UI', size=10)),
)
fig.show()

# [ ] Color can be based on the context - MCH, school, other
# [ ] check this - IDN_TD_S_GENERAL

# Collapse the age and populaion categories into Context and Subpopulation




