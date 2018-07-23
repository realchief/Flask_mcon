#!/usr/bin/env python
# coding: utf8

"""
1. grab costs and Part 1 of subscriber conversions from:
Source Name - GEO - Push Subs
2. grab Part 2 of subscribers from backflow, using GEO > Custom Variable #2 i think in:
Backflow - Global - Push Subs
3. combine part 1 subs from Source Name > GEO + Backflow which is part 2 of subs > add them per geo and source
4. grab revenue from Push - Global - Revenue & Push - Global - New Sub : Revenue
in the Push - Global - Revenue > You can associate revenue by GEO > Custom Variable for Source. Will also need to track GEO > Affiliate Network for ouput reporting of knowing what aff networks have what rev, etc
but for the New Sub : Revenue we dont have assigned placements tracking conversions so easiest way is just to lump it all together by GEO > Affiliate Network
5. Using the above data we can compute all the other metrics we need which are, all plus the ones we need to computer are:
Cost
Revenue
Profit
ROI
CPA
RPS = revenue for source / subscribers
EPS  = profit from source / subscribers

these metrics are needed at the source/geo level and the total daily values and total monthly values
"""

import requests
import json
import unicodedata
import arrow
from datetime import datetime
from sqlalchemy import create_engine
# Generate and validate token for accessing voluum
token_request = requests.post(
    'https://api.voluum.com/auth/access/session',
    json={
        "accessId": "ace793ba-7917-4013-86bd-7f888aa0caba",
        "accessKey": "7PMpMgC3kTU4cb3c9cAd3bd48mg-tkrYFgW7"})
token = str(token_request.json()['token'])
headers = {'content-type': 'application/json', 'cwauth-token': token}
token_validate = requests.get(
    'https://api.voluum.com/auth/session',
    headers=headers)

