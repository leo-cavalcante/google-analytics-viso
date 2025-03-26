## STREAMLIT APP
import os
import pages as pg
import dateutil
from functions import *
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_navigation_bar import st_navbar
from datetime import date
import plotly_express as px
import matplotlib.pyplot as plt
from bokeh.plotting import figure
import streamlit.components.v1 as components
from google.analytics.data_v1beta import BetaAnalyticsDataClient
import warnings
import base64
warnings.filterwarnings("ignore")

## STREAMLIT APP - MAIN STRUCTURE
property_id = "386101877"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-analytics-viso-service-account.json'
client = BetaAnalyticsDataClient()
st.set_page_config(layout="wide", initial_sidebar_state='auto', page_title='VISO MKT Digital', page_icon='viso-logo.svg')   # Use the full page instead of a narrow central column

# GLOBAL VARIABLES
color_discrete_map_type={"Users" : "#2279CF", "Sessions" : "salmon", "Prospects" : "#2aa198"}

color_discrete_map_channels={"Unassigned"   : "#dc322f",  "Paid Search"  : "#b58900",
                            "Email"         : "#6c71c4",  "Referral"        :"#859900",
                            "Organic Shopping":"#d33682", "Organic Social"  :"#cb4b16",
                            "Direct"          :"#268bd2", "Organic Search": "#2aa198"}

yearmonth_order=['2026 Dec', '2026 Nov', '2026 Oct', '2026 Sep', '2026 Aug', '2026 Jul', '2026 Jun', '2026 May', '2026 Apr', '2026 Mar', '2026 Feb', '2026 Jan', 
    '2025 Dec', '2025 Nov', '2025 Oct', '2025 Sep', '2025 Aug', '2025 Jul', '2025 Jun', '2025 May', '2025 Apr', '2025 Mar', '2025 Feb', '2025 Jan', 
    '2024 Dec', '2024 Nov', '2024 Oct', '2024 Sep', '2024 Aug', '2024 Jul', '2024 Jun', '2024 May', '2024 Apr', '2024 Mar', '2024 Feb', '2024 Jan', 
    '2023 Dec', '2023 Nov', '2023 Oct', '2023 Sep', '2023 Aug', '2023 Jul', '2023 Jun', '2023 May', '2023 Apr', '2023 Mar', '2023 Feb', '2023 Jan', 
    '2022 Dec', '2022 Nov', '2022 Oct', '2022 Sep', '2022 Aug', '2022 Jul', '2022 Jun', '2022 May', '2022 Apr', '2022 Mar', '2022 Feb', '2022 Jan', 
    '2021 Dec', '2021 Nov', '2021 Oct', '2021 Sep', '2021 Aug', '2021 Jul', '2021 Jun', '2021 May', '2021 Apr', '2021 Mar', '2021 Feb', '2021 Jan', 
    '2020 Dec', '2020 Nov', '2020 Oct', '2020 Sep', '2020 Aug', '2020 Jul', '2020 Jun', '2020 May', '2020 Apr', '2020 Mar', '2020 Feb', '2020 Jan']

channels_map={"Unassigned"   : "1", "Paid Search"       : "2",
            "Email"         : "3" , "Referral"        :"4",
            "Organic Shopping":"5", "Organic Social"  :"6",
            "Direct"          :"7", "Organic Search": "8"}

category_order_channels=["1-Unassigned","2-Paid Search","3-Email","4-Referral","5-Organic Shopping","5-Organic Social","7-Direct","8-Organic Search"]
# category_order_channels=["Unassigned","Paid Search","Email","Referral","Organic Shopping","Organic Social","Direct","Organic Search"]

# output_df = st.session_state.output_df
# comp_df = st.session_state.comp_df
    
intro1, intro2 = st.columns([0.2, 0.8])
with intro1:
    st.image('viso-logo.svg')
with intro2:
    st.header("Tableau de Bord | Marketing Digital", divider='rainbow')

# FILTERS SIDEBAR -- PART 1
st.sidebar.subheader("Filtres", divider='gray')
activate_log = st.sidebar.toggle("Échelle Logarithmique")

st.sidebar.divider()

one_year = date.today() - dateutil.relativedelta.relativedelta(months=11)
start_date_input = st.sidebar.date_input("Date de Début d'Analyse", value=date(one_year.year, one_year.month, 1),
                                            min_value="2016-01-01", max_value=date(date.today().year, date.today().month, date.today().day-1))
end_date_input = st.sidebar.date_input("Date de Fin d'Analyse", value="today", min_value=start_date_input,
                                            max_value=date(date.today().year, date.today().month, date.today().day-1))
no_days = end_date_input - start_date_input

