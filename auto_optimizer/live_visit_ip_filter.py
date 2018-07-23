"""
Watcher module which does the following:
1) Pulls live visit data from Voluum every 3 minutes
2) Filters out IP ranges for carriers by country, connection type, carrier, and time
3) Splits IP ranges into /16 and /24 CIDR configurations
4) Stores in Postgres for further use in MobRevTeam Dashboard 

Voluum
Key Id
ace793ba-7917-4013-86bd-7f888aa0caba
Key
7PMpMgC3kTU4cb3c9cAd3bd48mg-tkrYFgW7
"""

import requests
import psycopg2
import arrow

token_request = requests.post('https://api.voluum.com/auth/access/session', json={"accessId": "ace793ba-7917-4013-86bd-7f888aa0caba", "accessKey":"7PMpMgC3kTU4cb3c9cAd3bd48mg-tkrYFgW7"})
token = str(token_request.json()['token'])
headers = {'content-type': 'application/json', 'cwauth-token': token}
token_validate = requests.get('https://api.voluum.com/auth/session', headers=headers)
campaign_request = requests.get('https://api.voluum.com/campaign', headers=headers)
campaigns = campaign_request.json()["campaigns"]
ip_isp_list = {}

campaign_id = "92788d37-4256-4e1b-aeda-af831b8adf07"
# Reports will be retrieved for current day and go back 7 days
report_from_datetime = str(arrow.utcnow().shift(days=-7).format('YYYY-MM-DD'))# + 'T00' # '2018-03-11T00'
report_to_datetime = str(arrow.utcnow().format('YYYY-MM-DD'))# + 'T00' # '2018-03-18T00'
# Pull report for campaign defined above grouped by campaign + placement
limit=10
reporting_url = 'https://api.voluum.com/report?include=TRAFFIC&columns=campaign,ip&groupBy=ip&filter={}&from={}&to={}&include=ACTIVE&limit={}&sort=visits&direction=DESC'.format(campaign_id, report_from_datetime, report_to_datetime, limit)
report_request = requests.get(reporting_url, headers=headers)
# Grouped by campaign + placement + browser
report_request = requests.get('https://api.voluum.com/report/ip?dateRange=yesterday&sortKey=cost&sortDirection=desc&page=1&chart=0&series=visits,clicks,conversions,revenue,cost,profit,impressions&columns=ip&columns=visits&columns=clicks&columns=conversions&columns=revenue&columns=customConversions1&columns=cost&columns=profit&columns=cpv&columns=ctr&columns=cr&columns=cv&columns=roi&columns=epv&columns=ap&columns=ecpa&filter=&limit=50&reportType=&include=TRAFFIC&reportDataType=0&tagsGrouping=ip&valueFiltersGrouping=ip&from=2018-03-29T00:00:00Z&to=2018-03-30T00:00:00Z&filter1=campaign&filter1Value=92788d37-4256-4e1b-aeda-af831b8adf07', headers=headers)
print(report_request.json())
report_rows = report_request.json()['rows']
for visitor in report_rows:
    print(visitor)
    ip = visitor['ip']
    isp = visitor['isp']
    countryCode = visitor['countryCode']
    connectionType = visitor['connectionType']
    if visitor['mobileCarrier']:
        mobileCarrier = visitor['mobileCarrier']
    else:
        mobileCarrier = 'None'
    browser = visitor['browser']
    ip_isp_list.setdefault(isp, [])
    ip_isp_list[isp].append((ip, countryCode, connectionType, mobileCarrier, browser))

twentyfour_cidr_block = []
sixteen_cidr_block = []
for isp in ip_isp_list.keys():
    for ip in ip_isp_list[isp]:
        ip_address = ip[0]
        country_code = ip[1]
        connection_type = ip[2]
        mobile_carrier = ip[3]
        browser = ip[4]
        split_ip = ip_address.split('.')
        sixteen_cidr_ip = split_ip[0] + '.' + split_ip[1] + '.0.0'
        twentyfour_cidr_ip = split_ip[0] + '.' + split_ip[1] + '.' + split_ip[2] + '.0'
        if sixteen_cidr_ip not in sixteen_cidr_block:
                sixteen_cidr_block.append((sixteen_cidr_ip, country_code, connection_type, mobile_carrier, browser))
        if twentyfour_cidr_ip not in twentyfour_cidr_block:
                twentyfour_cidr_block.append((twentyfour_cidr_ip, country_code, connection_type, mobile_carrier, browser))

print('Establishing database connection...')
conn = psycopg2.connect(                                                                                                                                                                                   
   database="pushengine",
   user="root",         
   password="agdevil1",  
   host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com",  
   port="5432")                                                                                                                                                                                                      
print("Database connection established.")  

for ip_address in sorted(list(set(sixteen_cidr_block))):
    cur = conn.cursor()
    ip = ip_address[0]
    ip_type = "sixteen"
    country_code = ip_address[1]
    connection_type = ip_address[2]
    mobile_carrier = ip_address[3]
    browser = ip_address[4]
    sql = "INSERT into public.ip_address (ip, ip_type, country_code, connection_type, mobile_carrier, browser) values ('{}', '{}', '{}', '{}', '{}', '{}')".format(ip, ip_type, country_code, connection_type, mobile_carrier, browser)
    cur.execute(sql)
    conn.commit()


for ip_address in sorted(list(set(twentyfour_cidr_block))):
    cur = conn.cursor()
    ip = ip_address[0]
    ip_type = "twentyfour"
    country_code = ip_address[1]
    connection_type = ip_address[2]
    mobile_carrier = ip_address[3]
    browser = ip_address[4]
    sql = "INSERT into public.ip_address (ip, ip_type, country_code, connection_type, mobile_carrier, browser) values ('{}', '{}', '{}', '{}', '{}', '{}')".format(ip, ip_type, country_code, connection_type, mobile_carrier, browser)
    cur.execute(sql)
    conn.commit()
