## SUPPORT FUNCTIONS FOR PROPER RUNNING OF STREAMLIT APP
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from google.analytics.data_v1beta.types import Metric
from google.analytics.data_v1beta.types import OrderBy
from google.analytics.data_v1beta.types import DateRange
from google.analytics.data_v1beta.types import Dimension
from google.analytics.data_v1beta.types import RunReportRequest 

channels_map = {"Unassigned"    :"1", "Paid Search"   :"2",
              "Organic Shopping":"3", "Organic Social":"4",
              "Email"           :"5", "Referral"      :"6",
              "Direct"          :"7", "Organic Search":"8"}
        
def request_ga_data(_client, property_id, start_date_input, end_date_input, events_df):
    request = RunReportRequest(
            property='properties/'+property_id,
            dimensions=[Dimension(name="yearMonth"), #Dimension(name="year"), Dimension(name="month"), # Dimension(name="week"), # Dimension(name="date"),
                        Dimension(name="country"), # Dimension(name="sessionSourceMedium")], # Dimension(name="sessionMedium"), # Dimension(name="defaultChannelGroup")],       # NOT POSSIBLE TO CALCULATE NEW VISITORS
                        Dimension(name="firstUserDefaultChannelGroup"),],
            metrics=[Metric(name="activeUsers"),
                     Metric(name="newUsers"),
                     Metric(name="Sessions"),
                     Metric(name="engagedSessions"), #  Metric(name="bounceRate"),
                     Metric(name="screenPageViews"),                    ## >> screen_view + page_view events
                     Metric(name="averageSessionDuration")],
            order_bys = [OrderBy(dimension = {'dimension_name': 'yearMonth'}), #OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}),
                        OrderBy(dimension = {'dimension_name': 'country'}),
                        OrderBy(dimension = {'dimension_name': 'firstUserDefaultChannelGroup',}),],
            date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],)
    output_df = format_report(_client, request)
    output_df['country'] = output_df['country'].str.replace('(not set)', 'INCONNU')
    
    # output_df = pd.merge(output_df, events_df, how='outer', on=['yearMonth', 'country', 'firstUserDefaultChannelGroup', 'pagePath'], suffixes=('','_event'))
    output_df = pd.merge(output_df, events_df, how='outer', on=['yearMonth', 'country', 'firstUserDefaultChannelGroup'], suffixes=('','_event'))
    output_df['returningUsers'] = output_df['activeUsers'] - output_df['newUsers']
    output_df['bounces'] = output_df['Sessions'] - output_df['engagedSessions']
    output_df['SessionsDuration'] = output_df['averageSessionDuration'] * output_df['engagedSessions']
    
    return output_df

def request_ga_key_events(_client, property_id, start_date_input, end_date_input):
    request_events = RunReportRequest(
            property='properties/'+property_id,
            dimensions=[Dimension(name="yearMonth"), #Dimension(name="year"), Dimension(name="month"), # Dimension(name="week"), # Dimension(name="date"),
                        Dimension(name="country"), # Dimension(name="sessionSourceMedium")], # Dimension(name="sessionMedium"), # Dimension(name="defaultChannelGroup")],       # NOT POSSIBLE TO CALCULATE NEW VISITORS
                        Dimension(name="firstUserDefaultChannelGroup"),
                        Dimension(name="eventName")],
            metrics=[Metric(name="keyEvents")],
            order_bys = [OrderBy(dimension = {'dimension_name': 'yearMonth'}), #OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}),
                        OrderBy(dimension = {'dimension_name': 'country'}),
                        OrderBy(dimension = {'dimension_name': 'firstUserDefaultChannelGroup'})],
            date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],)
    events_df = format_report(_client, request_events)

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
    
    return events_df

#  Format Report - run_report method
def format_report(client, request):
    response = client.run_report(request)
    
    #  Row index
    row_index_names = [header.name for header in response.dimension_headers]
    row_header = []
    
    for i in range(len(row_index_names)):
        row_header.append([row.dimension_values[i].value for row in response.rows])
    
    row_index_names = pd.MultiIndex.from_arrays(np.array(row_header, dtype = 'U'), names = np.array(row_index_names, dtype = 'U'))
    
    # Row flat data
    metric_names = [header.name for header in response.metric_headers]
    data_values = []
    
    for i in range(len(metric_names)):
        data_values.append([row.metric_values[i].value for row in response.rows])
    
    output = pd.DataFrame(data = np.transpose(np.array(data_values, dtype = 'f')),
                                                index=row_index_names, columns=metric_names)
    output.reset_index(inplace=True)
    return output