def build_report(from_date, to_date):
    subscriber_counts = {}
    #from_date = "2018-03-23T00:00:00Z"
    #to_date = "2018-03-24T00:00:00Z"
    # Request stats for backflow campaign
    backflow_report_request = requests.get('https://api.voluum.com/report?from={}&to={}&tz=America%2FChicago&sort=visits&direction=desc&columns=customVariable2&columns=countryName&columns=visits&columns=clicks&columns=conversions&columns=revenue&columns=cost&columns=profit&columns=cpv&columns=ctr&columns=cr&columns=cv&columns=roi&columns=epv&columns=ap&columns=ecpa&groupBy=custom-variable-2&groupBy=country-code&offset=0&limit=50&include=ACTIVE&conversionTimeMode=VISIT&filter1=campaign&filter1Value=5fcf8ab6-94dc-4fa1-acc7-95b639f6ba11'.format(from_date, to_date), headers=headers)
    for campaign in backflow_report_request.json()['rows']:
        if campaign['customConversions1'] > 0:
            cost = None
            subscribers = None
            ecpa = None
            eps = None
            rps = None
            profit = None
            revenue = None
            roi = None
            print('\n\n')
            print('Country:')
            print(campaign['countryName'])
            try:
                country = campaign['countryName']
            except:
                country = 'Unknown'
            print('Traffic Source:')
            print(campaign['customVariable2'])
            try:
                traffic_source = campaign['customVariable2']
                if traffic_source == '':
                    traffic_source = 'Unknown'
            except:
                traffic_source = 'Unknown'
            print('Subscribers:')
            print(campaign['customConversions1'])
            subscribers = campaign['customConversions1']
            print('Cost:')
            print(campaign['cost'])
            cost = campaign['cost']
            print('ECPA:')
            print(campaign['ecpa'])
            ecpa = campaign['ecpa']
            source_country = traffic_source + '-' + country
            if source_country in subscriber_counts.keys():
                subscriber_counts[source_country]['subscribers'] += subscribers
                subscriber_counts[source_country]['cost'] += cost
                ecpa = subscriber_counts[source_country]['cost'] / subscriber_counts[source_country]['subscribers']
                subscriber_counts[source_country]['ecpa'] = ecpa
            else:
                subscriber_counts[source_country] = {}
                subscriber_counts[source_country]['subscribers'] = subscribers
                subscriber_counts[source_country]['cost'] = cost

    # Request stats for all campaigns (excluding backflow)
    campaigns_report_request = requests.get('https://api.voluum.com/report?from={}&to={}&tz=America%2FChicago&sort=visits&direction=desc&columns=campaignName&columns=visits&columns=clicks&columns=conversions&columns=revenue&columns=cost&columns=profit&columns=cpv&columns=ctr&columns=cr&columns=cv&columns=roi&columns=epv&columns=ap&columns=ecpa&groupBy=campaign&offset=0&limit=50&include=TRAFFIC&conversionTimeMode=VISIT'.format(from_date, to_date), headers=headers)
    #campaign_names = {}
    # Pull all campaigns from ZeroPark with active tag and use them to display
    # names for each campaign
    for campaign in campaigns_report_request.json()['rows']:
        if campaign['customConversions1'] > 0 and '5fcf8ab6-94dc-4fa1-acc7-95b639f6ba11' not in campaign['campaignId']:
            print('\n\n')
            print('Country:')
            print(campaign['campaignCountry'])
            country = campaign['campaignCountry']
            print('Traffic Source:')
            print(campaign['trafficSourceName'])
            traffic_source = campaign['trafficSourceName']
            if traffic_source is '':
                traffic_source = 'Unknown'
            print('Subscribers:')
            print(campaign['customConversions1'])
            subscribers = campaign['customConversions1']
            print('Cost:')
            print(campaign['cost'])
            cost = campaign['cost']
            print('ECPA:')
            print(campaign['ecpa'])
            ecpa = campaign['ecpa']
            try:
                source_country = traffic_source + '-' + country
            except:
                source_country = "Unknown-Unknown"
            if source_country in subscriber_counts.keys():
                subscriber_counts[source_country]['subscribers'] += subscribers
                subscriber_counts[source_country]['cost'] += cost
                ecpa = subscriber_counts[source_country]['cost'] / subscriber_counts[source_country]['subscribers']
                subscriber_counts[source_country]['ecpa'] = ecpa
            else:
                subscriber_counts[source_country] = {}
                subscriber_counts[source_country]['subscribers'] = subscribers
                subscriber_counts[source_country]['cost'] = cost

    # Pulling revenue information
    source_map = {
        "7Y36ZHPYtvfyn11zy5R4NQ": "PopCash",
        "Qt9xZ5sayu46amCoRrsIIw": "PopAds",
        "xwrl1gDaaSNrdL7ueAY9": "ExoClick",
        "dUAA3y5OGsDCunODuTNs": "TrafficStars",
        "vvgyDm7Rs8dUQK123zSF": "TrafficHaus",
        "Cad7abiTEloFNpWt8qHR": "TrafficHunt",
        "U75n0bcuSVjvGGu5o1Xc": "PropellorAds",
        "1Z7F2oWvSMsZm4XySehF": "Adcash",
        "MXMzzGIxSXbKCFnWRdKu": "Clickadu",
        "JysrZjjmUqx9g98xEfld": "Zeropark",
        "wFMvpasJrvvO_O4zh5FNbA": "Unknown",
        "wFMvpasJrvvO_O4zh5FNbA": "Backflow",
        "3LVE9sdseQIEpMGuR7Ud": "Reporo",
        "9V95EwUTJUeU2sIuWQ1S": "TrafficForce",
        "YMfSahHLWliSJSGLzxrx": "TrafficShop",
        "ousumM7ZqMZ3KdyphH8q": "ActiveRevenue",
        "ZyL7WtHR4j4l9DaPJqy9": "JuicyAds",
        "QkNGHlMcdb12lqefGztO": "Tonic",
        "JdEPtfXksUCQm3mfCawn": "TrafficJunky",
        "1XwkDpBqv2UfUOELchnH": "MediaHub",
        "I2axTANYbAOloQ3XF5hV": "PlugRush",
        "GyyjcYqG8XLv0dQTNhnZ": "Bidvertiser",
        "LrLYa47F2Wgw3YaX3zCR": "ReachEffect",
        "XlACoKfo30TuNh9nRi9q": "AdXpansion",
        "5ruSix1w3c06s74gqkOM": "EroAdvertising",
        "Z8mPD7ULj6pXvxK31IsV": "Adnium",
        "NKR4WyW6HjmEaULZlZDq": "Advertizer"
    }


    # Calculate revenue generated from all sources
    revenue_report_request = requests.get('https://api.voluum.com/report?from={}&to={}&tz=America%2FChicago&sort=visits&direction=desc&columns=countryName&columns=customVariable9&columns=visits&columns=clicks&columns=conversions&columns=revenue&columns=cost&columns=profit&columns=cpv&columns=ctr&columns=cr&columns=cv&columns=roi&columns=epv&columns=ap&columns=ecpa&groupBy=country-code&groupBy=custom-variable-9&offset=0&limit=50&include=ACTIVE&conversionTimeMode=VISIT&filter1=campaign&filter1Value=0faecec5-56de-4a85-acb9-49fa4902d071'.format(from_date, to_date), headers=headers)
    for row in revenue_report_request.json()['rows']:
        cost = None
        subscribers = None
        ecpa = None
        eps = None
        rps = None
        profit = None
        revenue = None
        roi = None
        country = row['countryName']
        print(country)
        try:    
            traffic_source = source_map[row['customVariable9']]
        except:
            traffic_source = 'Unknown'
        print(traffic_source)
        try:
            source_country = traffic_source + '-' + country
        except:
            source_country = 'Unknown-Unknown'
        try:
            revenue = row['revenue']
            if revenue == 0:
                revenue = None
                break
        except:
            pass
        if source_country in subscriber_counts.keys():
            if 'revenue' in subscriber_counts[source_country].keys():
                subscriber_counts[source_country]['revenue'] += revenue
            else:
                subscriber_counts[source_country]['revenue'] = revenue
            try:
                profit = subscriber_counts[source_country]['revenue'] - subscriber_counts[source_country]['cost']
                if 'profit' in subscriber_counts[source_country].keys():
                    subscriber_counts[source_country]['profit'] += profit
                else:
                    subscriber_counts[source_country]['profit'] = profit
            except:
                profit = None
            try:
                roi = subscriber_counts[source_country]['revenue'] / subscriber_counts[source_country]['cost']
            except:
                roi = None
            subscriber_counts[source_country]['roi'] = roi
            try:
                rps = subscriber_counts[source_country]['revenue'] / subscriber_counts[source_country]['subscribers']
            except:
                rps = None
            subscriber_counts[source_country]['rps'] = rps
            try:
                eps = (subscriber_counts[source_country]['revenue'] - subscriber_counts[source_country]['cost']) / subscriber_counts[source_country]['subscribers']
            except:
                eps = None
            subscriber_counts[source_country]['eps'] = eps
        else:
            subscriber_counts[source_country] = {}
            subscriber_counts[source_country]['revenue'] = revenue

    # Calculate monetizer revenue generated from new sub revenue
    # report?from=2018-04-14T00:00:00Z&to=2018-04-22T00:00:00Z&tz=America%2FChicago&sort=visits&direction=desc&columns=countryName&columns=customVariable9&columns=visits&columns=clicks&columns=conversions&columns=revenue&columns=cost&columns=profit&columns=cpv&columns=ctr&columns=cr&columns=cv&columns=roi&columns=epv&columns=ap&columns=ecpa&groupBy=country-code&groupBy=custom-variable-9&offset=0&limit=50&include=ACTIVE&conversionTimeMode=VISIT&filter1=campaign&filter1Value=596c4e0f-e9ce-4fad-bce9-eced91fcd6c5
    monetizer_revenue_report_request = requests.get('https://api.voluum.com/report?from={}&to={}&tz=America%2FChicago&sort=visits&direction=desc&columns=countryName&columns=customVariable9&columns=visits&columns=clicks&columns=conversions&columns=revenue&columns=cost&columns=profit&columns=cpv&columns=ctr&columns=cr&columns=cv&columns=roi&columns=epv&columns=ap&columns=ecpa&groupBy=country-code&groupBy=custom-variable-9&offset=0&limit=50&include=ACTIVE&conversionTimeMode=VISIT&filter1=campaign&filter1Value=596c4e0f-e9ce-4fad-bce9-eced91fcd6c5'.format(from_date, to_date), headers=headers)
    for row in monetizer_revenue_report_request.json()['rows']:
        cost = None
        subscribers = None
        ecpa = None
        eps = None
        rps = None
        profit = None
        revenue = None
        roi = None
        try:
            country = row['countryName']
        except:
            country = 'Unknown'
        if country == '':
            country = 'Unknown'
        try:    
            traffic_source = row['customVariable9']
        except:
            traffic_source = 'Unknown'
        if traffic_source == '':
            traffic_source = 'Unknown'
        print(traffic_source)
        print(country)
        try:
            source_country = traffic_source + '-' + country
        except:
            source_country = 'Unknown-Unknown'
        try:
            revenue = row['revenue']
            if revenue == 0:
                revenue = None
                break
        except:
            revenue = None
        print(revenue)
        if source_country in subscriber_counts.keys():
            try:
                if 'revenue' in subscriber_counts[source_country].keys():
                    subscriber_counts[source_country]['revenue'] += revenue
                else:
                    subscriber_counts[source_country]['revenue'] = revenue
            except:
                revenue = None
            try:
                profit = subscriber_counts[source_country]['revenue'] - subscriber_counts[source_country]['cost']
                if 'profit' in subscriber_counts[source_country].keys():
                    subscriber_counts[source_country]['profit'] += profit
                else:
                    subscriber_counts[source_country]['profit'] = profit
            except:
                profit = None
            
            try:
                roi = subscriber_counts[source_country]['revenue'] / subscriber_counts[source_country]['cost']
            except:
                roi = None 
            subscriber_counts[source_country]['roi'] = roi
            try:
                rps = subscriber_counts[source_country]['revenue'] / subscriber_counts[source_country]['subscribers']
            except:
                rps = None 
            subscriber_counts[source_country]['rps'] = rps
            try:
                eps = (subscriber_counts[source_country]['revenue'] - subscriber_counts[source_country]['cost']) / subscriber_counts[source_country]['subscribers']
            except:
                eps = None 
            subscriber_counts[source_country]['eps'] = eps
        else:
            subscriber_counts[source_country] = {}
            subscriber_counts[source_country]['revenue'] = revenue

    print(subscriber_counts)
    table="public.push_reports"
    db="pushengine"
    username="root"
    password="agdevil1"
    host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com"
    engine = create_engine("postgresql://{0}:{1}@{2}/{3}".format(username, password, host, db))
    connection = engine.connect()
    for key in subscriber_counts.keys():
        print(key)
        print(subscriber_counts[key])
        if len(set(subscriber_counts[key].values())) > 0:
            cost = None
            subscribers = None
            ecpa = None
            eps = None
            rps = None
            profit = None
            revenue = None
            roi = None
            report_date = from_date.split('T')[0]
            traffic_source = key.split('-')[0]
            country = key.split('-')[1]
            country = unicodedata.normalize('NFD', country).encode('ascii', 'ignore')
            if 'cost' in subscriber_counts[key].keys():
                cost = subscriber_counts[key]['cost']
            if 'subscribers' in subscriber_counts[key].keys():
                subscribers = subscriber_counts[key]['subscribers']
            if 'ecpa' in subscriber_counts[key].keys():
                ecpa = subscriber_counts[key]['ecpa']
            if 'eps' in subscriber_counts[key].keys():
                eps = subscriber_counts[key]['eps']
            if 'rps' in subscriber_counts[key].keys():
                rps = subscriber_counts[key]['rps']
            if 'profit' in subscriber_counts[key].keys():
                profit = subscriber_counts[key]['profit']
            if 'revenue' in subscriber_counts[key].keys():
                revenue = subscriber_counts[key]['revenue']
                if revenue == 0:
                    break
            if 'roi' in subscriber_counts[key].keys():
                roi = subscriber_counts[key]['roi']
            sql = "INSERT INTO push_reports (report_date, traffic_source, country"
            if cost:
                sql += ", cost"
            if subscribers:
                sql += ", subscribers"
            if ecpa:
                sql += ", ecpa"
            if eps:
                sql += ", eps"
            if rps:
                sql += ", rps"
            if profit:
                sql += ", profit"
            if revenue:
                sql += ", revenue"
            if roi:
                sql += ", roi"
            sql += ") values ('{}', '{}', '{}'".format(report_date, traffic_source, country)
            if cost:
                sql += ", '{}'".format(round(float(cost), 2))
            if subscribers:
                sql += ", '{}'".format(subscribers)
            if ecpa:
                sql += ", '{}'".format(round(float(ecpa), 3))
            if eps:
                sql += ", '{}'".format(round(float(eps), 3))
            if rps:
                sql += ", '{}'".format(round(float(rps), 3))
            if profit:
                sql += ", '{}'".format(round(float(profit), 2))
            if revenue:
                sql += ", '{}'".format(round(float(revenue), 2))
            if roi:
                sql += ", '{}'".format(round(float(roi), 2))
            sql += ")"  
            print(sql)  
            connection.execute(sql)
        else:
            print('Insufficient data for report')

    result = connection.execute("select * from public.push_reports")
    for row in result:
        print(row)
    connection.close()
        # insert into push_reports (report_date, traffic_source, country, cost, subscribers, ecpa, eps, rps, profit,
        # revenue, roi) values ('4-2-18', 'PopAds', 'United States', '200', '300', '400', '500',' 600', '700', '800',
        # '900');
        #create table push_reports (
        #    id serial primary key,
        #    report_date date not null,
        #    traffic_source varchar(255) not null,
        #    country varchar(255) not null,
        #    cost varchar(255) default 'Unknown',
        #    subscribers varchar(255) default 'Unknown',
        #    ecpa varchar(255) default 'Unknown',
        #    eps varchar(255) default 'Unknown',
        #    rps varchar(255) default 'Unknown',
        #    profit varchar(255) default 'Unknown',
        #    revenue varchar(255) default 'Unknown',
        #    roi varchar(255) default 'Unknown'
        #);

start = datetime(2018, 4, 24)
end = datetime(2018, 4, 24)
for day in arrow.Arrow.range('day', start, end):
	print repr(day)
	from_date_raw = day
	from_date = from_date_raw.format('YYYY-MM-DDT00:00:00') + 'Z'
	to_date_raw = from_date_raw.shift(days=+1)
	to_date = to_date_raw.format('YYYY-MM-DDT00:00:00') + 'Z'
	print(from_date)
	print(to_date)
	build_report(from_date, to_date)
