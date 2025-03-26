## SUPPORT FUNCTIONS FOR PROPER RUNNING OF STREAMLIT APP
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

channels_map={"Unassigned"   : "1", "Paid Search"       : "2",
            "Email"         : "3" , "Referral"        :"4",
            "Organic Shopping":"5", "Organic Social"  :"6",
            "Direct"          :"7", "Organic Search": "8"}

def request_ga_data(property_id, start_date_input, end_date_input):
    return RunReportRequest(
            property='properties/'+property_id,
            dimensions=[Dimension(name="yearMonth"), #Dimension(name="year"), Dimension(name="month"), # Dimension(name="week"), # Dimension(name="date"),
                        Dimension(name="country"), # Dimension(name="sessionSourceMedium")], # Dimension(name="sessionMedium"), # Dimension(name="defaultChannelGroup")],       # NOT POSSIBLE TO CALCULATE NEW VISITORS
                        # Dimension(name="landingPage"),
                        # Dimension(name="pagePath"),],
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
            date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],
        )

def request_ga_key_events(property_id, start_date_input, end_date_input):
    return RunReportRequest(
            property='properties/'+property_id,
            dimensions=[Dimension(name="yearMonth"), #Dimension(name="year"), Dimension(name="month"), # Dimension(name="week"), # Dimension(name="date"),
                        Dimension(name="country"), # Dimension(name="sessionSourceMedium")], # Dimension(name="sessionMedium"), # Dimension(name="defaultChannelGroup")],       # NOT POSSIBLE TO CALCULATE NEW VISITORS
                        Dimension(name="firstUserDefaultChannelGroup"),
                        Dimension(name="eventName")],
            metrics=[Metric(name="keyEvents")],
            order_bys = [OrderBy(dimension = {'dimension_name': 'yearMonth'}), #OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}), # OrderBy(dimension = {'dimension_name': 'year'}), OrderBy(dimension = {'dimension_name': 'month'}),
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

def rename_cols_df(df_final):
    df_final = df_final.rename(columns={'engagedSessions':'Sessions Engagées', 'bounces':'Bounces',
                               'returningUsers':'Visiteurs de Retour', 'newUsers':'Visiteurs Nouveaux',
                               'downloads':'Prospects Catalogue','demande_contact_realisee':'Prospects Formulaire'},)
                    #   inplace=False)
    return df_final

def build_df_final(output_df):
    df_final = output_df.copy()
    output_df=output_df.fillna(0)
    
    # Rectifying data type
    df_final['activeUsers'] = df_final['activeUsers'].values.astype('int')
    df_final['newUsers'] = df_final['newUsers'].values.astype('int')

    # Creating new & deleting avg columns on dataframe
    df_final['yearMonth'] = pd.to_datetime(df_final['yearMonth'], format='%Y%m')
    df_final['yearMonth'] = df_final['yearMonth'].dt.strftime('%Y-%m %b')
    df_final['activeUsers'] = df_final['activeUsers'].astype('int') 
    df_final['engagedSessions'] = df_final['engagedSessions'].astype('int')
    
    # df_final.drop(columns={'year', 'month'})
    df_final.sort_values('yearMonth', ascending=False, inplace=True)

    return df_final

# FOR GRAPH 1
def build_funnel(df_final):
    funnel_df = df_final[['screenPageViews', 'Sessions', 'engagedSessions','activeUsers', 'newUsers', 'returningUsers', 'interet_par_les_catalogues', 'download', 'demande_contact_realisee']].sum()#agg('sum')
    # funnel_df = df_final[['screenPageViews', 'Sessions', 'Sessions Engagées','Visiteurs Actifs', 'Visiteurs Nouveaux', 'returningUsers', 'interet_par_les_catalogues', 'download', 'demande_contact_realisee']].sum()#agg('sum')
    funnel_df = funnel_df.rename({'screenPageViews':'Pages Vues', 'Sessions':'Sessions', 'activeUsers':'Visiteurs Actifs',
                                    'engagedSessions':'Sessions Engagées', 'newUsers':'Visiteurs Nouveaux', 'returningUsers':'Visiteurs de Retour',
                                    'interet_par_les_catalogues':'Prospects Vues Catalogue', 'download':'Prospects Catalogue', 'demande_contact_realisee':'Prospects Formulaire'})
    funnel_df = funnel_df.reset_index().rename(columns={0:'Nombre', 'index':'Étape'})
    funnel_df['Type'] = funnel_df['Étape'].map(lambda x: 'Visiteurs' if x[0:8]=='Visiteur' else 'Prospects' if x[0:8]=='Prospect' else 'Sessions')
    funnel_df = funnel_df.set_index('Étape')
    funnel_df = funnel_df.rename(index={'Prospects Vues Catalogue':'Vues Catalogue','Prospects Catalogue':'Prospects Catalogue','Prospects Formulaire':'Prospects Formulaire'})
    funnel_df['Nombre'] = funnel_df['Nombre'].values.astype('int')
    # st.write(funnel_df['Nombre'].values.type)
    funnel_df['Nombre'] = funnel_df['Nombre'].map(lambda x: round(x,-2) if x>10000 else round(x,-1) if x>100 else round(x,0))
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
    
    yearMonth_agg['Sessions_vs_LY'] = ((yearMonth_agg['Sessions']/yearMonth_agg['Sessions_LY']) - 1).apply(lambda x: round(x, 3))
    yearMonth_agg['engagedSessions_vs_LY'] = (yearMonth_agg['engagedSessions']/yearMonth_agg['engagedSessions_LY'] - 1).apply(lambda x: round(x, 3))
    yearMonth_agg['bounces_vs_LY'] = (yearMonth_agg['bounces']/yearMonth_agg['bounces_LY'] - 1).apply(lambda x: round(x, 3))
    yearMonth_agg['activeUsers_vs_LY'] = (yearMonth_agg['activeUsers']/yearMonth_agg['activeUsers_LY'] - 1).apply(lambda x: round(x, 3))
    yearMonth_agg['newUsers_vs_LY'] = (yearMonth_agg['newUsers']/yearMonth_agg['newUsers_LY'] - 1).apply(lambda x: round(x, 3))
    yearMonth_agg['returningUsers_vs_LY'] = (yearMonth_agg['returningUsers']/yearMonth_agg['returningUsers_LY'] - 1).apply(lambda x: round(x, 3))
    yearMonth_agg.drop(columns={'Sessions_LY','engagedSessions_LY','bounces_LY','activeUsers_LY','newUsers_LY','returningUsers_LY'}, inplace=True)
    
    yearMonth_agg['engagedSessionsRate'] = (yearMonth_agg['engagedSessions'] / yearMonth_agg['Sessions']).apply(lambda x: round(x, 3))
    yearMonth_agg['bounceRate'] = (yearMonth_agg['bounces'] / yearMonth_agg['Sessions']).apply(lambda x: round(x, 3))
    yearMonth_agg['newUsersRate'] = (yearMonth_agg['newUsers'] / yearMonth_agg['activeUsers']).apply(lambda x: round(x, 3))
    yearMonth_agg['returningUsersRate'] = (yearMonth_agg['returningUsers'] / yearMonth_agg['activeUsers']).apply(lambda x: round(x, 3))
    
    yearMonth_agg['bounceRate'] = (yearMonth_agg['bounces'] / yearMonth_agg['Sessions'])
    yearMonth_agg['bounceRate_txt'] = yearMonth_agg['bounceRate'].map(lambda x: f"{x*100:0.0f}%")
    yearMonth_agg['avgScreenViews'] = yearMonth_agg['screenPageViews'] / yearMonth_agg['Sessions']
    yearMonth_agg['avgScreenViews'] = yearMonth_agg['avgScreenViews'].map('{:.1f}'.format) #.values.astype('str')
    yearMonth_agg['avgSessionDuration'] = yearMonth_agg['SessionsDuration'] / yearMonth_agg['Sessions']
    yearMonth_agg['avgSessionDuration'] = yearMonth_agg['avgSessionDuration'].map('{:.1f}'.format) #.values.astype('str')
    yearMonth_agg.drop(columns=['screenPageViews','SessionsDuration'], inplace=True)
    yearMonth_agg = yearMonth_agg.sort_values(by='yearMonth', ascending=False)
    
    yearMonth_agg = yearMonth_agg[yearMonth_agg['Sessions']>0] # | yearMonth_agg['activeUsers']>0]
    yearMonth_agg.reset_index(inplace=True)
    
    # st.write(yearMonth_pivot)
    
    return yearMonth_agg

# FOR GRAPH 3
def build_channel(df_final):
    channel_df = df_final.copy()
    channel_df = channel_df.groupby(['yearMonth', 'firstUserDefaultChannelGroup']).agg(engagedSessions=('engagedSessions', 'sum'), activeUsers=('activeUsers','sum'))
    channel_df.reset_index(names=['yearMonth', 'firstUserDefaultChannelGroup'], inplace=True)
    
    channel_total = channel_df.groupby(['yearMonth']).agg(engagedSessions=('engagedSessions', 'sum'), activeUsers=('activeUsers','sum'))
    channel_total.reset_index(names=['yearMonth'], inplace=True)
    
    channel_df = pd.merge(channel_df, channel_total, on='yearMonth', how='left', suffixes=('','_total'))
    channel_df['Percent'] = (channel_df['activeUsers']/channel_df['activeUsers_total']).apply(lambda x: round(100*x,0))
    channel_df['Percent'] = channel_df['Percent'].apply(lambda x: f"{x:.0f}%".format() if x>5 else '').astype('str')
    channel_df['activeUsers_label'] = channel_df['activeUsers'].apply(lambda x: f"  ({x:.0f})".format() if x>100 else '').astype('str')
    channel_df['Label'] = channel_df['Percent'] + channel_df['activeUsers_label'] #.values.astype('str') + ')'
    channel_df['engagedSessions_Percent'] = (channel_df['engagedSessions']/channel_df['engagedSessions_total']).apply(lambda x: round(100*x,0))
    channel_df['engagedSessions_Percent'] = channel_df['engagedSessions_Percent'].apply(lambda x: f"{x:.0f}%".format() if x>10 else '').astype('str')
    channel_df['engagedSessions_Label'] = channel_df['engagedSessions'].apply(lambda x: f"  ({x:.0f})".format() if x>100 else '').astype('str')
    channel_df['Label_bis'] = channel_df['engagedSessions_Percent'] + channel_df['engagedSessions_Label'] #.values.astype('str') + ')'
    channel_df = channel_df.rename(columns={'yearMonth':'yearMonth','firstUserDefaultChannelGroup':'Channel', 'activeUsers':'activeUsers', 'engagedSessions':'engagedSessions'})
    
    channel_pivot = pd.pivot_table(channel_df, index=['yearMonth', 'Channel'],
                             values=['engagedSessions','activeUsers'],
                             aggfunc='sum').reset_index()
    channel_unpivot = channel_pivot.melt(id_vars=['yearMonth','Channel'],
                                       value_vars=['activeUsers','engagedSessions'],
                                       var_name="SubType", value_name="Nombre")
    channel_unpivot['Type'] = channel_unpivot['SubType'].map(lambda x: 'Users' if x[-5:]=='Users' else 'Sessions')
    channel_unpivot['Channel_DEF'] = channel_unpivot['Channel'].map(lambda x: str(channels_map[x]) + '-' + str(x))
    channel_unpivot = channel_unpivot.sort_values(by='Channel_DEF', ascending=True)
    channel_unpivot.reset_index(inplace=True)
    # st.write(channel_unpivot)
    
    return channel_unpivot

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