def rename_cols_df(df):
    df = df.rename(columns={'engagedSessions':'Sessions Engagées', 'Bounces':'Sessions Bounces', 'bounces':'Sessions Bounces',
                               'returningUsers':'Visiteurs de Retour', 'newUsers':'Visiteurs Nouveaux',
                               'downloads':'Prospects Catalogue','demande_contact_realisee':'Prospects Formulaire'},)
    return df

def build_df_final(output_df):
    df_final = output_df.copy()
    output_df=output_df.fillna(0)
    
    # Rectifying data type

    # Creating new & deleting avg columns on dataframe
    df_final['yearMonth'] = pd.to_datetime(df_final['yearMonth'], format='%Y%m')
    df_final['yearMonth'] = df_final['yearMonth'].dt.strftime('%Y-%m %b')
    df_final['newUsers'] = df_final['newUsers'].values.astype('int')
    df_final['activeUsers'] = df_final['activeUsers'].values.astype('int')
    # df_final['activeUsers'] = df_final['activeUsers'].astype('int') 
    df_final['engagedSessions'] = df_final['engagedSessions'].values.astype('int')
    
    # df_final.drop(columns={'year', 'month'})
    df_final.sort_values('yearMonth', ascending=False, inplace=True)

    return df_final

# FOR GRAPH 1
def build_funnel(df_final):
    funnel_df = df_final[['screenPageViews', 'Sessions', 'engagedSessions','activeUsers', 'newUsers', 'returningUsers', 'interet_par_les_catalogues', 'download', 'demande_contact_realisee']].sum()#agg('sum')
    funnel_df = funnel_df.rename({'screenPageViews':'Pages Vues', 'Sessions':'Sessions', 'activeUsers':'Visiteurs',
                                    'engagedSessions':'Sessions Engagées', 'newUsers':'Visiteurs Nouveaux', 'returningUsers':'Visiteurs de Retour',
                                    'interet_par_les_catalogues':'Prospects Vues Catalogue', 'download':'Prospects Catalogue', 'demande_contact_realisee':'Prospects Formulaire'})
    funnel_df = funnel_df.reset_index().rename(columns={0:'Nombre', 'index':'Étape'})
    funnel_df['Type'] = funnel_df['Étape'].map(lambda x: 'Visiteurs' if x[0:8]=='Visiteur' else 'Prospects' if x[0:8]=='Prospect' else 'Sessions')
    funnel_df = funnel_df.set_index('Étape')
    funnel_df = funnel_df.rename(index={'Prospects Vues Catalogue':'Vues Catalogue','Prospects Catalogue':'Prospects Catalogue','Prospects Formulaire':'Prospects Formulaire'})
    funnel_df['Nombre'] = funnel_df['Nombre'].values.astype('int')
    funnel_df['Nombre'] = funnel_df['Nombre'].map(lambda x: round(x,-2) if x>10000 else round(x,0) if x>100 else round(x,0))
    funnel_df = funnel_df.reset_index()
    # funnel_df = funnel_df.loc[~funnel_df['Nombre']==0]
    return funnel_df

