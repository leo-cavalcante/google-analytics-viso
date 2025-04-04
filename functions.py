## SUPPORT FUNCTIONS FOR PROPER RUNNING OF STREAMLIT APP
import re
import dateutil
import numpy as np
import pandas as pd
from io import BytesIO
import streamlit as st
from datetime import date
import plotly_express as px
import matplotlib.pyplot as plt
from pyxlsb import open_workbook as open_xlsb
from google.analytics.data_v1beta.types import Metric
from google.analytics.data_v1beta.types import OrderBy
from google.analytics.data_v1beta.types import DateRange
from google.analytics.data_v1beta.types import Dimension
from google.analytics.data_v1beta.types import RunReportRequest 

# GLOBAL VARIABLES - COLOR PALETTE
color_discrete_map_type={"Visiteurs" : "rgba(0,0,255,100)", "Sessions" : "rgba(215,48,39,100)", "Prospects" : "#2aa198"}

color_discrete_map_channels={ "1-Unassigned"        : "rgba(165,0,38,100)",   "2-Paid Search"    : "rgba(215,48,39,100)",
                                "Unassigned"          : "rgba(165,0,38,100)",   "Paid Search"      : "rgba(215,48,39,100)",
                                "3-Organic Shopping"  : "rgba(90,174,97,100)",   "4-Email"         : "rgba(253,174,97,100)",
                                "Organic Shopping"    : "rgba(90,174,97,100)",   "Email"           : "rgba(253,174,97,100)",
                                "5-Organic Social"    : "rgba(128,205,193,100)",   "6-Referral"    : "rgba(244,109,67,100)",
                                "Organic Social"      : "rgba(128,205,193,100)",   "Referral"      : "rgba(244,109,67,100)",
                                "7-Direct"            : "rgba(0,0,255,100)",   "8-Organic Search"  : "rgba(53,151,143,100)",
                                "Direct"              : "rgba(0,0,255,100)",   "Organic Search"    : "rgba(53,151,143,100)"}

channels_map = {"Unassigned"    :"1", "Paid Search"   :"2",
              "Organic Shopping":"3", "Organic Social":"4",
              "Email"           :"5", "Referral"      :"6",
              "Direct"          :"7", "Organic Search":"8"}
        
yearmonth_order=['2026-12 Dec', '2026-11 Nov', '2026-10 Oct', '2026-09 Sep', '2026-08 Aug', '2026-07 Jul', '2026-06 Jun', '2026-05 May', '2026-04 Apr', '2026-03 Mar', '2026-02 Feb', '2026-01 Jan', 
                    '2025-12 Dec', '2025-11 Nov', '2025-10 Oct', '2025-09 Sep', '2025-08 Aug', '2025-07 Jul', '2025-06 Jun', '2025-05 May', '2025-04 Apr', '2025-03 Mar', '2025-02 Feb', '2025-01 Jan', 
                    '2024-12 Dec', '2024-11 Nov', '2024-10 Oct', '2024-09 Sep', '2024-08 Aug', '2024-07 Jul', '2024-06 Jun', '2024-05 May', '2024-04 Apr', '2024-03 Mar', '2024-02 Feb', '2024-01 Jan', 
                    '2023-12 Dec', '2023-11 Nov', '2023-10 Oct', '2023-09 Sep', '2023-08 Aug', '2023-07 Jul', '2023-06 Jun', '2023-05 May', '2023-04 Apr', '2023-03 Mar', '2023-02 Feb', '2023-01 Jan', 
                    '2022-12 Dec', '2022-11 Nov', '2022-10 Oct', '2022-09 Sep', '2022-08 Aug', '2022-07 Jul', '2022-06 Jun', '2022-05 May', '2022-04 Apr', '2022-03 Mar', '2022-02 Feb', '2022-01 Jan', 
                    '2021-12 Dec', '2021-11 Nov', '2021-10 Oct', '2021-09 Sep', '2021-08 Aug', '2021-07 Jul', '2021-06 Jun', '2021-05 May', '2021-04 Apr', '2021-03 Mar', '2021-02 Feb', '2021-01 Jan', 
                    '2020-12 Dec', '2020-11 Nov', '2020-10 Oct', '2020-09 Sep', '2020-08 Aug', '2020-07 Jul', '2020-06 Jun', '2020-05 May', '2020-04 Apr', '2020-03 Mar', '2020-02 Feb', '2020-01 Jan']

