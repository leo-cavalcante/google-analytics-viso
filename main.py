## Google Analytics 4 (GA4) Data in Pyton Using run_report
# import os
import numpy as np
import pandas as pd
# import seaborn as sns
# import streamlit as st
# from datetime import date
# from datetime import timedelta
import matplotlib.pyplot as plt
from google.analytics.data_v1beta.types import Metric
from google.analytics.data_v1beta.types import OrderBy
from google.analytics.data_v1beta.types import DateRange
from google.analytics.data_v1beta.types import Dimension
from google.analytics.data_v1beta.types import RunReportRequest 
# from google.analytics.data_v1beta import BetaAnalyticsDataClient

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

## Export to Excel
def export_to_excel(output_df):
    output_df.reset_index().to_excel('GA4_python_output.xlsx', sheet_name = 'GA4_report', engine = 'xlsxwriter')

## Export to CSV
def export_to_csv(output_df):
    output_df.to_csv('GA4_python_output.csv')

def monthly_traffic_chart(output_df):
    monthly_users_pivot = pd.pivot_table(output_df, 
                                        columns=['sessionMedium'], 
                                        index=['month'], 
                                        values=['activeUsers'], 
                                        aggfunc = 'sum',
                                        fill_value=0).droplevel(0, axis=1)
    return monthly_users_pivot

def traffic_report(end_date_input, start_date_input, property_id, client):
    # daily_traffic_request = RunReportRequest(
    #     property='properties/'+property_id,
    #     dimensions=[Dimension(name="date"), 
    #                 Dimension(name="sessionMedium")],
    #     metrics=[Metric(name="activeUsers")],
    #     order_bys = [OrderBy(dimension = {'dimension_name': 'date'}),
    #                 OrderBy(dimension = {'dimension_name': 'sessionMedium'})],
    #     date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],
    # )

    pages_request = RunReportRequest(
                property='properties/'+property_id,
                dimensions=[Dimension(name="pagePath")],
                metrics=[Metric(name="activeUsers"),
                    #  Metric(name="Sessions"),
                     Metric(name="engagedSessions"),
                     Metric(name="averageSessionDuration")],
                order_bys = [OrderBy(metric = {'metric_name': 'activeUsers'}, desc = True)],
                date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))]
    )
        
    landing_pages_request = RunReportRequest(
                property='properties/'+property_id,
                dimensions=[Dimension(name="landingPage")],
                metrics=[Metric(name="activeUsers"),
                    #  Metric(name="Sessions"),
                     Metric(name="engagedSessions"),
                     Metric(name="averageSessionDuration")],
                order_bys = [OrderBy(metric = {'metric_name': 'activeUsers'}, desc = True)],
                date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))]
    )
    
    countries_users_request = RunReportRequest(
                property='properties/'+property_id,
                dimensions=[Dimension(name="country")],
                metrics=[Metric(name="activeUsers"),
                    #  Metric(name="Sessions"),
                     Metric(name="engagedSessions"),
                     Metric(name="averageSessionDuration")],
                order_bys = [OrderBy(metric = {'metric_name': 'activeUsers'}, desc = True)],
                date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))]
    )
    
    # Produce Top pages output tables
    countries_table = format_report(client, countries_users_request)
    countries_table['activeUsers'] = countries_table['activeUsers'].astype('int') 
    countries_table['engagedSessions'] = countries_table['engagedSessions'].astype('int')
    # countries_table['Sessions'] = countries_table['Sessions'].astype('int')
    countries_table['averageSessionDuration'] = countries_table['averageSessionDuration'].apply(lambda x: round(x,0)).astype('float')

    landing_table = format_report(client, landing_pages_request)
    landing_table['activeUsers'] = landing_table['activeUsers'].astype('int') 
    landing_table['engagedSessions'] = landing_table['engagedSessions'].astype('int')
    # landing_table['Sessions'] = landing_table['Sessions'].astype('int')
    landing_table['averageSessionDuration'] = landing_table['averageSessionDuration'].apply(lambda x: round(x,0)).astype('float')
    # landing_table['SessionsDuration'] = landing_table['Sessions'] * landing_table['averageSessionDuration'] 
    
    pages_table = format_report(client, pages_request)
    pages_table['activeUsers'] = pages_table['activeUsers'].astype('int') 
    pages_table['engagedSessions'] = pages_table['engagedSessions'].astype('int') 
    # pages_table['Sessions'] = pages_table['Sessions'].astype('int')
    pages_table['averageSessionDuration'] = pages_table['averageSessionDuration'].apply(lambda x: round(x,0)).astype('float')    

    # daily_traffic = format_report(client, daily_traffic_request).reset_index()
    # active_users_pivot = pd.pivot_table(daily_traffic, 
    #                                  columns=['sessionMedium'], 
    #                                  index=['date'], 
    #                                  values=['activeUsers'], 
    #                                  aggfunc = 'sum',
    #                                  fill_value=0).droplevel(0, axis=1)
    # active_users_pivot.index = active_users_pivot.index.str.slice(start=4)
    
    # Produce pie and line charts
    # fig, (axs1, axs2) = plt.subplots(1,2, figsize = (14, 4), gridspec_kw={'width_ratios': [1, 2]})
    # pie_data = daily_traffic.groupby(by = ['sessionMedium']).sum().sort_values(by = ['activeUsers'], ascending = False)

    # pie_data.plot.pie(ax = axs1,
    #                   colormap = 'Dark2',
    #                   y = 'activeUsers',
    #                   title = 'Active Users by Medium',
    #                   legend = False, 
    #                   label = False,
    #                   startangle = 0, 
    #                   autopct = lambda p:f'{p:.0f}%').set_ylabel('')
    
    # active_users_pivot.plot.line(ax = axs2, 
    #                              colormap = 'Dark2',
    #                              y = pie_data.index, 
    #                              title = 'Active Users by Day')

    # axs2.legend(title = 'User Medium', bbox_to_anchor = (1.05, 0.6))

    # plt.show();
    
    
    return landing_table, pages_table, countries_table