# FOR GRAPHS 2 & 3
# FOR TABLES 1 & 2
def build_yearMonth(df_final):
    yearMonth_agg = df_final.groupby(by='yearMonth').agg(  Sessions=('Sessions', 'sum'), engagedSessions=('engagedSessions', 'sum'),   Sessions_LY=('Sessions_LY', 'sum'), engagedSessions_LY=('engagedSessions_LY', 'sum'),
                                                        bounces=('bounces','sum'), activeUsers=('activeUsers','sum'),               bounces_LY=('bounces_LY','sum'),    activeUsers_LY=('activeUsers_LY','sum'),
                                                        newUsers=('newUsers','sum'), returningUsers=('returningUsers', 'sum'),      newUsers_LY=('newUsers_LY','sum'),  returningUsers_LY=('returningUsers_LY', 'sum'),
                                                        screenPageViews=('screenPageViews', 'sum'),                                 screenPageViews_LY=('screenPageViews_LY', 'sum'),
                                                        SessionsDuration=('SessionsDuration','sum'),                                SessionsDuration_LY=('SessionsDuration_LY','sum'),
                                                        interet_par_les_catalogues=('interet_par_les_catalogues', 'sum'),           #interet_par_les_catalogues_LY=('interet_par_les_catalogues_LY', 'sum'),
                                                        download=('download', 'sum'),                                               download_LY=('download_LY', 'sum'),
                                                        demande_contact_realisee=('demande_contact_realisee', 'sum'))               #demande_contact_realisee_LY=('demande_contact_realisee_LY', 'sum')
    
    yearMonth_agg['Sessions_vs_LY'] = (yearMonth_agg['Sessions']/yearMonth_agg['Sessions_LY'] - 1)
    yearMonth_agg['engagedSessions_vs_LY'] = (yearMonth_agg['engagedSessions']/yearMonth_agg['engagedSessions_LY'] - 1).apply(lambda x: round(x, 3))
    yearMonth_agg['bounces_vs_LY'] = (yearMonth_agg['bounces']/yearMonth_agg['bounces_LY'] - 1).apply(lambda x: round(x, 3))
    yearMonth_agg['activeUsers_vs_LY'] = (yearMonth_agg['activeUsers']/yearMonth_agg['activeUsers_LY'] - 1).apply(lambda x: round(x, 3))
    yearMonth_agg['newUsers_vs_LY'] = (yearMonth_agg['newUsers']/yearMonth_agg['newUsers_LY'] - 1).apply(lambda x: round(x, 3))
    yearMonth_agg['returningUsers_vs_LY'] = (yearMonth_agg['returningUsers']/yearMonth_agg['returningUsers_LY'] - 1).apply(lambda x: round(x, 3))
    
    yearMonth_agg['bounceRate'] = (yearMonth_agg['bounces'] / yearMonth_agg['Sessions']).apply(lambda x: round(x, 3))
    
    yearMonth_agg['newUsersRate'] = (yearMonth_agg['newUsers'] / yearMonth_agg['activeUsers']).apply(lambda x: round(x, 3))
    yearMonth_agg['returningUsersRate'] = (yearMonth_agg['returningUsers'] / yearMonth_agg['activeUsers']).apply(lambda x: round(x, 3))
    
    yearMonth_agg['engagedSessionsRate'] = (yearMonth_agg['engagedSessions'] / yearMonth_agg['Sessions']).apply(lambda x: round(x, 3))
    yearMonth_agg['avgScreenViews'] = (yearMonth_agg['screenPageViews'] / yearMonth_agg['Sessions']).map('{:.1f}'.format)
    yearMonth_agg['avgSessionDuration'] = (yearMonth_agg['SessionsDuration'] / yearMonth_agg['Sessions']).map('{:.1f}'.format)
    
    yearMonth_agg.drop(columns={'screenPageViews','SessionsDuration','Sessions_LY','engagedSessions_LY','bounces_LY','activeUsers_LY','newUsers_LY','returningUsers_LY'}, inplace=True)
    
    yearMonth_agg = yearMonth_agg[yearMonth_agg['Sessions']>0] # | yearMonth_agg['activeUsers']>0]
    yearMonth_agg = yearMonth_agg.sort_values(by='yearMonth', ascending=False)
    yearMonth_agg.reset_index(inplace=True)
    
    return yearMonth_agg

# FOR GRAPH 3
def build_channel(df_final):
    channel_df = df_final.copy()
    channel_df = channel_df.groupby(['yearMonth', 'firstUserDefaultChannelGroup']).agg(engagedSessions=('engagedSessions', 'sum'), activeUsers=('activeUsers','sum'))
    channel_df.reset_index(names=['yearMonth', 'firstUserDefaultChannelGroup'], inplace=True)
    
    channel_total = channel_df.groupby(['yearMonth']).agg(engagedSessions=('engagedSessions', 'sum'), activeUsers=('activeUsers','sum'))
    channel_total.reset_index(names=['yearMonth'], inplace=True)
    
    channel_df = pd.merge(channel_df, channel_total, on='yearMonth', how='left', suffixes=('','_total'))
    channel_df = channel_df.rename(columns={'yearMonth':'yearMonth','firstUserDefaultChannelGroup':'Channel', 'activeUsers':'activeUsers', 'engagedSessions':'engagedSessions'})
    
    channel_pivot = pd.pivot_table(channel_df, index=['yearMonth', 'Channel'],
                             values=['engagedSessions','activeUsers'],
                             aggfunc='sum').reset_index()
    channel_unpivot = channel_pivot.melt(id_vars=['yearMonth','Channel'],
                                       value_vars=['activeUsers','engagedSessions'],
                                       var_name="SubType", value_name="Nombre")
    channel_unpivot['Type'] = channel_unpivot['SubType'].map(lambda x: 'Visiteurs' if x[-5:]=='Users' else 'Sessions' if x[-8:]=='Sessions' else 'Prospects')
    channel_unpivot['Channel_DEF'] = channel_unpivot['Channel'].map(lambda x: str(channels_map[x]) + '-' + str(x))
    channel_unpivot = channel_unpivot[channel_unpivot['Type'] == 'Visiteurs']
    channel_unpivot = channel_unpivot.groupby(['Channel_DEF', 'Channel','yearMonth', 'Type', 'SubType']).agg(Nombre=('Nombre', 'sum'))
    channel_unpivot = channel_unpivot.reset_index(names=['Channel_DEF', 'Channel', 'yearMonth', 'Type', 'SubType'])
    channel_unpivot = channel_unpivot.sort_values(by=['Channel_DEF','yearMonth','Nombre'], ascending=[True, False, True])
    channel_unpivot['Nombre'] = channel_unpivot['Nombre'].apply(lambda x: round(x,0)).astype('int')
    channel_unpivot.reset_index(drop=True, inplace=True)
    # st.write(channel_unpivot)
    
    return channel_unpivot

