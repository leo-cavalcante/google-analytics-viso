import os
import datetime
import dateutil
from main import *
import altair as alt
import pandas as pd
import streamlit as st
from datetime import date
import plotly_express as px
import matplotlib.pyplot as plt
from bokeh.plotting import figure
import streamlit.components.v1 as components
from google.analytics.data_v1beta import BetaAnalyticsDataClient
# set_page_config()

# GLOBAL VARIABLES
property_id = "386101877"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-analytics-viso-service-account.json'
client = BetaAnalyticsDataClient()
# output_df = st.session_state.output_df
# comp_df = st.session_state.comp_df
    
## STREAMLIT APP - MAIN STRUCTURE
st.set_page_config(layout="wide", initial_sidebar_state='collapsed', page_icon='viso-logo.jpg', page_title='VISO MKT Digital')   # Use the full page instead of a narrow central column

intro1, intro2 = st.columns([0.25, 0.75])
with intro1:
    st.image('viso-logo.jpg')
with intro2:
    st.header("Tableau de Bord | Marketing Digital", divider='rainbow')

# FILTERS SIDEBAR -- PART 1
st.sidebar.subheader("Filtres", divider='gray')

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
def request_df_and_comp(_client, property_id, start_date_input=start_date_input, end_date_input=end_date_input, start_date_comparison=start_date_comparison, end_date_comparison=end_date_comparison):
    request = request_ga_data(property_id, start_date_input, end_date_input)
    output_df = format_report(client, request)
    
    request_comp = request_ga_data(property_id, start_date_comparison, end_date_comparison)
    comp_df = format_report(client, request_comp)
    
    output_df[['activeUsers','newUsers','Sessions','engagedSessions','screenPageViews','averageSessionDuration']] = output_df[['activeUsers','newUsers','Sessions','engagedSessions','screenPageViews','averageSessionDuration']].fillna(0)
    comp_df[['activeUsers','newUsers','Sessions','engagedSessions','screenPageViews','averageSessionDuration']] = comp_df[['activeUsers','newUsers','Sessions','engagedSessions','screenPageViews','averageSessionDuration']].fillna(0)
    comp_df['yearMonth'] = comp_df['yearMonth'].map(lambda x: str(int(x)+100))
    
    return output_df, comp_df
    
## TABLE OUTPUT
output_df, comp_df = request_df_and_comp(client, property_id, start_date_input, end_date_input, start_date_comparison, end_date_comparison)

# FILTERS SIDEBAR -- PART 2
country_filter = st.sidebar.multiselect("Pays:", options=output_df['country'].unique())
firstUserDefaultChannelGroup_filter = st.sidebar.multiselect("Canal d'Acquisition:", options=output_df['firstUserDefaultChannelGroup'].unique())
st.sidebar.divider()
top_results = st.sidebar.slider("Nombre de TOP résultats à afficher:", min_value=5, max_value=50, value=10, step=5)
st.sidebar.divider()
st.sidebar.button("Download Excel Output", on_click=export_to_excel(output_df))
# st.sidebar.download_button("Download Excel Output", data=output_df, file_name=date.today().strftime("%Y-%m-%d at %H-%m-%s") + '.xlsx', on_click=export_to_excel(output_df))

# APPLYING FILTERS TO DATAFRAME
output_df = df_preparation(output_df=output_df, country_filter=country_filter, firstUserDefaultChannelGroup_filter=firstUserDefaultChannelGroup_filter)
comp_df = df_preparation(output_df=comp_df, country_filter=country_filter, firstUserDefaultChannelGroup_filter=firstUserDefaultChannelGroup_filter)

