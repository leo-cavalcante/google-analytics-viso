import os
import dateutil
from main import *
import altair as alt
import pandas as pd
import streamlit as st
import datetime
from datetime import date
# from datetime import datetime
import plotly_express as px
# from vega_datasets import data
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

intro1, intro2 = st.columns([0.25, 0.75])
with intro1:
    st.image('viso-logo.jpg')
with intro2:
    st.header("Marketing Digital | Tableau de Bord")

# FILTERS SIDEBAR -- PART 1
st.sidebar.header("Filtres")

one_year = date.today() - dateutil.relativedelta.relativedelta(months=11)

# scol1, scol2 = st.sidebar.columns(2)
# with scol1:
start_date_input = st.sidebar.date_input("Date de Début d'Analyse", value=date(one_year.year, one_year.month, 1),
                                            min_value="2016-01-01", max_value=date(date.today().year, date.today().month, date.today().day-1))
end_date_input = st.sidebar.date_input("Date de Fin d'Analyse", value="today", min_value=start_date_input,
                                            max_value=date(date.today().year, date.today().month, date.today().day-1))
no_days = end_date_input - start_date_input
# with scol2:
#     start_date_comparison = st.sidebar.date_input("Début Comparaison", value=date(start_date_input.year-1, start_date_input.month, start_date_input.day),
#                                                 min_value="2016-01-01", max_value=start_date_input - dateutil.relativedelta.relativedelta(days=1))
#     end_date_comparison = st.sidebar.date_input("Fin Comparaison", value=min(date(end_date_input.year-1, end_date_input.month, end_date_input.day),start_date_input),
#                                                 min_value="2016-01-01", max_value=start_date_input - dateutil.relativedelta.relativedelta(days=1))

start_date_comparison = date(start_date_input.year-1, start_date_input.month, start_date_input.day)
end_date_comparison = date(end_date_input.year-1, end_date_input.month, end_date_input.day)
no_days_comparison = end_date_comparison - start_date_comparison
st.sidebar.markdown("Dates de Comparaison: du {} au {}".format(start_date_comparison.strftime("%d %B %Y"),end_date_comparison.strftime("%d %B %Y")))
st.sidebar.divider()

## DATA COLLECTION
@st.cache_data
def request_ga_data(property_id, start_date_input=start_date_input, end_date_input=end_date_input):
    return RunReportRequest(
            property='properties/'+property_id,
            dimensions=[Dimension(name="yearMonth"), # Dimension(name="year"), Dimension(name="month"), # Dimension(name="week"), # Dimension(name="date"),
                        Dimension(name="country"), # Dimension(name="sessionSourceMedium")], # Dimension(name="sessionMedium"), # Dimension(name="defaultChannelGroup")],       # NOT POSSIBLE TO CALCULATE NEW VISITORS
                        Dimension(name="firstUserDefaultChannelGroup")],
            metrics=[Metric(name="activeUsers"),
                     Metric(name="newUsers"),
                     Metric(name="Sessions"),
                     Metric(name="engagedSessions"), #  Metric(name="bounceRate"),
                     Metric(name="screenPageViews"),                    ## >> screen_view + page_view events
                     Metric(name="averageSessionDuration")],
            order_bys = [OrderBy(dimension = {'dimension_name': 'yearMonth'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}),
                        OrderBy(dimension = {'dimension_name': 'country'}),
                        OrderBy(dimension = {'dimension_name': 'firstUserDefaultChannelGroup'})],
            date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],
        )
    
## TABLE OUTPUT
request = request_ga_data(property_id, start_date_input, end_date_input)
output_df = format_report(client, request)
# output_df.reset_index(inplace=True)

request_comp = request_ga_data(property_id, start_date_comparison, end_date_comparison)
comp_df = format_report(client, request_comp)
comp_df['yearMonth'] = comp_df['yearMonth'].map(lambda x: str(int(x)+100))

# FILTERS SIDEBAR -- PART 2
country_filter = st.sidebar.multiselect("Pays:", options=output_df['country'].unique())
firstUserDefaultChannelGroup_filter = st.sidebar.multiselect("Canal d'Acquisition:", options=output_df['firstUserDefaultChannelGroup'].unique())
st.sidebar.divider()
top_results = st.sidebar.slider("Nombre de TOP résultats à afficher:", min_value=5, max_value=50, value=5, step=5)
st.sidebar.divider()
st.sidebar.button("Download Excel Output", on_click=export_to_excel(output_df))
# st.sidebar.download_button("Download Excel Output", data=output_df, file_name=date.today().strftime("%Y-%m-%d at %H-%m-%s") + '.xlsx', on_click=export_to_excel(output_df))