def traffic_report(end_date_input, start_date_input, property_id, client):        
    pages_request = RunReportRequest(
                property='properties/'+property_id,
                dimensions=[Dimension(name="yearMonth"),
                            Dimension(name="country"),
                            Dimension(name="landingPage"),
                            Dimension(name="pagePath"),
                            Dimension(name="firstUserDefaultChannelGroup")],
                metrics=[Metric(name="activeUsers"),
                     Metric(name="Sessions"),
                     Metric(name="engagedSessions"),
                     Metric(name="screenPageViews"),                    ## >> screen_view + page_view events
                     Metric(name="averageSessionDuration")],
                order_bys = [OrderBy(metric = {'metric_name': 'activeUsers'}, desc = True)],
                date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))]
    )
    
    # Produce Top pages output tables
    table_requested = format_report(client, pages_request)
    table_requested['country'] = table_requested['country'].str.replace('(not set)', 'INCONNU')
    table_requested['yearMonth'] = pd.to_datetime(table_requested['yearMonth'], format='%Y%m')
    table_requested['yearMonth'] = table_requested['yearMonth'].dt.strftime('%Y-%m %b')
    table_requested['activeUsers'] = table_requested['activeUsers'].astype('int') 
    table_requested['Sessions'] = table_requested['Sessions'].astype('int') 
    table_requested['engagedSessions'] = table_requested['engagedSessions'].astype('int')
    table_requested['averageSessionDuration'] = table_requested['averageSessionDuration'].apply(lambda x: round(x,0)).astype('float')
    table_requested['SessionsDuration'] = table_requested['Sessions'] * table_requested['averageSessionDuration'] # .apply(lambda x: round(x,0)).astype('float')
    table_requested.drop(columns=['averageSessionDuration'], inplace=True)
    
    table_requested.reset_index(inplace=True)
    pages_table = table_requested.groupby(['yearMonth','country','pagePath','firstUserDefaultChannelGroup']
                                          ).agg(activeUsers=('activeUsers','sum'), Sessions=('Sessions','sum'), engagedSessions=('engagedSessions','sum'),
                                                SessionsDuration=('SessionsDuration','sum'), screenPageViews=('screenPageViews','sum'),
                                          ).sort_values('activeUsers', ascending=False
                                          ).reset_index()
    return pages_table

def pages_table_transformation(pages_table):
    pages_final = pages_table.groupby('pagePath').agg(activeUsers=('activeUsers','sum'), Sessions=('Sessions','sum'),
                                                        engagedSessions=('engagedSessions','sum'), SessionsDuration=('SessionsDuration','sum'),
                                                        screenPageViews=('screenPageViews','sum'),
                                                ).sort_values('activeUsers', ascending=False
                                                ).reset_index()
    pages_final['product'] = pages_final['pagePath'].apply(lambda x: x.split('.')[0])
    pages_final['product'] = pages_final['product'].apply(lambda x: x.split('/')[-1])
    pages_final['product'] = pages_final['product'].apply(lambda x: x.replace('-',' ').replace('_',' ').replace(' de l a l','').replace(' d '," d'"))
    pages_final['product'] = pages_final['product'].apply(lambda x: re.sub(r'[0-9]','',x))
    pages_final['product'] = pages_final['product'].str.strip(' ')
    pages_final['product'] = pages_final['product'].str.capitalize()
    
    pages_final['avgSessionDuration'] = (pages_final['SessionsDuration']/pages_final['Sessions']).apply(lambda x: round(x,0)).astype('int')
    
    return pages_final

def color_font(value):
    if value<-10 or value>10:
        return f"color: white"
        
    elif value<0:
        return f"color: #4B4B4B"
        
    elif value>=0:
        return f"color: #4B4B4B"
        
    else:
        return f"color: #4B4B4B"

def color_rate(value):
    return f"color: #B0B0B0"

## Export to Excel
def export_to_excel(output_df):
    output_df.reset_index().to_excel('GA4_python_output.xlsx', sheet_name = 'GA4_report', engine = 'xlsxwriter')

## Export to CSV
def export_to_csv(output_df):
    output_df.to_csv('GA4_python_output.csv')
