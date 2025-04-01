## STREAMLIT APP
import os
import dateutil
import pandas as pd
import streamlit as st
from functions import *
from datetime import date
import plotly_express as px
import matplotlib.pyplot as plt
from bokeh.plotting import figure
import streamlit.components.v1 as components
from google.analytics.data_v1beta import BetaAnalyticsDataClient
import warnings
warnings.filterwarnings("ignore")

## DATA COLLECTION
@st.cache_data
def request_data(_client, property_id, start_date_input, end_date_input):
    events_df = request_ga_key_events(_client, property_id, start_date_input, end_date_input)
    output_df = request_ga_data(_client, property_id, start_date_input, end_date_input, events_df)
    return output_df

def upload_data():
    property_id = "386101877"
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-analytics-viso-service-account.json'
    client = BetaAnalyticsDataClient()
    
    ## STREAMLIT APP - MAIN STRUCTURE
    st.set_page_config(layout="wide", initial_sidebar_state='auto', page_title='VISO MKT Digital', page_icon='images/viso-logo.svg')   # Use the full page instead of a narrow central column
    
    intro1, intro2 = st.columns([0.2, 0.8])
    with intro1:
        st.image('images/viso-logo.svg')
    with intro2:
        st.header("Tableau de Bord | Marketing Digital", divider='rainbow')

    # FILTERS SIDEBAR -- PART 1
    st.sidebar.header("Filtres", divider='rainbow')

    yesterday_date = date.today() - dateutil.relativedelta.relativedelta(days=1)
    one_year = yesterday_date - dateutil.relativedelta.relativedelta(months=11)

    start_date_input = st.sidebar.date_input("Date de Début d'Analyse", value=date(one_year.year, one_year.month, 1),
                                                min_value="2016-01-01", max_value=yesterday_date)
    end_date_input = st.sidebar.date_input("Date de Fin d'Analyse", value=yesterday_date, min_value=start_date_input, max_value=yesterday_date)

    start_date_comparison = date(start_date_input.year-1, start_date_input.month, start_date_input.day)
    end_date_comparison = date(end_date_input.year-1, end_date_input.month, end_date_input.day)
    st.sidebar.caption("Période de Comparaison:\ndu {}\nau {}".format(start_date_comparison.strftime("%d %B %Y"),end_date_comparison.strftime("%d %B %Y")))
    st.sidebar.divider()
        
    ## TABLE OUTPUT
    output_df = request_data(client, property_id, start_date_input, end_date_input)
    output_df = build_df_final(output_df)
    comp_df = request_data(client, property_id, start_date_comparison, end_date_comparison)
    comp_df['yearMonth'] = comp_df['yearMonth'].astype('int').apply(lambda x: x+100).astype('str')
    comp_df = build_df_final(comp_df)
    
    df_final = pd.merge(output_df, comp_df, how='outer', on=['yearMonth','country','firstUserDefaultChannelGroup'], suffixes=('','_LY'))
    pages_table = traffic_report(end_date_input, start_date_input, property_id, client)
    
    return df_final, pages_table
    
# FILTERS SIDEBAR -- PART 2
def filter_applications(df_final, pages_final):
    if "channel_filter" not in st.session_state:
        channel_filter = st.sidebar.multiselect("Canal d'Acquisition:", options=df_final['firstUserDefaultChannelGroup'].unique(), default=[])
    else:
        channel_filter = st.sidebar.multiselect("Canal d'Acquisition:", options=df_final['firstUserDefaultChannelGroup'].unique(), default=st.session_state["channel_filter"])
    if channel_filter:
        df_final = df_final[df_final["firstUserDefaultChannelGroup"].isin(channel_filter)]
        pages_final = pages_final[pages_final["firstUserDefaultChannelGroup"].isin(channel_filter)]
        
    country_df = df_final.groupby(by='country').agg(Visiteurs=('activeUsers','sum')).sort_values(by='Visiteurs', ascending=False).reset_index()
    country_list = country_df['country']
    if "country_filter" not in st.session_state:
        country_filter = st.sidebar.multiselect("Pays:", options=country_list, default=[])
    else:
        country_filter = st.sidebar.multiselect("Pays:", options=country_list, default=st.session_state["country_filter"])
    if country_filter:
        df_final = df_final[df_final["country"].isin(country_filter)]
        pages_final = pages_final[pages_final["country"].isin(country_filter)]
    
    if "date_filter" not in st.session_state:
        date_filter = []
    else:
        date_filter = st.session_state["date_filter"]
    if date_filter:
        df_final = df_final[df_final["yearMonth"].isin(date_filter)]
        pages_final = pages_final[pages_final["yearMonth"].isin(date_filter)]
        
    if "top_results" not in st.session_state:
        top_results = st.sidebar.slider("Nombre de résultats à afficher:", min_value=5, max_value=100, value=20, step=5)
    else:
        top_results = st.sidebar.slider("Nombre de résultats à afficher:", min_value=5, max_value=100, value=st.session_state["top_results"], step=5)
    
    if "counter" not in st.session_state:
        st.session_state.counter = 0
    
    st.sidebar.divider()
    st.sidebar.button("Download Excel Output", on_click=export_to_excel(df_final))
    
    return df_final, pages_final, top_results

