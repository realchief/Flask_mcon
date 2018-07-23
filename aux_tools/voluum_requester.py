"""
VoluumRequester - The Developer Interface to Voluum that should have been
"""

from __future__ import print_function

import csv
import datetime
import json
import os
import logging
from StringIO import StringIO
from collections import defaultdict
import requests
from sqlalchemy import create_engine
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
import re
LOG = logging.getLogger("requests.packages.urllib3")
LOG.setLevel(logging.DEBUG)
LOG.propagate = True


VOLUUM_ACCESS_KEY = os.environ["VOLUUM_ACCESS_KEY"]
VOLUUM_ACCESS_KEY_ID = os.environ["VOLUUM_ACCESS_KEY_ID"]
ZEROPARK_ACCESS_KEY = os.environ["ZEROPARK_ACCESS_KEY"]
POSTGRES_HOST = os.environ["PUSH_DB_HOST"]
POSTGRES_DB = os.environ["PUSH_DB"]
POSTGRES_USERNAME = os.environ["PUSH_DB_USER"]
POSTGRES_PASSWORD = os.environ["PUSH_DB_PASSWD"]

all_campaign_totals = ["advertiserCost", "ap", "bids", "clicks", "conversions", "cost", "cpv", "cr", "ctr", "customConversions1", "customConversions2", "customConversions3", "customConversions4", "customConversions5", "customRevenue1", "customRevenue2", "customRevenue3", "customRevenue4", "customRevenue5", "cv", "ecpa", "ecpc", "ecpm", "epc", "epv", "errors", "ictr", "impressions", "internalBids", "profit", "revenue", "roi", "rpm", "visits", "winRate"]
all_offer_totals = ["advertiserCost", "ap", "clicks", "conversions", "cost", "cpv", "cr", "ctr", "customConversions1", "customConversions2", "customConversions3", "customConversions4", "customConversions5", "customRevenue1", "customRevenue2", "customRevenue3", "customRevenue4", "customRevenue5", "cv", "ecpa", "ecpc", "ecpm", "epc", "epv", "errors", "ictr", "impressions", "profit", "revenue", "roi", "rpm", "visits"]
all_lander_totals = ["advertiserCost","ap","clicks","conversions","cost","cpv","cr","ctr","customConversions1","customConversions2","customConversions3","customConversions4","customConversions5","customRevenue1","customRevenue2","customRevenue3","customRevenue4","customRevenue5","cv","ecpa","ecpc","ecpm","epc","epv","errors","ictr","impressions","profit","revenue","roi","rpm","visits"]
all_campaign_fields = ["actions", "advertiserCost", "ap", "approvalCreationTime", "approvalStatus", "bid", "biddingStatus", "bids", "campaignCountry", "campaignCurrencyCode", "campaignId", "campaignName", "campaignNamePostfix", "campaignType", "campaignUrl", "campaignVisibility", "campaignWorkspaceId", "campaignWorkspaceName", "catApprovalStatus", "changeSources", "clickRedirectType", "clicks", "clientId", "conversions", "cost", "costModel", "cpa", "cpc", "cpm", "cpv", "cr", "created", "createdBy", "ctr", "customConversions1", "customConversions2", "customConversions3", "customConversions4", "customConversions5", "customRevenue1", "customRevenue2", "customRevenue3", "customRevenue4", "customRevenue5", "cv", "dailyBudget", "deleted", "dspCampaignId", "dspCampaignType", "ecpa", "ecpc", "ecpm", "epc", "epv", "errors", "externalCampaignId", "externalCampaignName", "hour", "ictr", "impressions", "internalBids", "isDsp", "isOptimizationEnabled", "name", "pixelUrl", "postbackUrl", "profit", "revenue", "revenueModel", "revision", "roi", "rpm", "status", "statusMessage", "totalBudget", "totalSpend", "trafficSegment", "trafficSourceName", "type", "updated", "updatedBy", "version", "visits", "winRate"]
all_offer_fields = ["actions", "advertiserCost", "ap", "clicks", "conversionCapConversionCount", "conversionCapValue", "conversions", "cost", "cpv", "cr", "created", "ctr", "customConversions1", "customConversions2", "customConversions3", "customConversions4", "customConversions5", "customRevenue1", "customRevenue2", "customRevenue3", "customRevenue4", "customRevenue5", "cv", "deleted", "ecpa", "ecpc", "ecpm", "epc", "epv", "errors", "hour", "ictr", "impressions", "offerCountry", "offerId", "offerName", "offerUrl", "offerWorkspaceId", "offerWorkspaceName", "payout", "profit", "readOnly", "revenue", "roi", "rpm", "updated", "visits"]
all_lander_fields = ["actions", "advertiserCost", "ap", "clicks", "conversions", "cost", "cpv", "cr", "created", "ctr", "customConversions1", "customConversions2", "customConversions3", "customConversions4", "customConversions5", "customRevenue1", "customRevenue2", "customRevenue3", "customRevenue4", "customRevenue5", "cv", "deleted", "ecpa", "ecpc", "ecpm", "epc", "epv", "errors", "hour", "ictr", "impressions", "landerCountry", "landerId", "landerName", "landerUrl", "landerWorkspaceId", "landerWorkspaceName", "numberOfOffers", "profit", "readOnly", "revenue", "roi", "rpm", "updated", "visits"]


