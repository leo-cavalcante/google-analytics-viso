## Google Analytics 4 (GA4) Data in Pyton Using run_report
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from google.analytics.data_v1beta.types import Metric
from google.analytics.data_v1beta.types import OrderBy
from google.analytics.data_v1beta.types import DateRange
from google.analytics.data_v1beta.types import Dimension
from google.analytics.data_v1beta.types import RunReportRequest 
# from google.analytics.data_v1beta import BetaAnalyticsDataClient

def request_ga_data(property_id, start_date_input, end_date_input):
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
            order_bys = [OrderBy(dimension = {'dimension_name': 'yearMonth'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}),
                        OrderBy(dimension = {'dimension_name': 'country'}),
                        OrderBy(dimension = {'dimension_name': 'firstUserDefaultChannelGroup'})],
            date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],
        )

def request_ga_key_events(property_id, start_date_input, end_date_input):
    return RunReportRequest(
            property='properties/'+property_id,
            dimensions=[Dimension(name="yearMonth"), # Dimension(name="year"), Dimension(name="month"), # Dimension(name="week"), # Dimension(name="date"),
                        Dimension(name="country"), # Dimension(name="sessionSourceMedium")], # Dimension(name="sessionMedium"), # Dimension(name="defaultChannelGroup")],       # NOT POSSIBLE TO CALCULATE NEW VISITORS
                        Dimension(name="firstUserDefaultChannelGroup"),
                        Dimension(name="eventName")],
            metrics=[Metric(name="keyEvents")],
            order_bys = [OrderBy(dimension = {'dimension_name': 'yearMonth'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}),
                        OrderBy(dimension = {'dimension_name': 'country'}),
                        OrderBy(dimension = {'dimension_name': 'firstUserDefaultChannelGroup'})],
            date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],
        )

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

def aggregate_yearMonth(output_df):
    output_df = output_df.groupby(by='yearMonth').agg(  Sessions=('Sessions', 'sum'), engagedSessions=('engagedSessions', 'sum'),   Sessions_LY=('Sessions_LY', 'sum'), engagedSessions_LY=('engagedSessions_LY', 'sum'),
                                                        bounces=('bounces','sum'), activeUsers=('activeUsers','sum'),               bounces_LY=('bounces_LY','sum'),    activeUsers_LY=('activeUsers_LY','sum'),
                                                        newUsers=('newUsers','sum'), returningUsers=('returningUsers', 'sum'),      newUsers_LY=('newUsers_LY','sum'),  returningUsers_LY=('returningUsers_LY', 'sum'),
                                                        screenPageViews=('screenPageViews', 'sum'),                                 screenPageViews_LY=('screenPageViews_LY', 'sum'),
                                                        SessionsDuration=('SessionsDuration','sum'),                                SessionsDuration_LY=('SessionsDuration_LY','sum'),
                                                        interet_par_les_catalogues=('interet_par_les_catalogues', 'sum'),           #interet_par_les_catalogues_LY=('interet_par_les_catalogues_LY', 'sum'),
                                                        download=('download', 'sum'),                                               download_LY=('download_LY', 'sum'),
                                                        demande_contact_realisee=('demande_contact_realisee', 'sum'))               #demande_contact_realisee_LY=('demande_contact_realisee_LY', 'sum')
    output_df['bounceRate'] = (output_df['bounces'] / output_df['Sessions'])
    output_df['bounceRate_txt'] = output_df['bounceRate'].map(lambda x: f"{x*100:0.0f}%")
    output_df['avgScreenViews'] = output_df['screenPageViews'] / output_df['Sessions']
    output_df['avgScreenViews'] = output_df['avgScreenViews'].map('{:.1f}'.format) #.values.astype('str')
    output_df['avgSessionDuration'] = output_df['SessionsDuration'] / output_df['Sessions']
    output_df['avgSessionDuration'] = output_df['avgSessionDuration'].map('{:.1f}'.format) #.values.astype('str')
    output_df.drop(columns=['screenPageViews','SessionsDuration'], inplace=True)
    output_df = output_df.sort_values(by='yearMonth', ascending=False)
    
    output_df = output_df[output_df['Sessions']>0] # | output_df['activeUsers']>0]
    output_df.reset_index(inplace=True)
    return output_df