start_date_comparison = date(start_date_input.year-1, start_date_input.month, start_date_input.day)
end_date_comparison = date(end_date_input.year-1, end_date_input.month, end_date_input.day)
no_days_comparison = end_date_comparison - start_date_comparison
st.sidebar.caption("Période de Comparaison:\ndu {}\nau {}".format(start_date_comparison.strftime("%d %B %Y"),end_date_comparison.strftime("%d %B %Y")))
st.sidebar.divider()

## DATA COLLECTION
@st.cache_data
def request_all_data(_client, property_id, start_date_input=start_date_input, end_date_input=end_date_input):
    request_events = request_ga_key_events(property_id, start_date_input, end_date_input)
    events_df = format_report(client, request_events)
    
    events_df = pd.pivot_table(events_df, index=['yearMonth', 'country', 'firstUserDefaultChannelGroup'],
                       columns=['eventName'], values='keyEvents', aggfunc="sum")
    events_df = events_df.fillna(0).reset_index()
    
    events_df['download'] = [0] * len(events_df.index)
    if 'téléchargement_catalogue_sign' in events_df.columns:
        events_df['download'] += events_df['téléchargement_catalogue_sign']
        events_df.drop(columns='téléchargement_catalogue_sign',inplace=True)
    if 'télécharger_catalogue_chain' in events_df.columns:
        events_df['download'] += events_df['télécharger_catalogue_chain']
        events_df.drop(columns='télécharger_catalogue_chain',inplace=True)
    if 'télécharger_catalogue_storage' in events_df.columns:
        events_df['download'] += events_df['télécharger_catalogue_storage']
        events_df.drop(columns={'télécharger_catalogue_storage'},inplace=True)
    
    # st.write(events_df)
    request = request_ga_data(property_id, start_date_input, end_date_input)
    output_df = format_report(client, request)
    output_df = pd.merge(output_df, events_df, how='outer', on=['yearMonth', 'country', 'firstUserDefaultChannelGroup'], suffixes=('','_event'))
    
    output_df['returningUsers'] = output_df['activeUsers'] - output_df['newUsers']
    output_df['bounces'] = output_df['Sessions'] - output_df['engagedSessions']
    output_df['SessionsDuration'] = output_df['averageSessionDuration'] * output_df['engagedSessions']

    return output_df
    
## TABLE OUTPUT
output_df = request_all_data(client, property_id, start_date_input, end_date_input)
output_df = build_df_final(output_df)
comp_df = request_all_data(client, property_id, start_date_input=start_date_comparison, end_date_input=end_date_comparison)
comp_df['yearMonth'] = comp_df['yearMonth'].astype('int').apply(lambda x: x+100).astype('str')
comp_df = build_df_final(comp_df)

# FILTERS SIDEBAR -- PART 2
country_filter = st.sidebar.multiselect("Pays:", options=output_df['country'].unique())
firstUserDefaultChannelGroup_filter = st.sidebar.multiselect("Canal d'Acquisition:", options=output_df['firstUserDefaultChannelGroup'].unique())
st.sidebar.divider()
top_results = st.sidebar.slider("Nombre de TOP résultats à afficher:", min_value=5, max_value=50, value=10, step=5)
st.sidebar.divider()
st.sidebar.button("Download Excel Output", on_click=export_to_excel(output_df))

# APPLYING FILTERS TO DATAFRAME
# output_df = df_preparation(output_df=output_df, country_filter=country_filter, firstUserDefaultChannelGroup_filter=firstUserDefaultChannelGroup_filter)
if country_filter:
    output_df = output_df[output_df["country"].isin(country_filter)]
if firstUserDefaultChannelGroup_filter:
    output_df = output_df[output_df["firstUserDefaultChannelGroup"].isin(firstUserDefaultChannelGroup_filter)]

df_final = pd.merge(output_df, comp_df, how='outer', on=['yearMonth','country','firstUserDefaultChannelGroup'], suffixes=('','_LY'))