tab1, tab2 = st.tabs(["Graphs", "Tables"])
with tab1:
    ## GRAPH 1 -- FUNNEL MARKETING
    st.header( 'Funnel Marketing Digital',divider='gray')
    funnel_chart = build_funnel(output_df)
    fig_funnel = px.funnel(funnel_chart, x='Nombre', y='Étape')
    fig_funnel.update_layout(font=dict(size=14))
    fig_funnel.update_yaxes(visible=True,title=None, tickfont=dict(size=14))#"Utilisateurs ou Sessions")
    st.plotly_chart(fig_funnel)


    ## GRAPH 2
        # components.html("""<div style="text-align: center; font-size: 36px"> Utilisateurs     vs    Sessions </div>""", height=40)
    st.subheader(f'\nUtilisateurs vs Sessions', divider='gray')
    minicol1, minicol2 = st.columns(2)
    with minicol1:
        components.html("""<div style="text-align: center; color: blue"> Nouveaux vs de Retour </div>""", height=50)
    with minicol2:
        components.html("""<div style="text-align: center; color: salmon"> Engagées vs Bounces </div>""", height=50)

    year_month = build_year_month(output_df=output_df, comp_df=comp_df)
    year_month_pivot= pd.pivot_table(year_month.sort_values(by='yearMonth', ascending=False), values=['Sessions Engagées','Bounces','Users Nouveaux','Users de Retour'],
                                   index=['yearMonth'], aggfunc='sum').reset_index()
    year_month_pivot = year_month_pivot.melt(id_vars='yearMonth', value_vars=['Users Nouveaux','Users de Retour','Sessions Engagées','Bounces'], var_name="SubType", value_name="Nombre")
    year_month_pivot['Type'] = year_month_pivot['SubType'].map(lambda x: 'Users' if x[0:5]=='Users' else 'Sessions')
    # st.write(year_month_pivot)
    
    fig_area = px.area(year_month_pivot, x='yearMonth', y="Nombre", text="Nombre", color="SubType", facet_row="Type",
                      labels={'yearMonth': 'Année - Mois', 'Nombre': 'Nombre', 'Type': 'Utilisateur ou Séance'},)
    fig_area.update_layout(legend=dict(bgcolor=None,title=None,yanchor="top",y=1.2,xanchor="left",x=0.01),
                          xaxis=dict(autorange="reversed"),
                          paper_bgcolor=None)
    fig_area.update_xaxes(visible=True,title=None)
    fig_area.update_yaxes(visible=True,title=None)
    fig_area.update_traces(textposition='top center', textfont=dict(size=12,color='#9C3587',weight="bold"))
    st.plotly_chart(fig_area, use_container_width=True, theme="streamlit", on_select="rerun")
    
    
    ## GRAPHS 3, 4
    st.subheader(f'\nAcquisition par Canal',divider='gray')
    channel = build_channel(output_df)
    
    st.markdown(f'\nUtilisateurs Actifs')
    base_channel_users = alt.Chart(channel).mark_bar().encode(x=alt.X("activeUsers:Q", title='', sort='ascending', stack='normalize'), #, scale=alt.Scale(clamp=True)
                                                       y=alt.Y('yearMonth:N', axis=alt.Axis(title=None, labelAngle=0), sort='descending'), #, type='temporal'
                                                       tooltip=['Percent:N','activeUsers:Q','Channel:N','yearMonth:N'])
    chart_channel_users = base_channel_users.mark_bar().encode(color="Channel")
    text_channel_users = base_channel_users.mark_text(align='center', baseline='line-top', xOffset=-50, yOffset=-5, size=12, color='white'
                ).encode(text=alt.Text('Label:N'))
    channel_users = st.altair_chart(chart_channel_users + text_channel_users, use_container_width=True)


    st.markdown(f'\nSessions Engagées')
    base_channel_sessions = alt.Chart(channel).mark_bar().encode(x=alt.X('engagedSessions:Q', title='', sort='ascending', stack='normalize'),
                                                            y=alt.Y('yearMonth:N', title='', sort='descending'),
                                                            tooltip=['engagedSessions_Percent:N','engagedSessions:Q','Channel:N','yearMonth:N']) #, type='temporal'
    chart_channel_sessions = base_channel_sessions.mark_bar().encode(color="Channel")
    text_channel_sessions = base_channel_sessions.mark_text(align='center', baseline='line-top', xOffset=-50, yOffset=-5, size=12, color='white'
                ).encode(text=alt.Text('Label_bis:N'))
    channel_sessions = st.altair_chart(chart_channel_sessions + text_channel_sessions, use_container_width=True)
    
    