def build_year_month(output_df):
    year_month = output_df
    
    year_month['Sessions_vs_LY'] = ((year_month['Sessions']/year_month['Sessions_LY']) - 1).apply(lambda x: round(x, 3))
    year_month['engagedSessions_vs_LY'] = (year_month['engagedSessions']/year_month['engagedSessions_LY'] - 1).apply(lambda x: round(x, 3))
    year_month['bounces_vs_LY'] = (year_month['bounces']/year_month['bounces_LY'] - 1).apply(lambda x: round(x, 3))
    year_month['activeUsers_vs_LY'] = (year_month['activeUsers']/year_month['activeUsers_LY'] - 1).apply(lambda x: round(x, 3))
    year_month['newUsers_vs_LY'] = (year_month['newUsers']/year_month['newUsers_LY'] - 1).apply(lambda x: round(x, 3))
    year_month['returningUsers_vs_LY'] = (year_month['returningUsers']/year_month['returningUsers_LY'] - 1).apply(lambda x: round(x, 3))
    
    year_month['engagedSessionsRate'] = (year_month['engagedSessions'] / year_month['Sessions']).apply(lambda x: round(x, 3))
    year_month['bounceRate'] = (year_month['bounces'] / year_month['Sessions']).apply(lambda x: round(x, 3))
    year_month['newUsersRate'] = (year_month['newUsers'] / year_month['activeUsers']).apply(lambda x: round(x, 3))
    year_month['returningUsersRate'] = (year_month['returningUsers'] / year_month['activeUsers']).apply(lambda x: round(x, 3))
    
    year_month[['Sessions','engagedSessions','activeUsers','newUsers']] = year_month[['Sessions','engagedSessions','activeUsers','newUsers']].fillna(0)
    
    year_month.sort_values('yearMonth', ascending=False, inplace=True)
    year_month.drop(columns={'Sessions_LY','engagedSessions_LY','bounces_LY','activeUsers_LY','newUsers_LY','returningUsers_LY'}, inplace=True)
    
    year_month['Sessions Engagées'] = year_month['engagedSessions']
    year_month['Bounces'] = year_month['bounces']
    year_month['Users de Retour'] = year_month['returningUsers']
    year_month['Users Nouveaux'] = year_month['newUsers']
    return year_month

def build_funnel(funnel_df):
    funnel_df = funnel_df[['screenPageViews', 'Sessions', 'engagedSessions','activeUsers', 'newUsers', 'returningUsers', 'interet_par_les_catalogues', 'download', 'demande_contact_realisee']].sum()#agg('sum')
    funnel_df = funnel_df.rename({'screenPageViews':'Pages Vues', 'Sessions':'Sessions', 'activeUsers':'Users Actifs',
                                    'engagedSessions':'Sessions Engagées', 'newUsers':'Users Nouveaux', 'returningUsers':'Users de Retour',
                                    'interet_par_les_catalogues':'Prospect Vues Catalogue', 'download':'Prospect Downloads Catalogue', 'demande_contact_realisee':'Prospect Formulaires Envoyés'})
    funnel_df = funnel_df.reset_index().rename(columns={0:'Nombre', 'index':'Étape'})
    funnel_df['Type'] = funnel_df['Étape'].map(lambda x: 'Users' if x[0:5]=='Users' else 'Prospects' if x[0:8]=='Prospect' else 'Sessions')
    funnel_df = funnel_df.set_index('Étape')
    funnel_df = funnel_df.rename(index={'Prospect Vues Catalogue':'Vues Catalogue','Prospect Downloads Catalogue':'Downloads Catalogue','Prospect Formulaires Envoyés':'Formulaires Envoyés'})
    funnel_df['Nombre'] = funnel_df['Nombre'].values.astype('int')
    funnel_df['Nombre'] = funnel_df['Nombre'].map(lambda x: round(x,-2) if x>10000 else round(x,-1) if x>100 else round(x,0))
    funnel_df = funnel_df.reset_index()
    # funnel_df = funnel_df.loc[~funnel_df['Nombre']==0]
    return funnel_df

def build_channel(output_df):
    channel = output_df.copy()
    channel = channel.groupby(['yearMonth', 'firstUserDefaultChannelGroup']).agg(engagedSessions=('engagedSessions', 'sum'), activeUsers=('activeUsers','sum'))
    channel.reset_index(names=['yearMonth', 'firstUserDefaultChannelGroup'], inplace=True)
    channel_total = channel.groupby(['yearMonth']).agg(engagedSessions=('engagedSessions', 'sum'), activeUsers=('activeUsers','sum'))
    channel_total.reset_index(names=['yearMonth'], inplace=True)
    channel = pd.merge(channel, channel_total, on='yearMonth', how='left', suffixes=('','_total'))
    channel['Percent'] = (channel['activeUsers']/channel['activeUsers_total']).apply(lambda x: round(100*x,0))
    channel['Percent'] = channel['Percent'].apply(lambda x: f"{x:.0f}%".format() if x>5 else '').astype('str')
    channel['activeUsers_label'] = channel['activeUsers'].apply(lambda x: f"  ({x:.0f})".format() if x>100 else '').astype('str')
    channel['Label'] = channel['Percent'] + channel['activeUsers_label'] #.values.astype('str') + ')'
    channel['engagedSessions_Percent'] = (channel['engagedSessions']/channel['engagedSessions_total']).apply(lambda x: round(100*x,0))
    channel['engagedSessions_Percent'] = channel['engagedSessions_Percent'].apply(lambda x: f"{x:.0f}%".format() if x>10 else '').astype('str')
    channel['engagedSessions_Label'] = channel['engagedSessions'].apply(lambda x: f"  ({x:.0f})".format() if x>100 else '').astype('str')
    channel['Label_bis'] = channel['engagedSessions_Percent'] + channel['engagedSessions_Label'] #.values.astype('str') + ')'
    channel = channel.rename(columns={'yearMonth':'yearMonth','firstUserDefaultChannelGroup':'Channel', 'activeUsers':'activeUsers', 'engagedSessions':'engagedSessions'})
    # st.write(channel)
    return channel