tab1, tab2 = st.tabs(["GRAPHES", "TABLEAUX"])
with tab1:
    ## GRAPH 1 -- FUNNEL MARKETING
    st.subheader( 'Funnel Marketing Digital', divider='gray')
    funnel_df = build_funnel(df_final)
    fig_funnel = px.funnel(funnel_df, x='Nombre', y='Étape', hover_data='Nombre', color='Type', log_x=activate_log,
                color_discrete_map=color_discrete_map_type,)
    fig_funnel.update_layout(font=dict(size=16))
    fig_funnel.update_xaxes(visible=True, title=None)
    fig_funnel.update_yaxes(visible=True, title=None, tickfont=dict(size=16))
    st.plotly_chart(fig_funnel)


    ## GRAPH 2
    st.subheader(f'\nUsers vs Sessions', divider='gray')
    minicol1, minicol2 = st.columns(2)
    with minicol1:
        components.html("""<div style="text-align: center; color: #2279CF"> Nouveaux vs de Retour </div>""", height=24)
    with minicol2:
        components.html("""<div style="text-align: center; color: salmon"> Engagées vs Bounces </div>""", height=24)

    
    yearMonth_agg = build_yearMonth(df_final)
    
    yearMonth_pivot = rename_cols_df(yearMonth_agg)
    
    yearMonth_pivot= pd.pivot_table(yearMonth_pivot.sort_values(by='yearMonth', ascending=False), values=['Sessions Engagées','Bounces','Users Nouveaux','Users de Retour'],
                                   index=['yearMonth'], aggfunc='sum').reset_index()
    yearMonth_pivot = yearMonth_pivot.melt(id_vars='yearMonth', value_vars=['Users Nouveaux','Users de Retour','Sessions Engagées','Bounces'], var_name="SubType", value_name="Nombre")
    yearMonth_pivot['Type'] = yearMonth_pivot['SubType'].map(lambda x: 'Users' if x[0:5]=='Users' else 'Sessions')
    
    fig_area = px.area(yearMonth_pivot, x='yearMonth', y="Nombre", text="Nombre", color="SubType", facet_row="Type",
                      labels={'yearMonth': 'Année - Mois', 'Nombre': 'Nombre', 'Type': 'Utilisateur ou Séance'},)
    fig_area.update_layout(font=dict(size=14),
                          legend=dict(bgcolor='rgba(0,0,0,0)',title=None,yanchor="top",y=1.1,xanchor="left",x=0),
                          xaxis=dict(autorange="reversed"),
                          paper_bgcolor=None)
    fig_area.update_xaxes(visible=True,title=None)
    fig_area.update_yaxes(visible=True,title=None)
    fig_area.update_traces(textposition='top center', textfont=dict(size=14,color='#9C3587'))#,weight="bold"))   #,color='#9C3587'
    st.plotly_chart(fig_area, use_container_width=True, theme="streamlit", on_select="rerun")
    
    
    ## GRAPHS 3, 4
    st.subheader(f'\nAcquisition par Canal',divider='gray')
    st.text("Canaux d'Acquisition d'Users et des Sessions")
    
    channel_unpivot = build_channel(df_final)
    
    fig_stacked = px.histogram(channel_unpivot, log_x=activate_log, y="yearMonth", x="Nombre", barmode='stack', orientation='h', barnorm='fraction', text_auto='.1%', #, text_auto='.0%',        # log_x=True,    #, nbins=len(channel_unpivot['yearMonth'].unique())
                               color='Channel', color_discrete_map=color_discrete_map_channels, height=1000, facet_row="Type", facet_row_spacing=0)          #.apply("{:1f}%".format()))
    fig_stacked.update_layout(font=dict(size=14),
                            # title={"text": "Canaux d'Acquisition d'Users et des Sessions", "x": 0},
                            yaxis = dict(title = "Année Mois", tickfont=dict(size=14), tickformat = "%Y-%m %b", categoryorder="array", categoryarray=yearmonth_order), #, tickformat = ".0%" , ticksuffix="%", categoryorder='array', categoryarray=category_order_channels
                            xaxis = dict(autorange=True, tickfont=dict(size=14), tickformat = ".1%", categoryorder="array", categoryarray=category_order_channels),  #, categoryorder='array', categoryarray=category_order_channels
                            legend = dict(bgcolor='rgba(0,0,0,0)',title='Canal',yanchor="bottom",y=-0.25,xanchor="left",x=0))
    fig_stacked.update_coloraxes(colorbar_tickmode='array', colorbar_tickvals=category_order_channels)
    fig_stacked.update_yaxes(visible=True, title=None, type='category', categoryorder="category ascending", categoryarray=category_order_channels,tickformat='%Y-%m %b')   # uniformtext_mode='show')
    fig_stacked.update_xaxes(visible=False, title=None, categoryorder="array", categoryarray=category_order_channels)
    st.plotly_chart(fig_stacked, use_container_width=True, theme="streamlit", on_select="rerun")
    
    
