import os
from main import *
import altair as alt
import plotly_express as px
import streamlit as st
from datetime import date
from vega_datasets import data
import matplotlib.pyplot as plt
from bokeh.plotting import figure
from google.analytics.data_v1beta.types import Metric
from google.analytics.data_v1beta.types import OrderBy
from google.analytics.data_v1beta.types import DateRange
from google.analytics.data_v1beta.types import Dimension
from google.analytics.data_v1beta.types import RunReportRequest
from google.analytics.data_v1beta import BetaAnalyticsDataClient

# GLOBAL VARIABLES
property_id = "386101877"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-analytics-viso-service-account.json'
client = BetaAnalyticsDataClient()

## STREAMLIT APP - MAIN STRUCTURE
st.set_page_config(layout="wide")   # Use the full page instead of a narrow central column
st.title("MK 9 - Audience Web")

st.divider()

# FILTERS SIDEBAR -- PART 1
st.sidebar.title("FILTRES")
start_date_input = st.sidebar.date_input("Date de Début", value=date(date.today().year-1, date.today().month, 1),
                                         min_value="2016-01-01", max_value=date(date.today().year, date.today().month, date.today().day-1))
end_date_input = st.sidebar.date_input("Date de Fin", value="today", min_value=start_date_input,
                                       max_value=date(date.today().year, date.today().month, date.today().day-1))
no_days = end_date_input - start_date_input

## DATA COLLECTION
@st.cache_data
def request_ga_data(property_id, start_date_input=start_date_input, end_date_input=end_date_input):
    return RunReportRequest(
            property='properties/'+property_id,
            dimensions=[Dimension(name="year"),
                        Dimension(name="yearMonth"),
                        Dimension(name="month"),
                        # Dimension(name="week"),
                        # Dimension(name="date"),
                        Dimension(name="country"),
                        # Dimension(name="sessionMedium"),
                        # Dimension(name="defaultChannelGroup")],       # NOT POSSIBLE TO CALCULATE NEW VISITORS
                        Dimension(name="firstUserDefaultChannelGroup")],
                        # Dimension(name="sessionSourceMedium")],
            metrics=[Metric(name="activeUsers"),
                     Metric(name="newUsers"),
                     Metric(name="Sessions"),
                     Metric(name="engagedSessions"),
                    #  Metric(name="bounceRate"),
                     Metric(name="screenPageViews"),                    ## >> screen_view + page_view events
                     Metric(name="averageSessionDuration")],
            order_bys = [OrderBy(dimension = {'dimension_name': 'year'}),
                         OrderBy(dimension = {'dimension_name': 'yearMonth'}),
                         OrderBy(dimension = {'dimension_name': 'month'}),
                        OrderBy(dimension = {'dimension_name': 'country'}),
                        OrderBy(dimension = {'dimension_name': 'firstUserDefaultChannelGroup'})],
            date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],
        )
    
## TABLE OUTPUT
request = request_ga_data(property_id, start_date_input, end_date_input)
output_df = format_report(client, request)
# output_df.reset_index(inplace=True)

# FILTERS SIDEBAR -- PART 2
country_filter = st.sidebar.multiselect("Pays:", options=output_df['country'].unique())
# defaultChannelGroup_filter = st.sidebar.multiselect("Canaux:", options=output_df['defaultChannelGroup'].unique())
firstUserDefaultChannelGroup_filter = st.sidebar.multiselect("Default Channel Group:", options=output_df['firstUserDefaultChannelGroup'].unique())
top_results = st.sidebar.slider("Choisissez combien de TOP pages vous souhaitez voir", min_value=5, max_value=100, value=10, step=5)
st.sidebar.button("Download Excel Output", on_click=export_to_excel(output_df))
# st.sidebar.download_button("Download Excel Output", data=output_df, file_name=date.today().strftime("%Y-%m-%d at %H-%m-%s") + '.xlsx', on_click=export_to_excel(output_df))

# Creating new & deleting avg columns on dataframe
output_df['yearMonth'] = pd.to_datetime(output_df['yearMonth'], format='%Y%m')
# st.write(type(output_df['yearMonth']))
# output_df['yearMonth'] = output_df['yearMonth'].strftime('%Y-%m')
# output_df['yearMonth'] = pd.to_datetime(output_df['yearMonth']).strftime("%Y%m")
output_df['bounces'] = output_df['Sessions'] - output_df['engagedSessions']
output_df['returningUsers'] = output_df['activeUsers'] - output_df['newUsers']
output_df['SessionsDuration'] = output_df['averageSessionDuration'] * output_df['engagedSessions']

# Rectifying data type
# output_df['yearMonth'] = output_df['yearMonth'].values.astype('str')
output_df['activeUsers'] = output_df['activeUsers'].values.astype('int')
output_df['newUsers'] = output_df['newUsers'].values.astype('int')

st.divider()

## GRAPH 1 -- FUNNEL MARKETING
# Aggregating absolute values on dimensions of interest 
funnel_chart_prep = output_df.copy()
funnel_chart_prep = funnel_chart_prep.drop(columns=['averageSessionDuration', 'SessionsDuration'])
funnel_chart_prep = output_df[['Sessions', 'engagedSessions','activeUsers', 'newUsers', 'returningUsers', 'screenPageViews']].sum()#agg('sum')
funnel_chart_prep = funnel_chart_prep.reset_index().rename(columns={0:'values', 'index':'stage'})
funnel_chart_prep = funnel_chart_prep.sort_values(by="values", ascending=False)
# st.write(funnel_chart_prep)
fig = px.funnel(funnel_chart_prep, x='values', y='stage')
st.plotly_chart(fig)