def monthly_traffic_chart(output_df):
    monthly_users_pivot = pd.pivot_table(output_df, 
                                        columns=['sessionMedium'], 
                                        index=['month'], 
                                        values=['activeUsers'], 
                                        aggfunc = 'sum',
                                        fill_value=0).droplevel(0, axis=1)
    return monthly_users_pivot

def traffic_report(end_date_input, start_date_input, property_id, client, country_filter, firstUserDefaultChannelGroup_filter):        
    landing_pages_request = RunReportRequest(
                property='properties/'+property_id,
                dimensions=[Dimension(name="country"),
                            Dimension(name="landingPage"),
                            Dimension(name="pagePath"),
                            Dimension(name="firstUserDefaultChannelGroup")],
                metrics=[Metric(name="activeUsers"),
                     Metric(name="Sessions"),
                     Metric(name="engagedSessions"),
                     Metric(name="averageSessionDuration")],
                order_bys = [OrderBy(metric = {'metric_name': 'activeUsers'}, desc = True)],
                date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))]
    )
    
    # Produce Top pages output tables
    table_requested = format_report(client, landing_pages_request)
    
    if country_filter:
        table_requested = table_requested[table_requested['country'].isin(country_filter)]
    
    if firstUserDefaultChannelGroup_filter:
        table_requested = table_requested[table_requested['firstUserDefaultChannelGroup'].isin(firstUserDefaultChannelGroup_filter)]
    
    table_requested['activeUsers'] = table_requested['activeUsers'].astype('int') 
    table_requested['engagedSessions'] = table_requested['engagedSessions'].astype('int')
    table_requested['averageSessionDuration'] = table_requested['averageSessionDuration'].apply(lambda x: round(x,0)).astype('float')
    table_requested['SessionsDuration'] = table_requested['Sessions'] * table_requested['averageSessionDuration'] # .apply(lambda x: round(x,0)).astype('float')
    table_requested.drop(columns=['averageSessionDuration'], inplace=True)
    
    countries_table = table_requested.groupby('country').sum().sort_values('activeUsers', ascending=False).reset_index()
    countries_table['averageSessionDuration'] = (countries_table['SessionsDuration']/countries_table['Sessions']).apply(lambda x: round(x,0))
    countries_table.drop(columns=['SessionsDuration','Sessions'], inplace=True)
    
    landing_table = table_requested.groupby('landingPage').sum().sort_values('activeUsers', ascending=False).reset_index()
    landing_table['averageSessionDuration'] = (landing_table['SessionsDuration']/landing_table['Sessions']).apply(lambda x: round(x,0))
    landing_table.drop(columns=['SessionsDuration','Sessions'], inplace=True)
    
    pages_table = table_requested.groupby('pagePath').sum().sort_values('activeUsers', ascending=False).reset_index()
    pages_table['averageSessionDuration'] = (pages_table['SessionsDuration']/pages_table['Sessions']).apply(lambda x: round(x,0))
    pages_table.drop(columns=['SessionsDuration','Sessions'], inplace=True)

    return landing_table, pages_table, countries_table

def color_background(value):
    if value<-0.50 or value>0.5:
        return f"color: white"
        
    elif value<-0.01:
        return f"color: darkred"
        # return f"background-color: linear-gradient(90deg,#fa8072 {100}%, transparent {50}%);"
        # return f"background-color: #fa8072, transparency:{-value*100};"
        
    elif value>0.01:
        return f"color: darkgreen"
        # return f"background: #green; opacity:{value/100};"
        
    else:
        return f"color: gray"

def color_rate(value):
    return f"color: #B0B0B0"

## Export to Excel
def export_to_excel(output_df):
    output_df.reset_index().to_excel('GA4_python_output.xlsx', sheet_name = 'GA4_report', engine = 'xlsxwriter')

## Export to CSV
def export_to_csv(output_df):
    output_df.to_csv('GA4_python_output.csv')