class VoluumRequester(object):
    """docstring for VoluumRequester"""
    
    def __init__(self, access_key, access_key_id, start_date=str(datetime.date.today() - datetime.timedelta(1)), end_date=str(datetime.date.today())):
        super(VoluumRequester, self).__init__()
        try:
            self.start_date = start_date
        except ValueError as error:
            LOG.exception('a traffic source is required')
        try:
            self.end_date = end_date
        except ValueError as error:
            LOG.exception('a traffic source is required')
        try:
            self.access_key = access_key
        except ValueError as error:
            LOG.exception('a Voluum acccess_key is required')
        try:
            self.access_key_id = access_key_id
        except ValueError as error:
            LOG.exception('A Voluum access_key_id is required')
        try:
            self.token = self.get_token()
        except ValueError as error:
            LOG.exception('unable to retreive Voluum token')
        self.offset = 0

    def get_token(self):
        """
        Requests a new access token from Voluum as these have an expiration date.
        """
        headers = {"Content-Type": "application/json; charset=utf-8",
                   "Accept": "application/json"}
        data = {"accessId": self.access_key_id,
                "accessKey": self.access_key}
        url = 'https://api.voluum.com/auth/access/session'
        req = requests.post(url, headers=headers, data=json.dumps(data))
        token = str(json.loads(req.content)["token"])
        print("GOT TOKEN! {}".format(token))
        return token

    def get_voluum_report_csv(self):
        """
        Requests data from Voluum, sorting by subs_key and offers. Retreiving
        the subscriber_key, offerName, visits, conversions, revenue, offerId and
        clicks fields.
        """
        headers = {"Content-Type": "application/json; charset=utf-8",
                   # "Accept": "text/csv",
                   "cwauth-token": self.token}

        url = 'https://api.voluum.com/report?from={0}&to={1}{2}&groupBy={3}'.format(
            self.start_date, self.end_date, self.report_columns, self.report_type)
        req = requests.post(url, headers=headers)

        return req.content

    def get_voluum_report_json(self):
        headers = {"Accept": "application/json; charset=utf-8",
                   # "Accept": "text/csv",
                   "cwauth-token": self.token}

        url = 'https://api.voluum.com/report?include=ACTIVE&from={0}&to={1}{2}&groupBy={3}&offset={4}'.format(self.start_date, self.end_date, self.report_columns, self.report_type, self.offset)
        req = requests.get(url, headers=headers)
        print(url)
        return json.loads(req.content)

    def csv_dict_list(self, csv_string, fieldnames):
        """
        Function to convert a csv file to a list of dictionaries.  Takes in two
        variables called "csv_string" and "fieldname"
        """
        csv_file = StringIO(csv_string)

        if fieldnames:
            reader = csv.DictReader(csv_file, delimiter=',', fieldnames=fieldnames)
        else:
            reader = csv.DictReader(csv_file, delimiter=',')

        rows = [row for row in reader]

        # Remove old headers if fieldnames exist
        if fieldnames:
            del rows[0]

        return rows

    def remove_non_traffic_source_dictionaries(self, campaigns_list, traffic_source):
        """
        Remove campaigns unrelated to traffic_source
        """
        try:
            if 'Traffic Source Name' in campaigns_list[0].keys():
                campaigns_list[:] = [d for d in campaigns_list if d.get(
                    'Traffic Source Name').lower() == traffic_source]
            elif 'traffic_source' in campaigns_list[0].keys():
                campaigns_list[:] = [d for d in campaigns_list if d.get(
                    'traffic_source').lower() == traffic_source]
        except Exception as error:
            return json.dumps(
                {"failure": "Parsing dictionary, incorrect keys", "status": 404, "error": error})

        return campaigns_list

    def parse_json_report(self,json_response, requested_totals = None, requested_fields = None):
        # requested_totals = ['conversions', 'advertiserCost', 'customRevenue4']
        # requested_fields = ['trafficSourceName','campaignName', 'campaignId', "campaignCountry", "campaignUrl"]

        if requested_totals == None:
            if self.report_type == 'campaign':
                requested_totals = all_campaign_totals
            elif self.report_type == 'offer':
                requested_totals = all_offer_totals
            elif self.report_type == 'lander':
                requested_totals = all_lander_totals

        if requested_fields == None:
            if self.report_type == 'campaign':
                requested_fields = all_campaign_fields
            elif self.report_type == 'offer':
                requested_fields = all_offer_fields
            elif self.report_type == 'lander':
                requested_fields = all_lander_fields

        # print("REQUESTED TOTALS",requested_totals)
        response = {"totals": {}, str(self.report_type+"s"): []}
        for requested_total in requested_totals:
            response['totals'][requested_total] = json_response['totals'][requested_total]

        for index, item in enumerate(json_response['rows']):
            row_to_insert = dict()
            for requested_field in requested_fields:
                row_to_insert[requested_field] = json_response['rows'][index][requested_field]
            response['campaigns'].append(row_to_insert)
            
        # print(response)
        return response


    def get_traffic_source_campaigns(
            self, traffic_source, report_columns=[], fieldnames=[], requested_totals=[]):
        """
        Retrieve list of campaigns for traffic source
        """
        self.set_report_columns(report_columns)
        self.set_group_by('campaign')
        return self.remove_non_traffic_source_dictionaries(self.csv_dict_list(self.get_voluum_report_csv(), fieldnames), traffic_source)

    def get_all_campaigns(
            self, report_columns=[], fieldnames=[]):
        """
        Retrieve list of all campaigns
        """
        self.set_report_columns(report_columns)
        self.set_group_by('campaign')
        output = {"totals": {}, str(self.report_type+"s"): []}

        not_loaded_all_campaigns = True

        while not_loaded_all_campaigns:
            json_report = self.get_voluum_report_json()
            parsed_json_report = self.parse_json_report(json_report)
            output['totals'] = parsed_json_report['totals']
            try:
                print(parsed_json_report[str(self.report_type+"s")][0]['campaignName'])
            except:
                print("NO MORE ROWS")
            output[str(self.report_type+"s")] += parsed_json_report[str(self.report_type+"s")]
            self.offset += 100
            if len(parsed_json_report[str(self.report_type+"s")]) < 100:
                not_loaded_all_campaigns = False

        counter = 0
        if self.report_type == 'campaign':
            # Associate campaign to category
            categories_list = self.get_categories_from_DB(POSTGRES_USERNAME, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_DB, 'frontend_categories')
            for campaign in output['campaigns']:
                try:
                    uuid_search = re.findall("[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}",campaign['campaignUrl'])
                    expected_category_uuid = uuid_search[0] if len(uuid_search) > 0 else ""

                    campaign["category"] = {"id": None, "name": "Unassigned", "url":None, "uuid":None}
                    for category in categories_list:
                        if category["uuid"] == expected_category_uuid:

                            campaign["category"] = category

                except Exception as error:
                    LOG.info('error getting category url {}'.format(error))


        #GENERATE TOTALS CPA RPS EPS:
        if set(["cost","customConversions1"]).issubset(output['totals'].keys()):
            if output['totals']["customConversions1"] != 0:
                if output['totals']["cost"] == 0:
                    output['totals']['cpa'] = 0
                else:
                    output['totals']['cpa'] = output['totals']['cost']/output['totals']['customConversions1']
            else:
                output['totals']['cpa'] = 0

        if set(["revenue","customConversions1"]).issubset(output['totals'].keys()):
            if output['totals']["customConversions1"] != 0:
                if output['totals']["revenue"] == 0:
                    output['totals']['rps'] = 0
                else:
                    output['totals']['rps'] = output['totals']['revenue']/output['totals']['customConversions1']
            else:
                output['totals']['rps'] = 0

        if set(["profit","customConversions1"]).issubset(output['totals'].keys()):
            if output['totals']["customConversions1"] != 0:
                if output['totals']["profit"] == 0:
                    output['totals']['eps'] = 0
                else:
                    output['totals']['eps'] = output['totals']['profit']/output['totals']['customConversions1']
            else:
                output['totals']['eps'] = 0

        return output

    def get_landers(self, report_columns=[], fieldnames=[]):
        """
        Retrieve list of landers
        """
        self.set_report_columns(report_columns)
        self.set_group_by('lander')
        return self.csv_dict_list(self.get_voluum_report_csv(), fieldnames)

    def get_offers(self, report_columns=[], fieldnames=[]):
        """
        Retrieve list of offers
        """
        self.set_report_columns(report_columns)
        self.set_group_by('offer')
        return self.csv_dict_list(self.get_voluum_report_csv(), fieldnames)

    def set_report_columns(self, report_columns=[], fieldnames=[]):
        """
        Set report columns for class
        """
        try:
            self.report_columns = ""
            for report_column in report_columns:
                self.report_columns += "&columns=" + report_column
        except ValueError as error:
            LOG.exception('report columns must be a list of strings')
            return json.dumps({"failure": "Report columns must be a list of strings", "status": 404, "error": error})

    def set_group_by(self, group_by):
        """
        Set group by for class
        """
        try:
            # self.group_by = "&groupBy=" + group_by
            self.report_type = group_by
        except ValueError as error:
            LOG.exception('a type to group by is required lander/offer/campaign')

    def group_dictionaries_by(self, dictionaries, group_by_field, sub_group_by_field=None):
        d = defaultdict(list)

        if sub_group_by_field:

            for dictionary in dictionaries:
                d[str(dictionary[group_by_field][sub_group_by_field])].append(dictionary)

        else:
            for dictionary in dictionaries:
                if group_by_field == 'campaignCountry' and dictionary[group_by_field] == None:
                    d["Global"].append(dictionary)
                else:
                    d[str(dictionary[group_by_field])].append(dictionary)

        output = dict()
        for item in d.items():
            output[item[0]] = item[1]
        return output

    def get_categories_from_DB(self, username, password, host, db, table):
        try:
            self.username = username
        except ValueError as error:
            LOG.info('username is required')
        try:
            self.password = password
        except ValueError as error:
            LOG.info('password is required')
        try:
            self.host = host
        except ValueError as error:
            LOG.info('host is required')
        try:
            self.db = db
        except ValueError as error:
            LOG.info('database is required')
        try:
            self.table = table
        except ValueError as error:
            LOG.info('table is required')
        try:
            engine = create_engine(
                "postgresql://{0}:{1}@{2}/{3}".format(self.username, self.password, self.host, self.db))
            connection = engine.raw_connection()
            cur = connection.cursor()
        except Exception as error:
            LOG.info('Could not establish connection to the DB')

        #REQUEST CATEGORIES FROM DB:
        cur.execute('SELECT * FROM {};'.format(self.table))
        response_categories = cur.fetchall()

        #CLOSE CONNECTION:
        cur.close()
        connection.close()

        output = []
        #FORMAT INTO DICTIONARY:
        for category in response_categories:

            uuid_search = re.findall("[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}",category[2])
            category_uuid = uuid_search[0] if len(uuid_search) > 0 else ""

            output.append({"id": category[0],"name": str(category[1]), "url": str(category[2]), "uuid": category_uuid})


        return output

    def field_sums(self, dictionaries_list, field_list):

        output_dict = dict()
        for dictionary in dictionaries_list:

            for field in field_list:
                if field not in output_dict.keys():
                    output_dict[field] = 0

                if field in dictionary.keys():
                    if dictionary[field]:
                        output_dict[field] += dictionary[field]

        if set(["cost","customConversions1"]).issubset(output_dict.keys()):
            if output_dict["customConversions1"] != 0:
                if output_dict["cost"] == 0:
                    output_dict['cpa'] = 0
                else:
                    output_dict['cpa'] = output_dict['cost']/output_dict['customConversions1']
            else:
                output_dict['cpa'] = 0

        if set(["revenue","customConversions1"]).issubset(output_dict.keys()):
            if output_dict["customConversions1"] != 0:
                if output_dict["revenue"] == 0:
                    output_dict['rps'] = 0
                else:
                    output_dict['rps'] = output_dict['revenue']/output_dict['customConversions1']
            else:
                output_dict['rps'] = 0

        if set(["profit","customConversions1"]).issubset(output_dict.keys()):
            if output_dict["customConversions1"] != 0:
                if output_dict["profit"] == 0:
                    output_dict['eps'] = 0
                else:
                    output_dict['eps'] = output_dict['profit']/output_dict['customConversions1']
            else:
                output_dict['eps'] = 0


        return output_dict

    def percent_difference_between_dictionaries(self, dict1, dict2):
        output_dict = dict()
        for key in dict1.keys():
            if key in dict2.keys():

                if dict1[key] == 0 and dict2[key] == 0 :
                    output_dict["diff_"+str(key)] = 0
                else:
                    output_dict["diff_"+str(key)] =((dict1[key] - dict2[key])/((dict1[key]+dict2[key])/2.0))*100

        return output_dict


    def format_output(self, unformated_ouput):
        formated_output = []
        item_id = 1
        for key, value in unformated_ouput.iteritems():
            subs = []

            sub_id = 1
            total_churn = 0
            total_rps = 0
            for sub_key in value.keys():

                if sub_key != 'totals':

                    temporary_dict = {"id": sub_id, "title": sub_key, "profit": round(value[sub_key]['profit'], 2), "revenue": round(value[sub_key]['revenue'], 2), "cost": round(value[sub_key]['cost'], 2), "cpa": round(value[sub_key]['cpa'], 2), "customConversions1": value[sub_key]['customConversions1'], "eps": round(value[sub_key]['eps'], 2), "rps": round(value[sub_key]['rps'], 2), "roi": round(value[sub_key]['roi'], 2)}
                    total_rps += value[sub_key]['rps']
                    if "churn" in value[sub_key].keys():
                        total_churn += value[sub_key]['churn']
                        temporary_dict["churn"] = round(value[sub_key]['churn'], 2)
                    subs.append(temporary_dict)
                    sub_id += 1

            temporary_dict = {"id": item_id, "title": key, "profit": round(value['totals']['profit'], 2), "revenue": round(value['totals']['revenue'], 2), "cost": round(value['totals']['cost'], 2), "cpa": round(value['totals']['cpa'], 2), "subs": subs, "subscribers": value['totals']['customConversions1'], "eps": round(value['totals']['eps'], 2), "rps": round(value['totals']['rps'], 2), "roi": round(value['totals']['roi'], 2)}
            if "churn" in value[sub_key].keys():
                # temporary_dict["churn"] = value['totals']['churn']
                temporary_dict["churn"] = round(total_churn, 2)
                temporary_dict['rps'] = round(total_rps, 2)

            formated_output.append(temporary_dict)
            item_id += 1      


        return formated_output

    def keep_keys_in_dict(self, input_dict, keys):
        remove_keys = [ remove_key for remove_key in input_dict.keys() if remove_key not in keys]
        for remove_key in remove_keys:
            input_dict.pop(remove_key, None)
        return input_dict

    def format_totals(self, totals_dict):
        
        output = []
        for key, value in totals_dict.iteritems():
            if key[:5] != 'diff_':

                item_value = (round(totals_dict['diff_'+key],2) if (str('diff_'+key) in totals_dict.keys()) else None)
                output.append({"price": round(value,2), "title": (key.title() if key not in ['roi', "cpa", 'rps', 'eps', 'customConversions1'] else (key.upper() if key != 'customConversions1' else 'Total Subs')), "value": (abs(item_value) if item_value != None else None), "increase": ((True if (item_value > 0) else False) if item_value != None else None)})

        return output

    def get_fcm_churn_from_DB(self, username, password, host, db, *args):
        try:
            self.username = username
        except ValueError as error:
            LOG.info('username is required')
        try:
            self.password = password
        except ValueError as error:
            LOG.info('password is required')
        try:
            self.host = host
        except ValueError as error:
            LOG.info('host is required')
        try:
            self.db = db
        except ValueError as error:
            LOG.info('database is required')
        try:
            engine = create_engine(
                "postgresql://{0}:{1}@{2}/{3}".format(self.username, self.password, self.host, self.db))
            connection = engine.raw_connection()
            cur = connection.cursor()
        except Exception as error:
            LOG.info('Could not establish connection to the DB')

        #REQUEST CATEGORIES FROM DB:
        try:
            if args:
                if len(args) == 1:
                    # SINGLE DATE CHURN
                    cur.execute("select count(*), country, sourcename, date_trunc('hour', date) from fcm_churn where (DATE(date) = '{0}') group by country, sourcename, date_trunc('hour', date) having count(*) > 150 ORDER BY date_trunc DESC NULL LAST;".format(args[0]))
                elif len(args) == 2:
                    try:
                        start_date = (datetime.datetime.strptime(args[0], "%Y-%m-%d") - datetime.timedelta(hours=5)).date()
                        end_date = (datetime.datetime.strptime(args[1], "%Y-%m-%d") - datetime.timedelta(hours=5)).date()
                    except Exception as error:
                        print("THERE WAS AN ERROR:", error)

                    date_span = (end_date - start_date).days + 1

                    date_list = []
                    for i in range(date_span):
                        date_list.append(start_date + datetime.timedelta(i))

                    date_tuple = tuple([ date.strftime('%Y-%m-%d %H:%M:%S') for date in date_list])
                    
                    # MULTI DATE CHURN
                    try:
                        #WITHOUT SOURCE:
                        cur.execute("select count(*), country, sourcename, date_trunc('hour', date) from fcm_churn where (DATE(date) IN {0}) group by country, sourcename, date_trunc('hour', date) having count(*) > 150  ORDER BY date_trunc DESC;".format(date_tuple))
                    except Exception as error:
                        print(error)
            else:
                # ALL CHURN
                cur.execute("select count(*), country, sourcename, date_trunc('hour', date) from fcm_churn group by country, sourcename, date_trunc('hour', date) having count(*) > 150;")
        except Exception as error:
            return {"failure": "reteiving relevant churns", "status": 404, "error": error}


        response_churns = cur.fetchall()

        #CLOSE CONNECTION:
        cur.close()
        connection.close()

        output = []
        #FORMAT INTO DICTIONARY:
        for churn in response_churns:

            output.append({"count": int(churn[0]),"country": str(churn[1]), "sourcename": str(churn[2]), "date_trunc": churn[3].strftime('%Y-%m-%d %H:%M:%S')})          

        output_total = self.field_sums(output, ['count'])
        output = self.group_dictionaries_by(output, 'country')

        try:
            if output['US']:
                if output['United States']:
                    output['United States'] += output['US']
                    output.pop('US', None)
        except:
            pass

        for key, value in output.iteritems():
            temporary_dict = self.field_sums(value, ['count']) 
            temporary_dict['date'] = value[0]['date_trunc']
            output[key] = self.group_dictionaries_by(value, 'sourcename')

        for key, value in output.iteritems():

            for sub_key, sub_value in output[key].iteritems():
                output[key][sub_key] = self.field_sums(sub_value, ['count'])
                output[key][sub_key]['date'] = sub_value[0]['date_trunc']

        # output[key]['total'] = temporary_dict

        output['total'] = output_total

        return output

    def prepare_overview_report(self):

        voluum_all_campaigns = self.get_all_campaigns(["profit", "revenue", "cost", "roi", "cpa", "customConversions1"], ["profit", "revenue", "cost", "roi", "ecpa", "customConversions1"])


        self.keep_keys_in_dict(voluum_all_campaigns['totals'],["profit", "revenue", "cost", "roi", "cpa", "customConversions1", 'rps', 'eps'])

        #REQUEST FCM_CHURN:
        try:
            start_date = datetime.datetime.strptime(self.start_date, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(self.end_date, "%Y-%m-%d").date()
        except Exception as error:
            print("THERE WAS AN ERROR:", error)

        date_span = (end_date - start_date).days + 1

        previous_start_date = (start_date - datetime.timedelta(date_span)).strftime('%Y-%m-%d')
        period_churns = self.get_fcm_churn_from_DB(POSTGRES_USERNAME, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_DB, self.start_date, self.end_date)

        #REQUEST PREVIOUS PERIOD CHURN:
        previous_period_churns = self.get_fcm_churn_from_DB(POSTGRES_USERNAME, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_DB, previous_start_date, self.start_date)

        grouped_by_campaignCountry = self.group_dictionaries_by(voluum_all_campaigns[str(self.report_type)+"s"], 'campaignCountry')

        ########################################
        # COUNTRY > CATEGORIES
        ########################################
      
        grouped_by_campaignCountry_by_category = grouped_by_campaignCountry.copy()

        temporary_dict = dict()
        for key, value in grouped_by_campaignCountry_by_category.iteritems():
            grouped_by_campaignCountry_by_category[key] = self.group_dictionaries_by(value, 'category', 'name')
            temporary_dict[key] = self.field_sums(value, ["profit", "revenue", "cost", "roi", "cpa", "customConversions1"])

        for key, value in grouped_by_campaignCountry_by_category.iteritems():
            for sub_key, sub_value in value.iteritems():
                grouped_by_campaignCountry_by_category[key][sub_key] = self.field_sums(sub_value, ["profit", "revenue", "cost", "roi", "cpa", "customConversions1"])

        for key in grouped_by_campaignCountry_by_category.keys():
            grouped_by_campaignCountry_by_category[key]['totals'] = temporary_dict[key]

        ########################################
        # COUNTRY > SOURCE
        ########################################
        grouped_by_campaignCountry_by_source = grouped_by_campaignCountry.copy()

        temporary_dict = dict()
        for key, value in grouped_by_campaignCountry_by_source.iteritems():
            grouped_by_campaignCountry_by_source[key] = self.group_dictionaries_by(value, 'trafficSourceName')
            temporary_dict[key] = self.field_sums(value, ["profit", "revenue", "cost", "roi", "cpa", "customConversions1"])

        for key, value in grouped_by_campaignCountry_by_source.iteritems():      
            for sub_key, sub_value in value.iteritems():
                grouped_by_campaignCountry_by_source[key][sub_key] = self.field_sums(sub_value, ["profit", "revenue", "cost", "roi", "cpa", "customConversions1"])
                try:
                    calculated_churn = ((period_churns[key][sub_key]['count'] - previous_period_churns[key][sub_key]['count'])/((period_churns[key][sub_key]['count']+previous_period_churns[key][sub_key]['count'])/2.0))*100
                except Exception as error:
                    print("error calculating churn  within country {} source {}".format(key, sub_key), error)
                    calculated_churn = 0

                grouped_by_campaignCountry_by_source[key][sub_key]['churn'] = calculated_churn

        for key in grouped_by_campaignCountry_by_category.keys():
            grouped_by_campaignCountry_by_source[key]['totals'] = temporary_dict[key]
            try:
                calculated_churn = ((period_churns[key]['total']['count'] - previous_period_churns[key]['total']['count'])/((period_churns[key]['total']['count']+previous_period_churns[key]['total']['count'])/2.0))*100
            except Exception as error:
                print("***** THERE WAS AN ERROR", error)
                calculated_churn = 0
            grouped_by_campaignCountry_by_source[key]['totals']['churn'] = calculated_churn

        ########################################
        # CATEGORIES > COUNTRY
        ########################################
        grouped_by_category = self.group_dictionaries_by(voluum_all_campaigns[str(self.report_type)+"s"], 'category', 'name')

        grouped_by_category_by_campaignCountry = grouped_by_category.copy()

        temporary_dict = dict()
        for key, value in grouped_by_category_by_campaignCountry.iteritems():
            grouped_by_category_by_campaignCountry[key] = self.group_dictionaries_by(value, 'campaignCountry')
            temporary_dict[key] = self.field_sums(value, ["profit", "revenue", "cost", "roi", "cpa", "customConversions1"])

        for key, value in grouped_by_category_by_campaignCountry.iteritems():

            for sub_key, sub_value in value.iteritems():
                grouped_by_category_by_campaignCountry[key][sub_key] = self.field_sums(sub_value, ["profit", "revenue", "cost", "roi", "cpa", "customConversions1"])

        for key in grouped_by_category_by_campaignCountry.keys():
            grouped_by_category_by_campaignCountry[key]['totals'] = temporary_dict[key]

        ##########################################
        # CALCULATE TOTALS VARIANCE:
        ##########################################

        self.end_date = self.start_date
        datetime_start_date = datetime.datetime.strptime(self.start_date, '%Y-%m-%d').date()
        self.start_date = str(datetime_start_date - datetime.timedelta(1))

        past_voluum_all_campaigns = self.get_all_campaigns(["profit", "revenue", "cost", "roi", "cpa", "customConversions1"], ["profit", "revenue", "cost", "roi", "ecpa", "customConversions1"])
        totals_percent_diff = self.percent_difference_between_dictionaries(voluum_all_campaigns['totals'], past_voluum_all_campaigns['totals'])
        voluum_all_campaigns['totals'].update(totals_percent_diff)

        try:
            calculated_churn = ((period_churns['total']['count'] - previous_period_churns['total']['count'])/((period_churns['total']['count']+previous_period_churns['total']['count'])/2.0))*100
        except Exception as error:
            print("***** THERE WAS AN ERROR", error)
            calculated_churn = 0


        num_of_campaigns = len(voluum_all_campaigns['campaigns'])

        voluum_all_campaigns['totals']['diff_churn'] = calculated_churn
        if 'count' in period_churns['total'].keys():
            voluum_all_campaigns['totals']['churn'] = (period_churns['total']['count']/num_of_campaigns) if (num_of_campaigns != 0) else 0
            voluum_all_campaigns['totals']['present churn'] = period_churns['total']['count']
        voluum_all_campaigns['totals'] = self.format_totals(voluum_all_campaigns['totals'])


        return {"totals": voluum_all_campaigns['totals'], "country_category": self.format_output(grouped_by_campaignCountry_by_category), "country_source": self.format_output(grouped_by_campaignCountry_by_source), "category_country": self.format_output(grouped_by_category_by_campaignCountry), "num_of_campaigns": num_of_campaigns}#


if __name__ == '__main__':

    VC = VoluumRequester(VOLUUM_ACCESS_KEY, VOLUUM_ACCESS_KEY_ID)
    # VC = VoluumRequester(VOLUUM_ACCESS_KEY, VOLUUM_ACCESS_KEY_ID, '2018-04-01')
    # VC = VoluumRequester(
    #     VOLUUM_ACCESS_KEY,
    #     VOLUUM_ACCESS_KEY_ID,
    #     '2018-06-29',
    #     '2018-07-02')
    # print(VC.get_traffic_source_campaigns('zeropark', ['trafficSourceName','campaignName', 'campaignId'], ['traffic_source', 'name', 'id']))
    # print(VC.get_landers(['landerId', 'landerName', 'landerUrl']))
    # print(VC.get_landers(['landerId', 'landerName', 'landerUrl'], ['lander_id', 'lander_name', 'lander_url']))

    # print(VC.get_offers(['offerId','offerName', 'offerUrl']))
    # print(VC.get_traffic_source_campaigns('zeropark', ['trafficSourceName','campaignName', 'campaignId']))





    # # print("")
    # # print(grouped_by_campaignCountry_by_category)
    # # print(VC.group_dictionaries_by(response[str(VC.report_type)+"s"], 'campaignUrl'))
    # # print(len(VC.group_dictionaries_by(response[str(VC.report_type)+"s"], 'campaignId').keys()))
    
# 

    print("************************************************************")
    print(json.dumps(VC.prepare_overview_report()))
    # all_camps =VC.get_all_campaigns()
    
    # for index, row in enumerate(all_camps['campaigns']):
    #     all_camps['campaigns'][index] = VC.keep_keys_in_dict(row, ['trafficSourceName','campaignName', 'campaignId', "campaignCountry", "campaignUrl"])

    # print(json.dumps(all_camps))