# APPLYING FILTERS TO DATAFRAME
@st.cache_data
def build_all(df_final):
    yearMonth_agg = build_yearMonth(df_final)
    yearMonth_pivot = rename_cols_df(yearMonth_agg)
    funnel_df = build_funnel(df_final)
    channel_unpivot = build_channel(df_final)

    return df_final, funnel_df, yearMonth_agg, yearMonth_pivot, channel_unpivot #, landing_table, pages_table, countries_table

# MAIN APP
def main(df_final, pages_table, top_results): 
    # GLOBAL VARIABLES
    # Plotly_Standard_Colors = ["rgb(31, 119, 180)","rgb(255, 127, 14)","rgb(44, 160, 44)","rgb(214, 39, 40)","rgb(148, 103, 189)","rgb(140, 86, 75)","rgb(227, 119, 194)","rgb(127, 127, 127)","rgb(188, 189, 34)","rgb(23, 190, 207)"]
    
    color_discrete_map_type={"Visiteurs" : "rgba(0,0,255,100)", "Sessions" : "rgba(215,48,39,100)", "Prospects" : "#2aa198"}

    color_discrete_map_channels={ "1-Unassigned"        : "rgba(165,0,38,100)",   "2-Paid Search"    : "rgba(215,48,39,100)",
                                  "Unassigned"          : "rgba(165,0,38,100)",   "Paid Search"      : "rgba(215,48,39,100)",
                                  "3-Organic Shopping"  : "rgba(90,174,97,100)",   "4-Email"         : "rgba(253,174,97,100)",
                                  "Organic Shopping"    : "rgba(90,174,97,100)",   "Email"           : "rgba(253,174,97,100)",
                                  "5-Organic Social"    : "rgba(128,205,193,100)",   "6-Referral"    : "rgba(244,109,67,100)",
                                  "Organic Social"      : "rgba(128,205,193,100)",   "Referral"      : "rgba(244,109,67,100)",
                                  "7-Direct"            : "rgba(0,0,255,100)",   "8-Organic Search"  : "rgba(53,151,143,100)",
                                  "Direct"              : "rgba(0,0,255,100)",   "Organic Search"    : "rgba(53,151,143,100)"}
    # st.write(px.colors.diverging.swatches())
    # st.write(px.colors.DEFAULT_PLOTLY_COLORS)

    yearmonth_order=['2026-12 Dec', '2026-11 Nov', '2026-10 Oct', '2026-09 Sep', '2026-08 Aug', '2026-07 Jul', '2026-06 Jun', '2026-05 May', '2026-04 Apr', '2026-03 Mar', '2026-02 Feb', '2026-01 Jan', 
                     '2025-12 Dec', '2025-11 Nov', '2025-10 Oct', '2025-09 Sep', '2025-08 Aug', '2025-07 Jul', '2025-06 Jun', '2025-05 May', '2025-04 Apr', '2025-03 Mar', '2025-02 Feb', '2025-01 Jan', 
                     '2024-12 Dec', '2024-11 Nov', '2024-10 Oct', '2024-09 Sep', '2024-08 Aug', '2024-07 Jul', '2024-06 Jun', '2024-05 May', '2024-04 Apr', '2024-03 Mar', '2024-02 Feb', '2024-01 Jan', 
                     '2023-12 Dec', '2023-11 Nov', '2023-10 Oct', '2023-09 Sep', '2023-08 Aug', '2023-07 Jul', '2023-06 Jun', '2023-05 May', '2023-04 Apr', '2023-03 Mar', '2023-02 Feb', '2023-01 Jan', 
                     '2022-12 Dec', '2022-11 Nov', '2022-10 Oct', '2022-09 Sep', '2022-08 Aug', '2022-07 Jul', '2022-06 Jun', '2022-05 May', '2022-04 Apr', '2022-03 Mar', '2022-02 Feb', '2022-01 Jan', 
                     '2021-12 Dec', '2021-11 Nov', '2021-10 Oct', '2021-09 Sep', '2021-08 Aug', '2021-07 Jul', '2021-06 Jun', '2021-05 May', '2021-04 Apr', '2021-03 Mar', '2021-02 Feb', '2021-01 Jan', 
                     '2020-12 Dec', '2020-11 Nov', '2020-10 Oct', '2020-09 Sep', '2020-08 Aug', '2020-07 Jul', '2020-06 Jun', '2020-05 May', '2020-04 Apr', '2020-03 Mar', '2020-02 Feb', '2020-01 Jan']

    category_order_channels=["1-Unassigned","2-Paid Search","3-Organic Shopping","4-Organic Social","5-Email","6-Referral","7-Direct","8-Organic Search"]

    df_final, funnel_df, yearMonth_agg, yearMonth_pivot, channel_unpivot = build_all(df_final)
    
    # GRAPH 1 -- FUNNEL MARKETING
    st.subheader( 'Funnel Marketing Digital', divider='gray')
    fig_funnel = px.funnel(funnel_df, x='Nombre', y='Étape', hover_data='Nombre', color='Type', log_x=False, # log_x=activate_log,
                color_discrete_map=color_discrete_map_type,)
    fig_funnel.update_layout(font=dict(size=16),
                            margin = dict(b=0, t=0, l=0, r=0),)
    fig_funnel.update_xaxes(visible=False, title=None)
    fig_funnel.update_yaxes(visible=True, title=None, tickfont=dict(size=16))
    st.plotly_chart(fig_funnel)
    st.markdown("""_* Attention : informations en vert sur le catalogue et formulaire sont existantes seulement depuis mi-mars 2025._""", unsafe_allow_html=True)

    ## TABLE 1
    with st.expander("Comparaison versus l'Année Précédente", expanded=True):    
        # st.subheader(f"\nComparaison à l'Année Précédente")
        yearMonth_agg['Sessions_vs_LY'] = yearMonth_agg['Sessions_vs_LY'].apply(lambda x: x*100)
        yearMonth_agg['engagedSessions_vs_LY'] = yearMonth_agg['engagedSessions_vs_LY'].apply(lambda x: x*100)
        yearMonth_agg['bounces_vs_LY'] = yearMonth_agg['bounces_vs_LY'].apply(lambda x: x*100)
        yearMonth_agg['activeUsers_vs_LY'] = yearMonth_agg['activeUsers_vs_LY'].apply(lambda x: x*100)
        yearMonth_agg['returningUsers_vs_LY'] = yearMonth_agg['returningUsers_vs_LY'].apply(lambda x: x*100)
        yearMonth_agg['newUsers_vs_LY'] = yearMonth_agg['newUsers_vs_LY'].apply(lambda x: x*100)
        cmap = plt.cm.get_cmap('coolwarm_r')
        yearMonth_agg_evol = yearMonth_agg.copy()
        selected_yearMonth_evol = st.dataframe(data=yearMonth_agg_evol.style.background_gradient(cmap=cmap,vmin=-50,vmax=50,axis=None).applymap(color_font,
                        subset=['Sessions_vs_LY','engagedSessions_vs_LY','bounces_vs_LY','activeUsers_vs_LY','returningUsers_vs_LY','newUsers_vs_LY']), #.set_properties(**{'text-align': 'center'}).set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
                        height=None, hide_index=True, on_select="rerun",
                        column_order=['yearMonth','Sessions_vs_LY','engagedSessions_vs_LY','bounces_vs_LY','activeUsers_vs_LY','returningUsers_vs_LY','newUsers_vs_LY'],
                    column_config={
            "yearMonth": st.column_config.DateColumn("Année - Mois", format="YYYY - MMM", pinned=True),
            "Sessions_vs_LY": st.column_config.NumberColumn("Sessions vs LY", format='%+2.1f%%', min_value=-1,max_value=1),
            "engagedSessions_vs_LY": st.column_config.NumberColumn("Engagées vs LY",format='%+2.1f%%',min_value=-1,max_value=1),
            "bounces_vs_LY": st.column_config.NumberColumn("Bounces vs LY",format='%+2.1f%%',min_value=-1,max_value=1),
            "activeUsers_vs_LY": st.column_config.NumberColumn("Visiteurs vs LY",format='%+2.1f%%',min_value=-1,max_value=1),
            "returningUsers_vs_LY": st.column_config.NumberColumn("Retour vs LY",format='%+2.1f%%',min_value=-1,max_value=1),
            "newUsers_vs_LY": st.column_config.NumberColumn("Nouveaux vs LY",format='%+2.1f%%',min_value=-1,max_value=1),
        })
        if selected_yearMonth_evol:
            # date_filter = list(set([yearMonth_agg_evol['yearMonth'][x] for x in selected_yearMonth_evol['selection']['rows']]))
            st.session_state["date_filter"] = list(set([yearMonth_agg_evol['yearMonth'][x] for x in selected_yearMonth_evol['selection']['rows']]))

    st.write("##")

    ## GRAPH 2
    st.subheader(f'\nVisiteurs vs Sessions', divider='gray')
    minicol1, minicol2 = st.columns(2)
    with minicol1:
        components.html("""<div style="text-align: center; color: rgba(0,0,255,100); font-size:20px; weight:bold"> Visiteurs: Nouveaux vs de Retour </div>""", height=30)
    with minicol2:
        components.html("""<div style="text-align: center; color: rgba(215,48,39,100); font-size:20px"> Sessions: Engagées vs Bounces </div>""", height=30)
    
    yearMonth_pivot= pd.pivot_table(yearMonth_pivot.sort_values(by='yearMonth', ascending=False), values=['Sessions Engagées','Sessions Bounces','Visiteurs Nouveaux','Visiteurs de Retour'],
                                    index=['yearMonth'], aggfunc='sum').reset_index()
    yearMonth_pivot = yearMonth_pivot.melt(id_vars='yearMonth', value_vars=['Visiteurs Nouveaux','Visiteurs de Retour','Sessions Engagées','Sessions Bounces'], var_name="SubType", value_name="Nombre")
    yearMonth_pivot['Type'] = yearMonth_pivot['SubType'].map(lambda x: 'Visiteurs' if x[0:8]=='Visiteur' else 'Prospects' if x[0:8]=='Prospect' else 'Sessions')

    yearMonth_pivot.sort_values(by=['yearMonth','Nombre','Type', 'SubType'], ascending=[False, True, False, False], inplace=True)
    
    color_map_subtype = {"Visiteurs de Retour": 'rgba(0,0,255,100)',#"#2279CF",#"rgb(128, 177, 211)", #  "rgb(31, 119, 180)",
                         "Visiteurs Nouveaux": 'rgba(53,151,143,100)',# '#3366CC', #"rgb(31, 119, 180)",#  "rgb(23, 190, 207)",
                         "Sessions Bounces": "rgba(165,0,38,100)",
                         "Sessions Engagées": "rgba(255,0,0,100)",}
    
    visiteurs_vs_sessions = yearMonth_pivot.pivot_table(columns='yearMonth', index='Type', values='Nombre', aggfunc='sum') #.sum(axis=0).reset_index()

    st.dataframe(visiteurs_vs_sessions, column_order=yearmonth_order, hide_index=False, 
                 column_config = {'2025-03 Mar': {'alignment': 'center'},
                                  '2025-02 Feb': {'alignment': 'center'},
                                  '2025-01 Jan': {'alignment': 'center'},
                                  '2024-12 Dec': {'alignment': 'center'},
                                  '2024-11 Nov': {'alignment': 'center'},
                                  '2024-10 Oct': {'alignment': 'center'},
                                  '2024-09 Sep': {'alignment': 'center'},
                                  '2024-08 Aug': {'alignment': 'center'},
                                  '2024-07 Jul': {'alignment': 'center'},
                                  '2024-06 Jun': {'alignment': 'center'},
                                  '2024-05 May': {'alignment': 'center'},
                                  '2024-04 Apr': {'alignment': 'center'},
                                  '2024-03 Mar': {'alignment': 'center'},
                                  '2024-02 Feb': {'alignment': 'center'},
                                  '2024-01 Jan': {'alignment': 'center'},})
    
    fig_area = px.area(yearMonth_pivot, x='yearMonth', y="Nombre", text="Nombre", color="SubType", facet_row="Type", orientation='v', # log_y=activate_log,
                        color_discrete_map=color_map_subtype,
                        labels={'yearMonth': 'Année - Mois', 'Nombre': 'Nombre', 'Type': 'Utilisateur ou Séance'},)
    fig_area.update_layout(font=dict(size=14),
                            legend=dict(bgcolor='rgba(0,0,0,0)',title=None,yanchor="top",y=1.1,xanchor="left",x=0),
                            xaxis=dict(autorange=True, title=None, tickfont=dict(size=16)),
                            margin = dict(b=0, t=0, l=0, r=0),
                            paper_bgcolor=None)
    fig_area.update_xaxes(visible=True,title=None)
    fig_area.update_yaxes(visible=False,title=None)
    fig_area.update_traces(textposition='top center', textfont=dict(size=14,color='#000000'))#,weight="bold"))   #,color='#9C3587'
    st.plotly_chart(fig_area, use_container_width=True, theme="streamlit", on_select="rerun")

    ## TABLE 2
    with st.expander("Principaux KPIs de Performance", expanded=True):
        # st.subheader(f'\nPrincipaux KPIs de Performance', divider='gray')
        # yearMonth_agg = yearMonth_agg.set_index('yearMonth')
        yearMonth_agg_KPIs = yearMonth_agg.copy()
        selected_yearMonth_KPIs = st.dataframe(data=yearMonth_agg_KPIs.style.applymap(color_rate, subset=['bounceRate','engagedSessionsRate','newUsersRate','returningUsersRate']),
                        height=None, hide_index=True, on_select="rerun", 
                        column_order=['yearMonth','Sessions','engagedSessionsRate','bounceRate','activeUsers','returningUsersRate','newUsersRate','avgScreenViews','avgSessionDuration'],
                    column_config={
            "yearMonth": st.column_config.DateColumn("Année - Mois", format="YYYY - MMM", pinned=True),
            "Sessions": st.column_config.ProgressColumn("Sessions", format="localized",min_value=0,max_value=max(max(yearMonth_agg['Sessions']),0)), #
            "engagedSessionsRate": st.column_config.NumberColumn("% Engagées",format="percent",min_value=0,max_value=1),
            "bounceRate": st.column_config.NumberColumn("% Bounce",help="% of users exiting website as soon as landing",format="percent",min_value=0,max_value=1,width="small"),
            "activeUsers": st.column_config.ProgressColumn("Visiteurs",format="localized",min_value=0,max_value=max(yearMonth_agg['activeUsers'])),
            "returningUsersRate": st.column_config.NumberColumn("% Retour",format="percent",min_value=0,max_value=1),
            "newUsersRate": st.column_config.NumberColumn("% Nouveaux",format="percent",min_value=0,max_value=1),
            "avgScreenViews": st.column_config.NumberColumn("Moy. Pages Vues",format="localized",min_value=0),
            "avgSessionDuration": st.column_config.NumberColumn("Durée Moy. Session",format="localized",min_value=0),
        })
        if selected_yearMonth_KPIs:
            # date_filter = list(set([yearMonth_agg['yearMonth'][x] for x in selected_yearMonth_KPIs['selection']['rows']]))
            st.session_state["date_filter"] = list(set([yearMonth_agg['yearMonth'][x] for x in selected_yearMonth_KPIs['selection']['rows']]))

    st.write("##")
    
    ## GRAPHS 3, 4
    st.subheader(f'Acquisition de Visiteurs par Canal', divider='gray')
    activate_log = st.toggle("Échelle Logarithmique", value=True)

    channel_unpivot['Label'] = channel_unpivot['Nombre'].apply(lambda x: f'{x:.0f}' if x>0 else '')

    channel_unpivot_agg = channel_unpivot.groupby(by=['yearMonth']).agg(Visiteurs=('Nombre','sum')).sort_values(by='yearMonth', ascending=False).reset_index('yearMonth')
    # fig_line_channel = px.line(channel_unpivot_agg, x='yearMonth', y="Visiteurs", text="Visiteurs", log_y=activate_log, height=150) # orientation='v', 
    #                             #labels={'yearMonth': 'Année - Mois', 'Nombre': 'Nombre de Visiteurs'},
    # fig_line_channel.update_layout(font=dict(size=14, color='rgba(0,0,0,0)'),
    #                         margin = dict(b=0, t=0, l=0, r=0),)
    # fig_line_channel.update_xaxes(visible=False, autorange=True, title=None, type="category", categoryorder="category descending", categoryarray=yearmonth_order)
    # fig_line_channel.update_yaxes(visible=False, autorange=True, title=None, categoryorder="array", categoryarray=category_order_channels)
    # fig_line_channel.update_traces(textposition='top center', textfont=dict(size=14,color='#000000'))#,weight="bold"))   #,color='#9C3587'
    # st.plotly_chart(fig_line_channel, use_container_width=True, theme="streamlit", on_select="rerun")
    
    test = channel_unpivot_agg.pivot_table(columns='yearMonth', values='Visiteurs', aggfunc='sum') #.sum(axis=0).reset_index()

    st.dataframe(test, column_order=yearmonth_order, hide_index=True,
                 column_config = {'2025-12 Dec': {'alignment': 'center'}, '2024-12 Dec': {'alignment': 'center'}, '2023-12 Dec': {'alignment': 'center'}, '2022-12 Dec': {'alignment': 'center'}, '2021-12 Dec': {'alignment': 'center'}, '2020-12 Dec': {'alignment': 'center'},
                                  '2025-11 Nov': {'alignment': 'center'}, '2024-11 Nov': {'alignment': 'center'}, '2023-11 Nov': {'alignment': 'center'}, '2022-11 Nov': {'alignment': 'center'}, '2021-11 Nov': {'alignment': 'center'}, '2020-11 Nov': {'alignment': 'center'},
                                  '2025-10 Oct': {'alignment': 'center'}, '2024-10 Oct': {'alignment': 'center'}, '2023-10 Oct': {'alignment': 'center'}, '2022-10 Oct': {'alignment': 'center'}, '2021-10 Oct': {'alignment': 'center'}, '2020-10 Oct': {'alignment': 'center'},
                                  '2025-09 Sep': {'alignment': 'center'}, '2024-09 Sep': {'alignment': 'center'}, '2023-09 Sep': {'alignment': 'center'}, '2022-09 Sep': {'alignment': 'center'}, '2021-09 Sep': {'alignment': 'center'}, '2020-09 Sep': {'alignment': 'center'},
                                  '2025-08 Aug': {'alignment': 'center'}, '2024-08 Aug': {'alignment': 'center'}, '2023-08 Aug': {'alignment': 'center'}, '2022-08 Aug': {'alignment': 'center'}, '2021-08 Aug': {'alignment': 'center'}, '2020-08 Aug': {'alignment': 'center'},
                                  '2025-07 Jul': {'alignment': 'center'}, '2024-07 Jul': {'alignment': 'center'}, '2023-07 Jul': {'alignment': 'center'}, '2022-07 Jul': {'alignment': 'center'}, '2021-07 Jul': {'alignment': 'center'}, '2020-07 Jul': {'alignment': 'center'},
                                  '2025-06 Jun': {'alignment': 'center'}, '2024-06 Jun': {'alignment': 'center'}, '2023-06 Jun': {'alignment': 'center'}, '2022-06 Jun': {'alignment': 'center'}, '2021-06 Jun': {'alignment': 'center'}, '2020-06 Jun': {'alignment': 'center'},
                                  '2025-05 May': {'alignment': 'center'}, '2024-05 May': {'alignment': 'center'}, '2023-05 May': {'alignment': 'center'}, '2022-05 May': {'alignment': 'center'}, '2021-05 May': {'alignment': 'center'}, '2020-05 May': {'alignment': 'center'},
                                  '2025-04 Apr': {'alignment': 'center'}, '2024-04 Apr': {'alignment': 'center'}, '2023-04 Apr': {'alignment': 'center'}, '2022-04 Apr': {'alignment': 'center'}, '2021-04 Apr': {'alignment': 'center'}, '2020-04 Apr': {'alignment': 'center'},
                                  '2025-03 Mar': {'alignment': 'center'}, '2024-03 Mar': {'alignment': 'center'}, '2023-03 Mar': {'alignment': 'center'}, '2022-03 Mar': {'alignment': 'center'}, '2021-03 Mar': {'alignment': 'center'}, '2020-03 Mar': {'alignment': 'center'},
                                  '2025-02 Feb': {'alignment': 'center'}, '2024-02 Feb': {'alignment': 'center'}, '2023-02 Feb': {'alignment': 'center'}, '2022-02 Feb': {'alignment': 'center'}, '2021-02 Feb': {'alignment': 'center'}, '2020-02 Feb': {'alignment': 'center'},
                                  '2025-01 Jan': {'alignment': 'center'}, '2024-01 Jan': {'alignment': 'center'}, '2023-01 Jan': {'alignment': 'center'}, '2022-01 Jan': {'alignment': 'center'}, '2021-01 Jan': {'alignment': 'center'}, '2020-01 Jan': {'alignment': 'center'},
                                  })
    
    fig_area_channel = px.area(channel_unpivot, x='yearMonth', y="Nombre", text="Label", orientation='v',
                                log_y=activate_log, color='Channel', color_discrete_map=color_discrete_map_channels, 
                                labels={'yearMonth': 'Année - Mois', 'Nombre': 'Nombre de Visiteurs', 'Channel': 'Canal', 'Type': 'Utilisateur ou Séance'},
                                height=200)
    fig_area_channel.update_layout(font=dict(size=14, color='rgba(0,0,0,0)'),
                            yaxis = dict(title = "Année Mois", tickfont=dict(size=14), tickformat = "%Y-%m %b", categoryorder="category descending", categoryarray=yearmonth_order), #, tickformat = ".0%" , ticksuffix="%", categoryorder='array', categoryarray=category_order_channels
                            xaxis = dict(title = "Canal", tickfont=dict(size=14), categoryorder="array", categoryarray=category_order_channels),  #, categoryorder='array', categoryarray=category_order_channels
                            legend = dict(bgcolor='rgba(0,0,0,0)',title='Canal',yanchor="top",y=-3,xanchor="center",x=0, visible=False),
                            margin = dict(b=0, t=0, l=0, r=0),)
    fig_area_channel.update_xaxes(visible=False, autorange=True, title=None, type="category", categoryorder="category descending", categoryarray=yearmonth_order)
    fig_area_channel.update_yaxes(visible=False, autorange=True, title=None, categoryorder="array", categoryarray=category_order_channels)
    fig_area_channel.update_traces(textposition='top right', textfont=dict(size=14,color='#000000'))#,weight="bold"))   #,color='#9C3587'
    selected_yearMonth_channel_area = st.plotly_chart(fig_area_channel, use_container_width=True, theme="streamlit", on_select="rerun")
    if selected_yearMonth_channel_area:
        # channel_filter = list(set([x["legendgroup"] for x in selected_stacked_column['selection']['points']]))
        st.session_state["channel_filter"] = list(set([x["legendgroup"] for x in selected_yearMonth_channel_area['selection']['points']]))
        # st.write(st.session_state["channel_filter"])
    

    fig_stacked = px.histogram(channel_unpivot, x="yearMonth", y="Nombre", barmode='stack', orientation='v', barnorm='fraction', text_auto='.2%',  opacity=0.33,#, text_auto='.0%',        # log_x=True,    #, nbins=len(channel_unpivot['yearMonth'].unique())
                            log_y=activate_log, color='Channel', color_discrete_map=color_discrete_map_channels,
                            labels={'yearMonth': 'Année - Mois', 'Nombre': 'Nombre de Visiteurs', 'Channel': 'Canal', 'Type': 'Utilisateur ou Séance'},
                            height=600) #, facet_col="Type", facet_row_spacing=0)          #.apply("{:1f}%".format()))
    fig_stacked.update_layout(font=dict(size=14),
                            yaxis = dict(title = "Année Mois", tickfont=dict(size=14), tickformat = "%Y-%m %b", categoryorder="array", categoryarray=yearmonth_order), #, tickformat = ".0%" , ticksuffix="%", categoryorder='array', categoryarray=category_order_channels
                            xaxis = dict(title = "Canal", tickfont=dict(size=14), tickformat = '.1%', categoryorder="array", categoryarray=category_order_channels),  #, categoryorder='array', categoryarray=category_order_channels
                            legend = dict(bgcolor='rgba(0,0,0,0)',title='Canal',yanchor="bottom",y=-1000,xanchor="left",x=0, visible=True),
                            margin = dict(b=0, t=0, l=0, r=0),)
    fig_stacked.update_coloraxes(colorbar_tickmode='array', colorbar_tickvals=category_order_channels)
    fig_stacked.update_xaxes(visible=False, autorange=True, title=None, type='category', categoryorder="category descending", categoryarray=category_order_channels, tickformat='%Y-%m %b')   # uniformtext_mode='show')
    fig_stacked.update_yaxes(visible=False, autorange=True, title=None, categoryorder="array", categoryarray=category_order_channels)
    fig_stacked.update_traces(textposition='inside', textfont=dict(size=14,color='#000000'))#,weight="bold"))   #,color='#9C3587'
    selected_yearMonth_channel_stacked = st.plotly_chart(fig_stacked, use_container_width=True, theme="streamlit", on_select="rerun")
    if selected_yearMonth_channel_stacked:
        # channel_filter = list(set([x["legendgroup"] for x in selected_yearMonth_channel_stacked['selection']['points']]))
        st.session_state["channel_filter"] = list(set([x["legendgroup"] for x in selected_yearMonth_channel_stacked['selection']['points']]))
    st.write("##")
        
    ## TABLE 3
    countries_table = df_final.groupby(by=['country']).agg(Visiteurs=('activeUsers','sum'), Sessions=('Sessions','sum'), engagedSessions=('engagedSessions','sum'), SessionsDuration=('SessionsDuration','sum'), screenPageViews=('screenPageViews','sum')
                                                    ).sort_values(by='Visiteurs', ascending=False
                                                    ).reset_index()
    countries_table['avgSessionDuration'] = (countries_table['SessionsDuration'] / countries_table['Sessions']).round(0)
    countries_table['avgPageViews'] = (countries_table['screenPageViews'] / countries_table['Visiteurs']).round(1)
    countries_table.drop(columns=['SessionsDuration','Sessions','screenPageViews'], inplace=True)
    top_results_label = min(top_results, len(countries_table))
    st.subheader(f'\nTop {str(top_results_label)} Pays', divider='gray')
    countries_table.index += 1
    if len(countries_table) > 0:
        selected_countries = st.dataframe(countries_table[0:top_results_label],column_order=["country", "Visiteurs", "engagedSessions", "avgSessionDuration",'avgPageViews'], height=37*top_results_label,
                    on_select="rerun",
                    column_config={
                "country": st.column_config.TextColumn("Pays"),
                "Visiteurs": st.column_config.ProgressColumn("Visiteurs",format="localized",min_value=0,max_value=max(countries_table['Visiteurs'][0:top_results_label])),
                "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(countries_table['engagedSessions'][0:top_results_label])),
                "avgSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(countries_table['avgSessionDuration'][0:top_results_label])),
                "avgPageViews": st.column_config.ProgressColumn("Moy. Pages Vues",format="localized",min_value=0,max_value=max(countries_table['avgPageViews'][0:top_results_label])),
                },)
    if selected_countries:
        # country_filter = list(set([countries_table['country'][x] for x in selected_countries['selection']['rows']]))
        # st.write(list(set([countries_table['country'][x] for x in selected_countries['selection']['rows']])))
        st.session_state["country_filter"] = list(set([countries_table['country'][x] for x in selected_countries['selection']['rows']]))
        # st.rerun()
        

    ## TABLE 4
    chosen_variable = 'Produits Vus'
    st.subheader(f'\nTop {str(top_results)} {chosen_variable}', divider='gray')
    pages_final = pages_table_transformation(pages_table)
    pages_exclues = list(set([x for x in pages_final['pagePath'] if 'produit' in x or 'products' in x or '/content/' in x or 'catalog' in x or 'contact' in x or 'connexion' in x or '/private/' in x]))
    pages_exclues = pages_exclues + ['/fr/', '/en/', '/nl/', '/fr/recherche', '/fr/6-equipement-interieur', '/fr/3-prevention-des-risques', '/fr/43-stockage-et-manutention', '/fr/25-amenagement-exterieur', '/fr/11-industrie', '/fr/28-amenagement-de-parking', '/fr/16-amenagements-industriels', '/en/connexion',
                                    'Index.php', '/en/recherche', '/fr/133-voirie-et-parking', '/img/cms/Catalogue_Nouveautés_SIGN_2020-.pdf', '/fr/152-industrie', '/fr/ODMtbWFsbG', ]
    pages_produits = st.toggle("Pages Produits (exclusion des pages de navigation)", value=True)
    if pages_produits:
        chosen_variable = 'Pages Produits Vus'
        pages_final = pages_final[(~pages_final['pagePath'].isin(pages_exclues))]
        pages_final['product'] = pages_final['product'].str.strip(' ')
        pages_final['output'] = pages_final['product'].values.astype(str)
        pages_final['output'].dropna(inplace=True)
    else:
        chosen_variable = 'Pages URL Visitées'
        pages_final['output'] = pages_final['pagePath'].values.astype(str)
        
    top_results_label = min(top_results, len(pages_final))
    pages_final.reset_index(inplace=True)
    pages_final.index += 1
    
    pages_final['avgPageViews'] = (pages_final['screenPageViews'] / pages_final['activeUsers']).round(1)
    pages_final.drop(columns=['SessionsDuration','Sessions','screenPageViews'], inplace=True)
    if len(pages_final) > 0:
        st.dataframe(pages_final[0:top_results_label],column_order=["output", "activeUsers", "engagedSessions", "avgSessionDuration",'avgPageViews'], height=37*top_results_label,
                    on_select="rerun",
                    column_config={
                "output": st.column_config.TextColumn(chosen_variable),
                "activeUsers": st.column_config.ProgressColumn("Visiteurs",format="localized",min_value=0,max_value=max(pages_final['activeUsers'][0:top_results_label])),
                "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(pages_final['engagedSessions'][0:top_results_label])),
                "avgSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(pages_final['avgSessionDuration'][0:top_results_label])),
                "avgPageViews": st.column_config.ProgressColumn("Moy. Pages Vues",format="localized",min_value=0,max_value=max(pages_final['avgPageViews'][0:top_results_label])),
                },)

if __name__ == "__main__":
    df_final, pages_table = upload_data()
    df_final, pages_final, top_results = filter_applications(df_final, pages_table)
    main(df_final, pages_final, top_results)