#  FORMAT FUNCTIONS
def format_report(client, request):
    response = client.run_report(request)
    
    row_index_names = [header.name for header in response.dimension_headers]
    row_header = []
    
    for i in range(len(row_index_names)):
        row_header.append([row.dimension_values[i].value for row in response.rows])
    
    row_index_names = pd.MultiIndex.from_arrays(np.array(row_header, dtype = 'U'), names = np.array(row_index_names, dtype = 'U'))
    
    metric_names = [header.name for header in response.metric_headers]
    data_values = []
    
    for i in range(len(metric_names)):
        data_values.append([row.metric_values[i].value for row in response.rows])
    
    output = pd.DataFrame(data = np.transpose(np.array(data_values, dtype = 'f')),
                                                index=row_index_names, columns=metric_names)
    output.reset_index(inplace=True)
    return output

def rename_cols(df):
    df = df.rename(columns={'engagedSessions':'Sessions Engagées', 'Bounces':'Sessions Bounces', 'bounces':'Sessions Bounces',
                               'returningUsers':'Visiteurs de Retour', 'newUsers':'Visiteurs Nouveaux',
                               'downloads':'Prospects Catalogue','demande_contact_realisee':'Prospects Formulaire'},)
    return df

# DATA COLLECTION FUNCTIONS
def read_database():
    try:
        database_df = pd.read_excel('extracts/GA_database.xlsx', sheet_name='Today')
        database_df.to_excel('extracts/GA_database.xlsx', sheet_name='Yesterday', engine='xlsxwriter')
    except:
        database_df = []
    return database_df
    
def request_ga(_client, property_id, start_date_input, end_date_input, comp_flag=False):
    request = RunReportRequest(
            property='properties/'+property_id,
            dimensions=[Dimension(name="date"), #Dimension(name="year"), Dimension(name="month"), # Dimension(name="week"),
                        Dimension(name="yearMonth"),
                        Dimension(name="eventName"),
                        Dimension(name="country"), # Dimension(name="sessionSourceMedium")], # Dimension(name="sessionMedium"), # Dimension(name="defaultChannelGroup")],       # NOT POSSIBLE TO CALCULATE NEW VISITORS
                        Dimension(name="firstUserDefaultChannelGroup"),],
            metrics=[Metric(name="activeUsers"),
                     Metric(name="newUsers"),
                     Metric(name="Sessions"),
                     Metric(name="engagedSessions"), #  Metric(name="bounceRate"),
                     Metric(name="keyEvents"),
                     Metric(name="screenPageViews"),                    ## >> screen_view + page_view events
                     Metric(name="averageSessionDuration")],
            order_bys = [OrderBy(dimension = {'dimension_name': 'date'}), #OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}),
                        OrderBy(dimension = {'dimension_name': 'yearMonth'}),
                        OrderBy(dimension = {'dimension_name': 'country'}),
                        OrderBy(dimension = {'dimension_name': 'firstUserDefaultChannelGroup',}),],
            date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],)
    
    df = format_report(_client, request)
    df = clean_df(df, comp_flag)
    st.write(df)
    df = df.fillna(0).reset_index()
    
    df_agg = df.groupby(['date','yearMonth','country','firstUserDefaultChannelGroup']).sum().reset_index()
    st.write(df_agg)
    df_events = df[df['keyEvents']>0]
    df_events = pd.pivot_table(df_events, index=['date','yearMonth','country','firstUserDefaultChannelGroup'],
                       columns=['eventName'], values='keyEvents', aggfunc="sum")
    st.write(df_events)
    
    df = pd.merge(df_agg, df_events, on=['date','yearMonth','country','firstUserDefaultChannelGroup'], how='outer', suffixes=('','_event'))
    # comp_df = pd.merge(comp_df, comp_events_df, how='outer', on=['date', 'yearMonth', 'country', 'firstUserDefaultChannelGroup'], suffixes=('','_event'))
    
    # FEATURE ENGINEERING
    df['returningUsers'] = df['activeUsers'] - df['newUsers']
    df['bounces'] = df['Sessions'] - df['engagedSessions']
    df['SessionsDuration'] = df['averageSessionDuration'] * df['engagedSessions']
    df.drop(columns=['averageSessionDuration','keyEvents','index'], inplace=True)
    
    if 'interet_par_les_catalogues' not in df.columns:
        df['interet_par_les_catalogues'] = [0] * len(df.index)
        
    df['download'] = [0] * len(df.index)
    if 'téléchargement_catalogue_sign' in df.columns:
        df['download'] += df['téléchargement_catalogue_sign']
        df.drop(columns='téléchargement_catalogue_sign',inplace=True)
    if 'télécharger_catalogue_chain' in df.columns:
        df['download'] += df['télécharger_catalogue_chain']
        df.drop(columns='télécharger_catalogue_chain',inplace=True)
    if 'télécharger_catalogue_storage' in df.columns:
        df['download'] += df['télécharger_catalogue_storage']
        df.drop(columns={'télécharger_catalogue_storage'},inplace=True)
        
    if 'demande_contact_realisee' not in df.columns:
        df['demande_contact_realisee'] = [0] * len(df.index)
    
    
    return df