# APPLYING FILTERS TO DATAFRAME
@st.cache_data
def df_preparation(output_df, country_filter=country_filter, firstUserDefaultChannelGroup_filter=firstUserDefaultChannelGroup_filter):
    if country_filter:
        output_df = output_df[output_df["country"].isin(country_filter)]
    if firstUserDefaultChannelGroup_filter:
        output_df = output_df[output_df["firstUserDefaultChannelGroup"].isin(firstUserDefaultChannelGroup_filter)]

    # Creating new & deleting avg columns on dataframe
    output_df['yearMonth'] = pd.to_datetime(output_df['yearMonth'], format='%Y%m')
    # output_df['yearMonth'] = pd.to_datetime(output_df['yearMonth'], format='%Y-%m-%d %H-%M-%S')
    output_df['yearMonth'] = output_df['yearMonth'].dt.strftime('%Y-%m %b')
    output_df['bounces'] = output_df['Sessions'] - output_df['engagedSessions']
    output_df['returningUsers'] = output_df['activeUsers'] - output_df['newUsers']
    output_df['SessionsDuration'] = output_df['averageSessionDuration'] * output_df['engagedSessions']

    # Rectifying data type
    output_df['activeUsers'] = output_df['activeUsers'].values.astype('int')
    output_df['newUsers'] = output_df['newUsers'].values.astype('int')
    
    return output_df

output_df = df_preparation(output_df=output_df, country_filter=country_filter, firstUserDefaultChannelGroup_filter=firstUserDefaultChannelGroup_filter)
comp_df = df_preparation(output_df=comp_df, country_filter=country_filter, firstUserDefaultChannelGroup_filter=firstUserDefaultChannelGroup_filter)

# st.divider()

tab1, tab2 = st.tabs(["Graphs", "Tables"])
with tab1:
    
    ## GRAPH 1 -- FUNNEL MARKETING
    # Aggregating absolute values on dimensions of interest
    st.subheader(f'\nFunnel Marketing Digital')
    funnel_chart_prep = output_df.copy()
    funnel_chart_prep = funnel_chart_prep.drop(columns=['averageSessionDuration', 'SessionsDuration'])
    funnel_chart_prep = funnel_chart_prep[['screenPageViews', 'Sessions', 'engagedSessions','activeUsers', 'newUsers', 'returningUsers']].sum()#agg('sum')
    funnel_chart_prep = funnel_chart_prep.rename({'screenPageViews':'Pages Vues', 'Sessions':'Sessions', 'activeUsers':'Utilisateurs Actifs',
                                                        'engagedSessions':'Sessions Engagées', 'newUsers':'Utilisateurs Nouveaux', 'returningUsers':'Utilisateurs Répétifs'})
    funnel_chart_prep = funnel_chart_prep.reset_index().rename(columns={0:'Nombre', 'index':'Étape'})
    fig = px.funnel(funnel_chart_prep, x='Nombre', y='Étape')
    st.plotly_chart(fig)

    st.divider()

    ## GRAPH 2
    st.subheader(f'\nUtilisateurs : Actifs, Nouveaux & Bounces')
    year_month_table = vs_LY(output_df=output_df, comp_df=comp_df)
    # st.write(year_month_table)
    base = alt.Chart(year_month_table).encode(
        x=alt.X('yearMonth:N', axis=alt.Axis(title='', format="YYYY MMM", formatType="YYYY MMM")),
        y=alt.Y('Sessions:Q', axis=alt.Axis(title=''))
        ) #.interactive() #, y2='sum(bounces)/count():Q')

    bar_active = base.mark_bar(color='blue', xOffset=-11, width=20).encode(y='activeUsers:Q')
    text_active = bar_active.mark_text(align='center', xOffset=-11, baseline='top', dx=0, color='white', size=10).encode(text='activeUsers:Q',
                x=alt.X('yearMonth:N', axis=alt.Axis(title='', format="YYYY MMM", formatType="YYYY MMM")),
                y=alt.Y('activeUsers:Q', stack='zero'),
                # y2=alt.Y2('bounceRate:Q', stack='zero'),
                )

    bar_new = base.mark_bar(color='green', opacity=1, xOffset=11, width=20).encode(y='newUsers:Q')
    text_new = bar_new.mark_text(align='center', xOffset=11, baseline='top', dx=0, color='white', size=10).encode(text='newUsers')
    
    bar_sessions = base.mark_bar(color='darkblue', opacity=1, xOffset=-11, width=20).encode(y=alt.Y('Sessions:Q', axis=alt.Axis(title='')))
    text_sessions = bar_sessions.mark_text(align='center', xOffset=-11, baseline='top', dx=0, color='white', size=10).encode(text='Sessions')

    alt.Color(value='lightgray')
    line_bounce = base.mark_line(color='#f93d48',dx=2).encode(y=alt.Y('bounces'), text='bounceRate_txt:N')  #.encode(y='sum(bounces)')
    # bar_bounce = base.mark_bar(color='red', opacity=0.75, xOffset=17, width=17).encode(y='bounces').encode(text='bounceRate_txt')
    text_bounce = line_bounce.mark_text(align='center', xOffset=0, baseline='bottom', dx=15, color='#fa8072', opacity=1, size=13).encode(text='bounceRate_txt')

    bar_users = st.altair_chart(bar_sessions + text_sessions + bar_new + text_new + bar_active + text_active + line_bounce + text_bounce,
                                # x_label='', y_label='',
                                # interactive=True,
                                theme="streamlit", use_container_width=True) # on_select="rerun")
    st.divider()
    
    ## GRAPHS 3, 4
    st.subheader(f'\nAcquisition par Canal')
    channel_prep = output_df.copy()
    channel_prep = channel_prep.groupby(['yearMonth', 'firstUserDefaultChannelGroup']).agg(engagedSessions=('engagedSessions', 'sum'),
                                                                                                activeUsers=('activeUsers','sum'))
    # st.write(channel_prep)
    channel_prep.reset_index(names=['yearMonth', 'firstUserDefaultChannelGroup'], inplace=True)
    channel_prep = channel_prep.rename(columns={'yearMonth':'Année - Mois','firstUserDefaultChannelGroup':' ', 'activeUsers':'Utilisateurs Actifs', 'engagedSessions':'Sessions Engagées'})
    channel_prep = channel_prep.sort_values('Année - Mois', ascending=False)
    
    # col1, col2 = st.columns(2)
    # with col1:
    st.markdown(f'\nUtilisateurs Actifs')
    st.bar_chart(channel_prep, x='Année - Mois', x_label='', y='Utilisateurs Actifs', y_label='', stack="normalize", color=' ', horizontal=True, use_container_width=True) #, x_label='Users Actifs'
    # with col2:
    st.markdown(f'\nSessions Engagées')
    st.bar_chart(channel_prep, x='Année - Mois', x_label='', y='Sessions Engagées', y_label='', stack="normalize", color=' ', horizontal=True, use_container_width=True) #, x_label='Sessions Engagées'
    