def aggregate_yearMonth(output_df):
    output_df['yearMonth'] = pd.to_datetime(output_df['yearMonth'], format='%Y-%m %b')
    output_df['yearMonth'] = output_df['yearMonth'].dt.strftime('%Y-%m %b')
    output_df = output_df.groupby(by='yearMonth').agg(Sessions=('Sessions', 'sum'), engagedSessions=('engagedSessions', 'sum'),
                                                        bounces=('bounces','sum'), activeUsers=('activeUsers','sum'),
                                                        newUsers=('newUsers','sum'), returningUsers=('returningUsers', 'sum'),
                                                        screenPageViews=('screenPageViews', 'sum'),
                                                        SessionsDuration=('SessionsDuration','sum'))
    output_df['bounceRate'] = (output_df['bounces'] / output_df['Sessions'])
    output_df['bounceRate_txt'] = output_df['bounceRate'].map(lambda x: f"{x*100:0.0f}%")
    output_df['avgScreenViews'] = output_df['screenPageViews'] / output_df['Sessions']
    output_df['avgScreenViews'] = output_df['avgScreenViews'].map('{:.1f}'.format) #.values.astype('str')
    output_df['avgSessionDuration'] = output_df['SessionsDuration'] / output_df['Sessions']
    output_df['avgSessionDuration'] = output_df['avgSessionDuration'].map('{:.1f}'.format) #.values.astype('str')
    output_df.drop(columns=['screenPageViews','SessionsDuration'], inplace=True)
    output_df.reset_index(inplace=True)
    output_df = output_df.sort_values(by='yearMonth', ascending=False)
    
    return output_df

def vs_LY(output_df, comp_df):
    
    output_df = aggregate_yearMonth(output_df)
    comp_df = aggregate_yearMonth(comp_df)
    
    output_df = pd.merge(output_df, comp_df, on=['yearMonth'], suffixes=('', '_LY'))
    
    output_df['Sessions_vs_LY'] = ((output_df['Sessions']/output_df['Sessions_LY']) - 1).apply(lambda x: round(x, 3))
    output_df['engagedSessions_vs_LY'] = (output_df['engagedSessions']/output_df['engagedSessions_LY'] - 1).apply(lambda x: round(x, 3))
    output_df['bounces_vs_LY'] = (output_df['bounces']/output_df['bounces_LY'] - 1).apply(lambda x: round(x, 3))
    output_df['activeUsers_vs_LY'] = (output_df['activeUsers']/output_df['activeUsers_LY'] - 1).apply(lambda x: round(x, 3))
    output_df['newUsers_vs_LY'] = (output_df['newUsers']/output_df['newUsers_LY'] - 1).apply(lambda x: round(x, 3))
    output_df['returningUsers_vs_LY'] = (output_df['returningUsers']/output_df['returningUsers_LY'] - 1).apply(lambda x: round(x, 3))
    
    output_df.drop(columns={'Sessions_LY','engagedSessions_LY','bounces_LY','activeUsers_LY','newUsers_LY','returningUsers_LY'}, inplace=True) #,'SessionsDuration_LY','averageSessionDuration_LY','screenPageViews_LY'
    
    output_df['engagedSessionsRate'] = (output_df['engagedSessions'] / output_df['Sessions']).apply(lambda x: round(x, 3))
    # output_df['bounceRate'] = output_df['bounces'] / output_df['Sessions']
    output_df['newUsersRate'] = (output_df['newUsers'] / output_df['activeUsers']).apply(lambda x: round(x, 3))
    output_df['returningUsersRate'] = (output_df['returningUsers'] / output_df['activeUsers']).apply(lambda x: round(x, 3))
    
    return output_df

def color_background(value):
    # if '%' in str(value):
    #     value = float(str(value).strip('%'))
    #     value = value/100
    
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