def request_ga_default(_client, property_id, start_date_input, end_date_input):
    request = RunReportRequest(
            property='properties/'+property_id,
            dimensions=[Dimension(name="date"), #Dimension(name="year"), Dimension(name="month"), # Dimension(name="week"),
                        Dimension(name="yearMonth"),
                        Dimension(name="country"), # Dimension(name="sessionSourceMedium")], # Dimension(name="sessionMedium"), # Dimension(name="defaultChannelGroup")],       # NOT POSSIBLE TO CALCULATE NEW VISITORS
                        Dimension(name="firstUserDefaultChannelGroup"),],
            metrics=[Metric(name="activeUsers"),
                     Metric(name="newUsers"),
                     Metric(name="Sessions"),
                     Metric(name="engagedSessions"), #  Metric(name="bounceRate"),
                     Metric(name="screenPageViews"),                    ## >> screen_view + page_view events
                     Metric(name="averageSessionDuration")],
            order_bys = [OrderBy(dimension = {'dimension_name': 'date'}), #OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}),
                        OrderBy(dimension = {'dimension_name': 'yearMonth'}),
                        OrderBy(dimension = {'dimension_name': 'country'}),
                        OrderBy(dimension = {'dimension_name': 'firstUserDefaultChannelGroup',}),],
            date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],)
    
    df = format_report(_client, request)
    
    # FEATURE ENGINEERING
    df['returningUsers'] = df['activeUsers'] - df['newUsers']
    df['bounces'] = df['Sessions'] - df['engagedSessions']
    df['SessionsDuration'] = df['averageSessionDuration'] * df['engagedSessions']
    
    return df

def request_ga_events(_client, property_id, start_date_input, end_date_input):
    request_events = RunReportRequest(
            property='properties/'+property_id,
            dimensions=[Dimension(name="date"), #Dimension(name="year"), Dimension(name="month"), # Dimension(name="week"),
                        Dimension(name="yearMonth"),
                        Dimension(name="country"), # Dimension(name="sessionSourceMedium")], # Dimension(name="sessionMedium"), # Dimension(name="defaultChannelGroup")],       # NOT POSSIBLE TO CALCULATE NEW VISITORS
                        Dimension(name="firstUserDefaultChannelGroup"),
                        Dimension(name="eventName")],
            metrics=[Metric(name="keyEvents")],
            order_bys = [OrderBy(dimension = {'dimension_name': 'date'}), #OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}),
                        OrderBy(dimension = {'dimension_name': 'yearMonth'}),
                        OrderBy(dimension = {'dimension_name': 'country'}),
                        OrderBy(dimension = {'dimension_name': 'firstUserDefaultChannelGroup'})],
            date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],)

    events_df = format_report(_client, request_events)
    
    events_df = pd.pivot_table(events_df, index=['date', 'yearMonth', 'country', 'firstUserDefaultChannelGroup'],
                       columns=['eventName'], values='keyEvents', aggfunc="sum")
    events_df = events_df.fillna(0).reset_index()
    
    # FEATURE ENGINEERING
    if 'interet_par_les_catalogues' not in events_df.columns:
        events_df['interet_par_les_catalogues'] = [0] * len(events_df.index)
    
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
    
    if 'demande_contact_realisee' not in events_df.columns:
        events_df['demande_contact_realisee'] = [0] * len(events_df.index)
    
    return events_df