## GRAPH 5
with tab2:
    st.subheader(f'\nPrincipaux KPIs de Performance')
    year_month_table.sort_values('yearMonth', ascending=False, inplace=True)
    year_month_table.drop(columns=['engagedSessions','returningUsers','newUsers','bounces'], inplace=True)
    # st.write(year_month_table)
    # st.dataframe(data=year_month_table.style.highlight_max(axis=0,subset=['bounceRate'],color='red',).highlight_max(axis=0,subset=['engagedSessionsRate','newUsersRate','returningUsersRate'],color='#34a853'),
    st.dataframe(data=year_month_table, #.style.applymap(color_background, subset=['bounceRate','engagedSessionsRate','newUsersRate','returningUsersRate'])
                    height=None, hide_index=True,
                    column_order=['yearMonth','Sessions','engagedSessionsRate','bounceRate','activeUsers','returningUsersRate','newUsersRate','avgScreenViews','avgSessionDuration'],
                column_config={
        "yearMonth": st.column_config.DateColumn("Année - Mois", format="YYYY - MMM", pinned=True),
        "Sessions": st.column_config.ProgressColumn("Sessions", format="localized",min_value=0,max_value=max(year_month_table['Sessions'])),
        "engagedSessionsRate": st.column_config.NumberColumn("% Engagées",format="percent",min_value=0,max_value=1),
        # "bounces": st.column_config.NumberColumn("Bounces",format="localized",min_value=0),
        "bounceRate": st.column_config.NumberColumn("% Bounce",help="% of users exiting website as soon as landing",format="percent",min_value=0,max_value=1,width="small"),
        "activeUsers": st.column_config.ProgressColumn("Utilisateurs Actifs",format="localized",min_value=0,max_value=max(year_month_table['activeUsers'])),
        "returningUsersRate": st.column_config.NumberColumn("% Retour",format="percent",min_value=0,max_value=1),
        "newUsersRate": st.column_config.NumberColumn("% Nouveaux",format="percent",min_value=0,max_value=1),
        "avgScreenViews": st.column_config.NumberColumn("Moy. Pages Vues",format="localized",min_value=0),
        "avgSessionDuration": st.column_config.NumberColumn("Durée Moy. Session",format="localized",min_value=0),
    })

    # st.divider()
    
    
    ## GRAPH 6
    st.markdown(f"\nComparaison à l'Année Précédente")
    year_month_table.sort_values('yearMonth', ascending=False, inplace=True)

    # st.dataframe(data=year_month_table.style.applymap(color_background, subset=['Sessions_vs_LY','engagedSessions_vs_LY','bounces_vs_LY','activeUsers_vs_LY','returningUsers_vs_LY','newUsers_vs_LY']), #.style.highlight_max(axis=0,subset=['bounceRate'],color='red').highlight_max(axis=0,subset=['engagedSessionsRate','newUsersRate','returningUsersRate'],color='#34a853'),
    # year_month_table.style.set_properties(**{'text-align': 'center'}).set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
    # st.markdown('<style>.col_heading{text-align: center;}</style>', unsafe_allow_html=True)
    # year_month_table.columns = ['<div class="col_heading">'+col+'</div>' for col in year_month_table.columns] 
    
    cmap = plt.cm.get_cmap('PRGn')
    st.dataframe(data=year_month_table.style.background_gradient(cmap=cmap,vmin=-1,vmax=1,axis=None).applymap(color_background, subset=['Sessions_vs_LY','engagedSessions_vs_LY','bounces_vs_LY','activeUsers_vs_LY','returningUsers_vs_LY','newUsers_vs_LY']), #.set_properties(**{'text-align': 'center'}).set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
                    height=None, hide_index=True,
                    column_order=['yearMonth','Sessions_vs_LY','engagedSessions_vs_LY','bounces_vs_LY','activeUsers_vs_LY','returningUsers_vs_LY','newUsers_vs_LY'],
                column_config={
        "yearMonth": st.column_config.DateColumn("Année - Mois", format="YYYY - MMM", pinned=True),
        "Sessions_vs_LY": st.column_config.NumberColumn("Sessions vs LY", format="percent",min_value=0,max_value=1,width="small"),
        "engagedSessions_vs_LY": st.column_config.NumberColumn("Engagées vs LY",format="percent",min_value=0,max_value=1,width="small"),
        # "bounces": st.column_config.NumberColumn("Bounces",format="localized",min_value=0),
        "bounces_vs_LY": st.column_config.NumberColumn("Bounces vs LY",help="% of users exiting website as soon as landing",format="percent",min_value=0,max_value=1,width="small"),
        "activeUsers_vs_LY": st.column_config.NumberColumn("Utilisateurs vs LY",format="percent",min_value=0,max_value=1,width="small"),
        "returningUsers_vs_LY": st.column_config.NumberColumn("Retour vs LY",format="percent",min_value=0,max_value=1,width="small"),
        "newUsers_vs_LY": st.column_config.NumberColumn("Nouveaux vs LY",format="percent",min_value=0,max_value=1,width="small"),
        # "avgScreenViews": st.column_config.NumberColumn("Moy. Pages Vues",format="localized",min_value=0,width="small"),
        # "avgSessionDuration": st.column_config.NumberColumn("Durée Moy. Session",format="localized",min_value=0,width="small"),
    })

    st.divider()

    ## DISPLAY - MAIN STRUCTURE
    col1, col2, col3 = st.columns(3)

    landing_table, pages_table, countries_table = traffic_report(end_date_input, start_date_input, property_id, client)

    ## GRAPHS 7, 8, 9
    # with col1:
    # st.header(f'\nTop {str(top_results)} ...')
    st.subheader(f'\nTop {str(top_results)} Pays')
    countries_table.index += 1
    st.dataframe(countries_table[0:top_results],
                column_config={
            "country": st.column_config.TextColumn("Pays"),
            "activeUsers": st.column_config.ProgressColumn("Utilisateurs Actifs",format="localized",min_value=0,max_value=max(countries_table['activeUsers'][0:top_results])),
            "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(countries_table['engagedSessions'][0:top_results])),
            "averageSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(countries_table['averageSessionDuration'][0:top_results])),
            },)

    # with col2:
    st.subheader(f'\nTop {str(top_results)} Landing Pages')
    landing_table.index += 1
    st.dataframe(landing_table[0:top_results],
                column_config={
            "landingPage": st.column_config.TextColumn("Landing Page URL"),
            "activeUsers": st.column_config.ProgressColumn("Utilisateurs Actifs",format="localized",min_value=0,max_value=max(landing_table['activeUsers'][0:top_results])),
            "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(landing_table['engagedSessions'][0:top_results])),
            "averageSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(landing_table['averageSessionDuration'][0:top_results])),
            },)
            
    # with col3:
    st.subheader(f'\nTop {str(top_results)} Pages Visitées')
    pages_table.index += 1
    st.dataframe(pages_table[0:top_results],
                column_config={
            "pagePath": st.column_config.TextColumn("Adresse Page URL"),
            "activeUsers": st.column_config.ProgressColumn("Utilisateurs Actifs",format="localized",min_value=0,max_value=max(pages_table['activeUsers'][0:top_results])),
            "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(pages_table['engagedSessions'][0:top_results])),
            "averageSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(pages_table['averageSessionDuration'][0:top_results])),
            },)
