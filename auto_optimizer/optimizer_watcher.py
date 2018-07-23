"""
Watcher module which does the following:
1) Pulls live visit data from Voluum every minute
2) Filters out placement for defined traffic sources to determine traffic composition
3) Pauses placements with unacceptable levels of incompatible traffic for push campaigns

Voluum
Key Id
ace793ba-7917-4013-86bd-7f888aa0caba
Key
7PMpMgC3kTU4cb3c9cAd3bd48mg-tkrYFgW7

ZeroPark api_key
AAABYk/TSanlykVoTFAznLqnNPiCJnQMM7d67kGhGJr6pIoO8YK6LizPSBh/KKWjyjg4rf5Vb7iDpOxldTIkaQ==

Test Campaign:
Zeropark - Turkey - Push Subs
ID: e029accf-d45c-4895-8d48-8c75fd58010f
External Name: P : Turkey
External ID: cf293c30-0006-11e8-b806-0ec5f5cbb90a (edited)
"""
from __future__ import print_function

import arrow
import psycopg2
import requests
import logging
from requests_toolbelt.utils import dump

# Instantiate logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler
handler = logging.FileHandler('/home/ubuntu/auto_optimizer/auto_optimizer.log')
handler.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(handler)

try:
    logger.info('Beginning auto optimization')
    logger.info('Establishing database connection...')
    conn = psycopg2.connect(
        database="pushengine",
        user="root",
        password="VK%Gu?kNdlS{",
        host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com",
        port="5432")
    logger.info('Connection established.')
except:
    logger.exception('Could not connect to postgres')

try:
    # Connect to DB and fetch all campaign rules
    cur = conn.cursor()
    sql = "select * from public.campaign_rule;"
    cur.execute(sql)
    campaign_rules = cur.fetchall()
    logger.info('Rows fetched')
    logger.info(campaign_rules)
except:
    logger.exception('Could not retrieve campaign rules')

def validate_session():
    try:
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
        return headers
    except:
        logger.exception('Could not validate session')

# Define rule variables for each run
for row in campaign_rules:
    headers = validate_session()
    logger.info('Checking campaign rule:' + str(row[0]))
    campaign_id = row[1]
    y_metric_gtlt = row[2]
    y_metric = row[3]
    y_metric_amount = row[4]
    x_metric = row[5]
    x_metric_amount = row[6]
    x_metric_gtlt = row[7]
    # Reports will be retrieved for current day and go back 7 days
    report_from_datetime = str(arrow.utcnow().shift(
        days=-7).format('YYYY-MM-DD')) + 'T00'  # '2018-03-11T00'
    report_to_datetime = str(arrow.utcnow().format(
        'YYYY-MM-DD')) + 'T00'  # '2018-03-18T00'
    # Pull report for campaign defined above grouped by campaign + placement
    limit = 200
    try:
        report_request = requests.get('https://api.voluum.com/report?include=TRAFFIC&columns=campaign&filter={}&=groupBy=campaign,customVariable1&from={}&to={}&include=ACTIVE&limit={}&sort=visits&direction=DESC'.format(campaign_id,
                report_from_datetime,
                report_to_datetime,
                limit),
            headers=headers)
        report_rows = report_request.json()['rows']
    except:
        logger.exception('Could not retrieve report rows')
    percent_chrome = 65
    placement_list = {}
    logger.info('Printing report rows...')
    logger.info(report_rows)
    if len(report_rows) > 0:
        for row in report_rows:
            try:
                # logger.info(row)
                placement = row['customVariable1']
                # browser = row['browser']
                visits = row['visits']
                cost = row['cost']
                conversions = row['conversions']  # Num Conversions
                cv = row['cv']  # Conversion Rate
                ctr = row['ctr']  # Clickthrough Rate
                ecpa = row['ecpa']  # Cost per Subscriber
                external_campaign_id = row['externalCampaignId']
                placement_list.setdefault(placement, [])
                placement_list[placement].append(
                    (visits, cost, cv, conversions, ctr, ecpa, external_campaign_id))
            except:
                logger.exception('Could not retrieve report row')
    logger.info('Printing placement list...')
    logger.info(placement_list)
    report_request = requests.get('https://api.voluum.com/report?from={}&to={}&tz=America%2FChicago&sort=visits&direction=desc&columns=campaignName&columns=campaignId&columns=externalCampaignId&groupBy=campaign&offset=0&limit=1000&include=TRAFFIC&conversionTimeMode=VISIT'.format(
    report_from_datetime,
    report_to_datetime),
    headers=headers)
    campaign_hash_map = {}
    for campaign in report_request.json()['rows']:
        if 'Zeropark' in campaign['trafficSourceName']:
                campaign_hash_map[campaign['campaignId']] = campaign['externalCampaignId']
    cut_placements = []
    logger.info(x_metric)
    for placement in placement_list:
        try:
            logger.info('Placement:')
            logger.info(placement)
            logger.info('Placement List Entry:')
            logger.info(placement_list[placement])
            logger.info('Analyzing placement:')
            # Initialize statuses as false and then set active if metrics met
            y_metric_status = False
            x_metric_status = False
            # Define x_metric
            if 'visits' in x_metric:
                placement_x = placement_list[placement][0][0]
            if 'spend' in x_metric:
                placement_x = placement_list[placement][0][1]
            # Check for gt or lt
            if 'gt' in x_metric_gtlt:
                if float(placement_x) > float(x_metric_amount):
                    x_metric_status = True
            if 'lt' in x_metric_gtlt:
                if float(placement_x) < float(x_metric_amount):
                    x_metric_status = True
            logger.info('X Metric Status: ')
            logger.info(x_metric_status)
            logger.info(x_metric_gtlt)
            logger.info(placement_x)
            logger.info(x_metric_amount)
            # Define y_metric
            if 'cv' in y_metric:
                placement_y = placement_list[placement][0][2]
            if 'conversions' in y_metric:
                placement_y = placement_list[placement][0][3]
            if 'ctr' in y_metric:
                placement_y = placement_list[placement][0][4]
            if 'ecpa' in y_metric:
                placement_y = placement_list[placement][0][5]
            # Check for gt or lt 
            if 'gt' in y_metric_gtlt:
                if placement_y > y_metric_amount:
                    y_metric_status = True
            if 'lt' in y_metric_gtlt:
                if placement_y < y_metric_amount:
                    y_metric_status = True
            logger.info('Y Metric Status: ')
            logger.info(y_metric_status)
            if y_metric_status and x_metric_status:
                cut_placements.append(placement)
        except:
            logger.exception('Could not analyze placement')
    logger.info('Placements to Pause: ')
    logger.info(len(cut_placements))
    logger.info(cut_placements)
    for placement in cut_placements:
        try:
            targetHash = placement
            # Substitute the internal campaign id for the external campaign_id)
            logger.info(campaign_hash_map[campaign_id])
            logger.info(targetHash)
            request_url = 'https://panel.zeropark.com/api/campaign/{}/target/pause?hash={}'.format(
                            campaign_hash_map[campaign_id], targetHash)
            headers = {'content-type': 'application/json',
                       'api-token': 'AAABYo8wtsK9tCSyJBTmtXg0zqdDIEBF32JSLGFhZOwvibVLbfW39UCsQMo1TZpJVcDauRPraOyxhDPUktqTTw=='}
            response = requests.post(request_url, headers=headers)
            #data = dump.dump_all(response)
            #logger.info(data.decode('utf-8'))
            logger.info(response.status_code)
            logger.info(response.text)
        except:
            logger.exception('Could not pause placement')