def request_ga_pages(client, property_id, start_date_input, end_date_input):        
    pages_request = RunReportRequest(
                property='properties/'+property_id,
                dimensions=[Dimension(name="date"),
                            Dimension(name="yearMonth"),
                            Dimension(name="country"),
                            # Dimension(name="landingPage"),
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
    
    # TRANSFORMATION STEPS APPLIED
    pages_df = format_report(client, pages_request)
    pages_df = clean_df(pages_df)
    
    pages_df['averageSessionDuration'] = pages_df['averageSessionDuration'].apply(lambda x: round(x,0)).astype('float')
    pages_df['SessionsDuration'] = pages_df['Sessions'] * pages_df['averageSessionDuration'] # .apply(lambda x: round(x,0)).astype('float')
    pages_df.drop(columns=['averageSessionDuration'], inplace=True)
    pages_df.reset_index(inplace=True)
    
    pages_df = pages_df.groupby(['yearMonth','country','pagePath','firstUserDefaultChannelGroup']
                                ).agg(activeUsers=('activeUsers','sum'), Sessions=('Sessions','sum'), engagedSessions=('engagedSessions','sum'),
                                    SessionsDuration=('SessionsDuration','sum'), screenPageViews=('screenPageViews','sum'),
                                ).sort_values('activeUsers', ascending=False
                                ).reset_index()
    return pages_df

# CLEAN DATA COLLECTED
def clean_df(df, comp_flag=False):
    # df_final = df.copy()
    df_final = df.fillna(0)
    
    # Rectifying data type
    df_final['date'] = pd.to_datetime(df_final['date'], format='%Y-%m-%d')
    df_final['yearMonth'] = pd.to_datetime(df_final['yearMonth'], format='%Y%m')
    if comp_flag:
        df_final['date'] = df_final['date'].apply(lambda x: x + dateutil.relativedelta.relativedelta(years=1))
        df_final['yearMonth'] = df_final['yearMonth'].apply(lambda x: x + dateutil.relativedelta.relativedelta(years=1))
        # df_final['yearMonth'] = df_final['yearMonth'].astype('int').apply(lambda x: x+100).astype('str')
    df_final['yearMonth'] = df_final['yearMonth'].dt.strftime('%Y-%m %b')
    
    try:
        df_final['newUsers'] = df_final['newUsers'].values.astype('int')
    except:
        pass
    df_final['activeUsers'] = df_final['activeUsers'].values.astype('int')
    df_final['Sessions'] = df_final['Sessions'].astype('int')
    df_final['engagedSessions'] = df_final['engagedSessions'].values.astype('int')
    df_final['screenPageViews'] = df_final['screenPageViews'].astype('int') 
    df_final['averageSessionDuration'] = df_final['averageSessionDuration'].astype('float') 
        
    # Correcting Values
    for index, row in df_final.iterrows():
        if  row['Sessions'] == 0:
            row['activeUsers'] = 0
            row['engagedSessions'] = 0
            row['screenPageViews'] = 0
            row['averageSessionDuration'] = 0
            try:
                row['newUsers'] = 0
            except:
                continue
        if row['country'].lower().strip() in ('(not set)', 'not set', ''):
            row['country'] = 'INCONNU'
            
    df_final.sort_values('yearMonth', ascending=False, inplace=True)

    return df_final

def clean_pages(pages_table):
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

## EXPORT TO EXCEL
def export_to_excel(df_final):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df_final.to_excel(writer, index=False, sheet_name='Final')
    workbook = writer.book
    worksheet = writer.sheets['Final']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.save()
    data_to_download = output.getvalue()
    return data_to_download

# def export_to_excel_OLD(df_final):
#     today_str = date.today().strftime('%Y-%m-%d at %H.%m')
#     return df_final.to_excel(f'{today_str}_GA4_df_final.xlsx', sheet_name = 'GA4_df_final', engine = 'xlsxwriter').encode("utf-8")

## Export to CSV
def export_to_csv(df):
    return df.to_csv().encode("utf-8")