## TABLE 1
with tab2:
    st.subheader(f'\nPrincipaux KPIs de Performance', divider='gray')
    st.dataframe(data=yearMonth_agg.style.applymap(color_rate, subset=['bounceRate','engagedSessionsRate','newUsersRate','returningUsersRate']),
                    height=None, hide_index=True, on_select="rerun",
                    column_order=['yearMonth','Sessions','engagedSessionsRate','bounceRate','activeUsers','returningUsersRate','newUsersRate','avgScreenViews','avgSessionDuration'],
                column_config={
        "yearMonth": st.column_config.DateColumn("Année - Mois", format="YYYY - MMM", pinned=True),
        "Sessions": st.column_config.ProgressColumn("Sessions", format="localized",min_value=0,max_value=max(max(yearMonth_agg['Sessions']),0)), #
        "engagedSessionsRate": st.column_config.NumberColumn("% Engagées",format="percent",min_value=0,max_value=1),
        "bounceRate": st.column_config.NumberColumn("% Bounce",help="% of users exiting website as soon as landing",format="percent",min_value=0,max_value=1,width="small"),
        "activeUsers": st.column_config.ProgressColumn("Users Actifs",format="localized",min_value=0,max_value=max(yearMonth_agg['activeUsers'])),
        "returningUsersRate": st.column_config.NumberColumn("% Retour",format="percent",min_value=0,max_value=1),
        "newUsersRate": st.column_config.NumberColumn("% Nouveaux",format="percent",min_value=0,max_value=1),
        "avgScreenViews": st.column_config.NumberColumn("Moy. Pages Vues",format="localized",min_value=0),
        "avgSessionDuration": st.column_config.NumberColumn("Durée Moy. Session",format="localized",min_value=0),
    })
    
    
    ## TABLE 2
    st.markdown(f"\nComparaison à l'Année Précédente")
    yearMonth_agg.sort_values('yearMonth', ascending=False, inplace=True)
    
    cmap = plt.cm.get_cmap('PiYG')
    # cmap = plt.cm.get_cmap('PRGn')
    st.dataframe(data=yearMonth_agg.style.background_gradient(cmap=cmap,vmin=-1,vmax=1,axis=None).applymap(color_background, subset=['Sessions_vs_LY','engagedSessions_vs_LY','bounces_vs_LY','activeUsers_vs_LY','returningUsers_vs_LY','newUsers_vs_LY']), #.set_properties(**{'text-align': 'center'}).set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
                    height=None, hide_index=True, on_select="rerun",
                    column_order=['yearMonth','Sessions_vs_LY','engagedSessions_vs_LY','bounces_vs_LY','activeUsers_vs_LY','returningUsers_vs_LY','newUsers_vs_LY'],
                column_config={
        "yearMonth": st.column_config.DateColumn("Année - Mois", format="YYYY - MMM", pinned=True),
        "Sessions_vs_LY": st.column_config.NumberColumn("Sessions vs LY", format="percent",min_value=0,max_value=1),
        "engagedSessions_vs_LY": st.column_config.NumberColumn("Engagées vs LY",format="percent",min_value=0,max_value=1),
        "bounces_vs_LY": st.column_config.NumberColumn("Bounces vs LY",help="% of users exiting website as soon as landing",format="percent",min_value=0,max_value=1),
        "activeUsers_vs_LY": st.column_config.NumberColumn("Users vs LY",format="percent",min_value=0,max_value=1),
        "returningUsers_vs_LY": st.column_config.NumberColumn("Retour vs LY",format="percent",min_value=0,max_value=1),
        "newUsers_vs_LY": st.column_config.NumberColumn("Nouveaux vs LY",format="percent",min_value=0,max_value=1),
    })

    ## DISPLAY - MAIN STRUCTURE
    col1, col2, col3 = st.columns(3)

    landing_table, pages_table, countries_table = traffic_report(end_date_input, start_date_input, property_id, client, country_filter, firstUserDefaultChannelGroup_filter)

    ## TABLES 3, 4, 5
    st.subheader(f'\nTop {str(top_results)} Pays', divider='gray')
    countries_table.index += 1
    st.dataframe(countries_table[0:top_results],
                column_config={
            "country": st.column_config.TextColumn("Pays"),
            "activeUsers": st.column_config.ProgressColumn("Users Actifs",format="localized",min_value=0,max_value=max(countries_table['activeUsers'][0:top_results])),
            "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(countries_table['engagedSessions'][0:top_results])),
            "averageSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(countries_table['averageSessionDuration'][0:top_results])),
            },)

    # with col2:
    st.subheader(f'\nTop {str(top_results)} Landing Pages', divider='gray')
    landing_table.index += 1
    st.dataframe(landing_table[0:top_results],
                column_config={
            "landingPage": st.column_config.TextColumn("Landing Page URL"),
            "activeUsers": st.column_config.ProgressColumn("Users Actifs",format="localized",min_value=0,max_value=max(landing_table['activeUsers'][0:top_results])),
            "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(landing_table['engagedSessions'][0:top_results])),
            "averageSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(landing_table['averageSessionDuration'][0:top_results])),
            },)
            
    # with col3:
    st.subheader(f'\nTop {str(top_results)} Pages Visitées', divider='gray')
    pages_table.index += 1
    st.dataframe(pages_table[0:top_results],
                column_config={
            "pagePath": st.column_config.TextColumn("Adresse Page URL"),
            "activeUsers": st.column_config.ProgressColumn("Users Actifs",format="localized",min_value=0,max_value=max(pages_table['activeUsers'][0:top_results])),
            "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(pages_table['engagedSessions'][0:top_results])),
            "averageSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(pages_table['averageSessionDuration'][0:top_results])),
            },)