st.divider()

## GRAPH 2
year_month_table = output_df.groupby(by='yearMonth').agg(Sessions=('Sessions', 'sum'), engagedSessions=('engagedSessions', 'sum'),
                                                      bounces=('bounces','sum'), activeUsers=('activeUsers','sum'),
                                                      newUsers=('newUsers','sum'), returningUsers=('returningUsers', 'sum'),
                                                      screenPageViews=('screenPageViews', 'sum'),
                                                      SessionsDuration=('SessionsDuration','sum'))

year_month_table['bounceRate'] = year_month_table['bounces'] / year_month_table['Sessions']
year_month_table['bounceRate'] = year_month_table['bounceRate'].map('{:.3f}'.format) #.values.astype('str')
year_month_table['avgScreenViews'] = year_month_table['screenPageViews'] / year_month_table['Sessions']
year_month_table['avgScreenViews'] = year_month_table['avgScreenViews'].map('{:.1f}'.format) #.values.astype('str')
year_month_table['avgSessionDuration'] = year_month_table['SessionsDuration'] / year_month_table['Sessions']
year_month_table['avgSessionDuration'] = year_month_table['avgSessionDuration'].map('{:.1f}'.format) #.values.astype('str')
year_month_table.drop(columns=['screenPageViews','SessionsDuration'], inplace=True)
year_month_table.reset_index(inplace=True)
# st.write(year_month_table)

st.header(f'\nActive, New & Bounced Users')
base = alt.Chart(year_month_table).encode(x='yearMonth')
bar_active = base.mark_bar(color='blue', xOffset=-12, width=20).encode(y='sum(activeUsers)')
bar_new = base.mark_bar(color='green', opacity=1, xOffset=12, width=20).encode(y='sum(newUsers)')
line = base.mark_line(color='red',dx=5).encode(alt.Y2('sum(bounceRate)'))
text_active = bar_active.mark_text(align='right',baseline='top',dx=2, color='white').encode(text='sum(activeUsers)')
text_new = bar_new.mark_text(align='left',baseline='top',dx=2, color='white').encode(text='sum(newUsers)')
alt.Color(value='lightgray')
bar_users = st.altair_chart(line + bar_active + text_active + bar_new + text_new,
                            use_container_width=None, theme="streamlit", key=None, on_select="ignore", selection_mode=None)
st.divider()

## GRAPH 3
year_month_table['engagedSessionsRate'] = (year_month_table['engagedSessions'] / year_month_table['Sessions']).map('{:.3f}'.format)
# year_month_table['bounceRate'] = year_month_table['bounces'] / year_month_table['Sessions']
year_month_table['newUsersRate'] = (year_month_table['newUsers'] / year_month_table['activeUsers']).map('{:.3f}'.format)
year_month_table['returningUsersRate'] = (year_month_table['returningUsers'] / year_month_table['activeUsers']).map('{:.3f}'.format)


st.header(f'\nTable de Données Principale')
year_month_table.sort_values('yearMonth', ascending=False, inplace=True)
year_month_table.drop(columns=['engagedSessions','returningUsers','newUsers','bounces'], inplace=True)
st.dataframe(data=year_month_table, height=None, hide_index=True, column_order=['yearMonth','Sessions','engagedSessionsRate','bounceRate','activeUsers','returningUsersRate','newUsersRate','avgScreenViews','avgSessionDuration'],
             column_config={
    "yearMonth": st.column_config.DateColumn("Année - Mois", format="YYYY - MMM"),
    "Sessions": st.column_config.NumberColumn("Sessions", format="localized", min_value=0),
    "engagedSessionsRate": st.column_config.ProgressColumn("% Sessions Engagées",format="percent",min_value=0,max_value=1),
    # "bounces": st.column_config.NumberColumn("Bounces",format="localized",min_value=0),
    "bounceRate": st.column_config.ProgressColumn("% Bounce",help="% of users exiting website as soon as landing",format="percent",min_value=0,max_value=1),
    "activeUsers": st.column_config.NumberColumn("Utilisateurs Actifs",format="localized",min_value=0,max_value=1),
    "returningUsersRate": st.column_config.ProgressColumn("% de Retour",format="percent",min_value=0,max_value=1),
    "newUsersRate": st.column_config.ProgressColumn("% de Nouveaux",format="percent",min_value=0,max_value=1),
    "avgScreenViews": st.column_config.NumberColumn("Moy. Pages Vues",format="localized",min_value=0),
    "avgSessionDuration": st.column_config.NumberColumn("Durée Moy. Session",format="localized",min_value=0),
},)

st.divider()

## DISPLAY - MAIN STRUCTURE
col1, col2, col3 = st.columns(3)

landing_table, page_users_table, countries_table = traffic_report(end_date_input, start_date_input, property_id, client)

## GRAPH 4
with col1:
    st.header(f'\nTop {str(top_results)} Countries')
    countries_table.index += 1
    st.dataframe(countries_table[0:top_results])#, hide_index=True)

with col2:
    st.header(f'\nTop {str(top_results)} Landing Pages')
    landing_table.index += 1
    st.table(landing_table[0:top_results])
        
with col3:
    st.header(f'\nTop {str(top_results)} Visited Pages')
    page_users_table.index += 1
    st.table(page_users_table[0:top_results])
    