## GRAPH 5
with tab2:
    st.subheader(f'\nPrincipaux KPIs de Performance', divider='gray')
    # st.dataframe(data=year_month.style.highlight_max(axis=0,subset=['bounceRate'],color='red',).highlight_max(axis=0,subset=['engagedSessionsRate','newUsersRate','returningUsersRate'],color='#34a853'),
    st.dataframe(data=year_month.style.applymap(color_rate, subset=['bounceRate','engagedSessionsRate','newUsersRate','returningUsersRate']),
                    height=None, hide_index=True, on_select="rerun",
                    column_order=['yearMonth','Sessions','engagedSessionsRate','bounceRate','activeUsers','returningUsersRate','newUsersRate','avgScreenViews','avgSessionDuration'],
                column_config={
        "yearMonth": st.column_config.DateColumn("Année - Mois", format="YYYY - MMM", pinned=True),
        "Sessions": st.column_config.ProgressColumn("Sessions", format="localized",min_value=0,max_value=max(max(year_month['Sessions']),0)), #
        "engagedSessionsRate": st.column_config.NumberColumn("% Engagées",format="percent",min_value=0,max_value=1),
        "bounceRate": st.column_config.NumberColumn("% Bounce",help="% of users exiting website as soon as landing",format="percent",min_value=0,max_value=1,width="small"),
        "activeUsers": st.column_config.ProgressColumn("Utilisateurs Actifs",format="localized",min_value=0), #,max_value=max(year_month['activeUsers'])
        "returningUsersRate": st.column_config.NumberColumn("% Retour",format="percent",min_value=0,max_value=1),
        "newUsersRate": st.column_config.NumberColumn("% Nouveaux",format="percent",min_value=0,max_value=1),
        "avgScreenViews": st.column_config.NumberColumn("Moy. Pages Vues",format="localized",min_value=0),
        "avgSessionDuration": st.column_config.NumberColumn("Durée Moy. Session",format="localized",min_value=0),
    })
    
    
    ## GRAPH 6
    st.markdown(f"\nComparaison à l'Année Précédente")
    year_month.sort_values('yearMonth', ascending=False, inplace=True)
    
    cmap = plt.cm.get_cmap('PRGn')
    st.dataframe(data=year_month.style.background_gradient(cmap=cmap,vmin=-1,vmax=1,axis=None).applymap(color_background, subset=['Sessions_vs_LY','engagedSessions_vs_LY','bounces_vs_LY','activeUsers_vs_LY','returningUsers_vs_LY','newUsers_vs_LY']), #.set_properties(**{'text-align': 'center'}).set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
                    height=None, hide_index=True, on_select="rerun",
                    column_order=['yearMonth','Sessions_vs_LY','engagedSessions_vs_LY','bounces_vs_LY','activeUsers_vs_LY','returningUsers_vs_LY','newUsers_vs_LY'],
                column_config={
        "yearMonth": st.column_config.DateColumn("Année - Mois", format="YYYY - MMM", pinned=True),
        "Sessions_vs_LY": st.column_config.NumberColumn("Sessions vs LY", format="percent",min_value=0,max_value=1),
        "engagedSessions_vs_LY": st.column_config.NumberColumn("Engagées vs LY",format="percent",min_value=0,max_value=1),
        "bounces_vs_LY": st.column_config.NumberColumn("Bounces vs LY",help="% of users exiting website as soon as landing",format="percent",min_value=0,max_value=1),
        "activeUsers_vs_LY": st.column_config.NumberColumn("Utilisateurs vs LY",format="percent",min_value=0,max_value=1),
        "returningUsers_vs_LY": st.column_config.NumberColumn("Retour vs LY",format="percent",min_value=0,max_value=1),
        "newUsers_vs_LY": st.column_config.NumberColumn("Nouveaux vs LY",format="percent",min_value=0,max_value=1),
    })


    ## DISPLAY - MAIN STRUCTURE
    col1, col2, col3 = st.columns(3)

    landing_table, pages_table, countries_table = traffic_report(end_date_input, start_date_input, property_id, client, country_filter, firstUserDefaultChannelGroup_filter)

    ## GRAPHS 7, 8, 9
    st.subheader(f'\nTop {str(top_results)} Pays', divider='gray')
    countries_table.index += 1
    st.dataframe(countries_table[0:top_results],
                column_config={
            "country": st.column_config.TextColumn("Pays"),
            "activeUsers": st.column_config.ProgressColumn("Utilisateurs Actifs",format="localized",min_value=0,max_value=max(countries_table['activeUsers'][0:top_results])),
            "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(countries_table['engagedSessions'][0:top_results])),
            "averageSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(countries_table['averageSessionDuration'][0:top_results])),
            },)

    # with col2:
    st.subheader(f'\nTop {str(top_results)} Landing Pages', divider='gray')
    landing_table.index += 1
    st.dataframe(landing_table[0:top_results],
                column_config={
            "landingPage": st.column_config.TextColumn("Landing Page URL"),
            "activeUsers": st.column_config.ProgressColumn("Utilisateurs Actifs",format="localized",min_value=0,max_value=max(landing_table['activeUsers'][0:top_results])),
            "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(landing_table['engagedSessions'][0:top_results])),
            "averageSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(landing_table['averageSessionDuration'][0:top_results])),
            },)
            
    # with col3:
    st.subheader(f'\nTop {str(top_results)} Pages Visitées', divider='gray')
    pages_table.index += 1
    st.dataframe(pages_table[0:top_results],
                column_config={
            "pagePath": st.column_config.TextColumn("Adresse Page URL"),
            "activeUsers": st.column_config.ProgressColumn("Utilisateurs Actifs",format="localized",min_value=0,max_value=max(pages_table['activeUsers'][0:top_results])),
            "engagedSessions": st.column_config.ProgressColumn("Sessions Engagées",format="localized",min_value=0,max_value=max(pages_table['engagedSessions'][0:top_results])),
            "averageSessionDuration": st.column_config.ProgressColumn("Durée Moy. Session (s)",format="localized",min_value=0,max_value=max(pages_table['averageSessionDuration'][0:top_results])),
            },)
