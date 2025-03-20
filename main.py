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

def print_hello():
    print("Hello World")

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
    # sns.set_theme()
    # monhtly_users_pivot.plot.bar(y = ['(none)', 'organic', 'referral', '(not set)'], stacked = True,
    #                             colormap = 'Dark2',
    #                             figsize=(7,5), title = 'Active Users by Month')
    # plt.legend(title = 'User Medium', bbox_to_anchor = (1.05, 0.5))
    # plt.title('Active Users by Month', fontsize = 15)
    return monthly_users_pivot

def traffic_report(end_date_input, start_date_input, property_id, client):
    daily_traffic_request = RunReportRequest(
        property='properties/'+property_id,
        dimensions=[Dimension(name="date"), 
                    Dimension(name="sessionMedium")],
        metrics=[Metric(name="activeUsers")],
        order_bys = [OrderBy(dimension = {'dimension_name': 'date'}),
                    OrderBy(dimension = {'dimension_name': 'sessionMedium'})],
        date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))],
    )

    page_users_request = RunReportRequest(
                property='properties/'+property_id,
                dimensions=[Dimension(name="pagePath")],
                metrics=[Metric(name="activeUsers"),
                     Metric(name="engagedSessions"),
                     Metric(name="averageSessionDuration")],
                order_bys = [OrderBy(metric = {'metric_name': 'activeUsers'}, desc = True)],
                date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))]
    )
        
    landing_page_users_request = RunReportRequest(
                property='properties/'+property_id,
                dimensions=[Dimension(name="landingPage")],
                metrics=[Metric(name="activeUsers"),
                     Metric(name="engagedSessions"),
                     Metric(name="averageSessionDuration")],
                order_bys = [OrderBy(metric = {'metric_name': 'activeUsers'}, desc = True)],
                date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))]
    )
    
    countries_users_request = RunReportRequest(
                property='properties/'+property_id,
                dimensions=[Dimension(name="country")],
                metrics=[Metric(name="activeUsers"),
                     Metric(name="engagedSessions"),
                     Metric(name="averageSessionDuration")],
                order_bys = [OrderBy(metric = {'metric_name': 'activeUsers'}, desc = True)],
                date_ranges=[DateRange(start_date=start_date_input.strftime("%Y-%m-%d"), end_date=end_date_input.strftime("%Y-%m-%d"))]
    )

    daily_traffic = format_report(client, daily_traffic_request).reset_index()
    active_users_pivot = pd.pivot_table(daily_traffic, 
                                     columns=['sessionMedium'], 
                                     index=['date'], 
                                     values=['activeUsers'], 
                                     aggfunc = 'sum',
                                     fill_value=0).droplevel(0, axis=1)
    active_users_pivot.index = active_users_pivot.index.str.slice(start=4)
    
    # Produce pie and line charts
    fig, (axs1, axs2) = plt.subplots(1,2, figsize = (14, 4), gridspec_kw={'width_ratios': [1, 2]})
    pie_data = daily_traffic.groupby(by = ['sessionMedium']).sum().sort_values(by = ['activeUsers'], ascending = False)

    pie_data.plot.pie(ax = axs1,
                      colormap = 'Dark2',
                      y = 'activeUsers',
                      title = 'Active Users by Medium',
                      legend = False, 
                      label = False,
                      startangle = 0, 
                      autopct = lambda p:f'{p:.0f}%').set_ylabel('')
    
    active_users_pivot.plot.line(ax = axs2, 
                                 colormap = 'Dark2',
                                 y = pie_data.index, 
                                 title = 'Active Users by Day')

    axs2.legend(title = 'User Medium', bbox_to_anchor = (1.05, 0.6))

    plt.show();
    
    # Produce Top pages output tables
    landing_table = format_report(client, landing_page_users_request)
    landing_table['activeUsers'] = landing_table['activeUsers'].astype('int') 
    
    page_users_table = format_report(client, page_users_request)
    page_users_table['activeUsers'] = page_users_table['activeUsers'].astype('int') 
    
    countries_table = format_report(client, countries_users_request)
    countries_table['activeUsers'] = countries_table['activeUsers'].astype('int') 
    
    return landing_table, page_users_table, countries_table
