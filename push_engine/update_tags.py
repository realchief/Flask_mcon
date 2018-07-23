#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coding: utf8
"""
update_tags.py

This will check each app for the subscriber and update if found, but will result in failures
equal to the number of app_ids - 1 (whichever one actually contains the user key).

Example:
Update tags for 700 users across 11 apps.
This will result in 7700 requests (# users * # apps).
7,000 of which will fail and 700 of which will succeed.

There's a limit of roughly 15 API requests per second but
lacking information on whether this is account-specific or app-specific.
`
Assuming it is account-specific that 7,700 requests will take 8.5 minutes to complete.

A smarter approach would be using the app_id if available,
or searching the DB for the subscriber key first to retrieve
the associated app_id (but users are not currently being updated in postgres,
so this would first necessitate a bulk export of users from OneSignal,
and modification to the landers to trigger adding new users
to postgres on successful subscription).

By cutting down on failing requests, only 700 requests would be made, taking roughly 0.7 minutes to complete.
"""

__author__ = 'MCON, LC (dmchale@mchaleconsulting.net)'
__copyright__ = 'Copyright (c) 2018 MCON, LC'
__license__ = 'New-style BSD'
__vcs_id__ = '$Id$'
__version__ = '1.0.0'  # Versioning: http://www.python.org/dev/peps/pep-0386/

import cStringIO
import datetime
import gzip
import json
import logging
import math
import os
import re
import sys
import time

import arrow
import multiprocess as mp
import numpy as np
import pandas as pd
import psycopg2
import requests
import sqlalchemy
from sqlalchemy import create_engine
sys.path.insert(0, '../aux_tools')
from multiprocess_tool import MultiprocessTool


if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


# Instantiate logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler
handler = logging.FileHandler('/home/ubuntu/push_engine/update_tags.log')
# handler = logging.FileHandler('./update_tags.log')
handler.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(handler)

app_ids = {"cb48c5f8-083e-4893-a330-2162ec73ce73":
           "MTc4NGE3MzItZjZkMC00NjczLWE3NzAtZWYxYjFlM2Q2MDFj",
           "26d0af0e-1eb1-4773-8df5-172b2382bccb":
           "ZGU2ZDc1OTUtOTg0Ni00MTY3LWExNjUtMmVkMzMxNDhkMjE1L",
           "0dd61234-7d87-4955-93e6-ac0c060934d1":
           "ODljNTVkZjEtOGFjOS00MTlkLTg0OGMtN2FkNGExODllZjE5L",
           "d6ad3116-9a9e-4b08-a986-a68a0a094086":
           "ODZkM2FmZGYtOWJmNi00N2ZiLThjMjYtODdiNmExNjYyMTgzL",
           "12a15cae-3ffd-4265-97e2-99ebd07a7472":
           "ZjQ5MmE3MzMtODBlNi00MjU4LTkzMmQtZjkwYzM0MmIyNjM4L",
           "48075596-a4e5-4b88-8a27-982cc4eca9a2":
           "OWQ4YmJiMWUtMTRhMS00ZDA1LTljYTQtMWRhOTY5ZjNiMGE3",
           "49db6ad5-8436-4fd6-b73d-d8b666c22865":
           "ZWMxMGI5MDAtMTQ0Ni00YjVlLTg4MzAtZGNlZThmZmYwYjg3",
           "106617c9-9423-4995-934e-29798ebcf78d":
           "YjcxOTg0ZWItOTVhYy00NzQyLTkxY2ItNGVmMzU4NmRmYmM5",
           "668921bd-2b70-4db4-86c4-3e067af25e4f":
           "NzM1MjlkNDItZWI3Zi00NWQwLTgwNTgtYjE0YjEyMTc2ZTI1",
           "6912f8ce-4d8f-462d-9302-4e9bff2b8cbf":
           "MDAwYTM1MjktOWQ3Mi00YTRjLWI2OGYtZDc2YmU5NmE5MmQ5",
           "6959f653-b568-42a8-bd0f-9026db57a8a0":
           "MDgzMWVhYTQtMjkxZC00YjgyLWJjZTAtYmJhZmQ4M2ZhMjlj",
           "7b114ee5-5e4e-41b5-a93d-db3853e14492":
           "M2I1ZGI5ZGYtY2U3NS00NjE1LWJhYjYtYjI2YTNhY2NhNmRk",
           "a39dd205-5d83-4a36-9ebc-f7422a734706":
           "ODRhMzhiMjUtYTY1ZC00YWQwLTkzMTctNDc1NmNjNjkxYmFi",
           "204b05c1-ab69-4005-928c-924f9b0fe31a":
           "MjI4YWVlNWQtODU1Zi00MzU3LWEwNGEtYjJjYTIzYmU1MTMx",
           "6deb6b65-1e54-4649-8da4-3514e9d300a7":
           "ZmFlYTgzYzktZDZmMC00NjkyLTk1YTYtNzliM2U5NGY3NTQw",
           "c52616a4-3e72-4396-a00b-3396523539c4":
           "MmY1NDJmMjEtZTk2OS00MjhhLWE0YzEtYTVkZWZiMDE2NmY0",
           "650bceb6-cb6d-4b92-8a03-25d6c224efb1":
           "MDZiMWVkNWItNzNkZC00ODY4LWJkZTMtNWViYTk0ZWE1NTA0",
           "64474374-1bbb-4203-9384-3e549de62399":
           "ODUzN2ViMTQtNGI5OS00YTY5LWExNmEtNTlhZGRlYjY3ZjM4"
           }


# Custom error to handle API connection issues
class MyAppLookupError(LookupError):
    '''raise this when there's a lookup error for my app'''

# Custom Error that denotes that the retryer decorator has maxed out retries.


class RetryError(RuntimeError):
    pass

# Retryer decorator, to handle functions that can be retried after falure.
# 2 parameters can be passed max_retries and timeout (in seconds)


def retryer(max_retries=10, timeout=5):
    def wraps(func):
        request_exceptions = (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            AttributeError,
            MyAppLookupError,
            mp.TimeoutError,
            Exception
        )

        def inner(*args, **kwargs):
            for i in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                except request_exceptions:
                    print("***********************")
                    print("Function failing:")
                    print(func.__name__)
                    print("exception raised, going to sleep")
                    print("failing at attempt {}".format(i + 1))
                    time.sleep(timeout * i)
                    continue
                else:
                    return result
            else:
                print("FALURE WITH:")
                print(func.__name__)
                print("failing at:")
                raise RetryError
        return inner
    return wraps


class UpdateOneSignalUsers(object):

    """UpdateOneSignalUsers iterates through a dictionary of app_ids and rest_authorization, polling OneSignalUsers for relevant data.
    Prossesing said data as appropreate to save on the onesignal_users postgres table. Doing so by parsing the tags returned from OneSignal,
    And removing irrelevand data."""

    def __init__(self, app_ids, username, password,
                 host, db, table, chunksize=1500):
        super(UpdateOneSignalUsers, self).__init__()
        try:
            self.app_ids = app_ids
        except ValueError as error:
            logger.info('app_ids dictionary is required')
        try:
            self.username = username
        except ValueError as error:
            logger.info('username is required')
        try:
            self.password = password
        except ValueError as error:
            logger.info('password is required')
        try:
            self.host = host
        except ValueError as error:
            logger.info('host is required')
        try:
            self.db = db
        except ValueError as error:
            logger.info('database is required')
        try:
            self.table = table
        except ValueError as error:
            logger.info('table is required')
        try:
            self.chunksize = chunksize
        except ValueError as error:
            logger.info('chunksize is required')

    # Retrieves the url to download onesignal app data
    @retryer(max_retries=20, timeout=10)
    def get_download_url(self, onesignal_app_id, rest_authorization):
        rest_authorization = "Basic {}".format(rest_authorization)
        headers = {"Content-Type": "application/json; charset=utf-8",
                   "Authorization": rest_authorization}
        data = {}
        params = {}
        url = "https://onesignal.com/api/v1/players/csv_export?app_id={}".format(
            onesignal_app_id)
        logger.info('Header:')
        logger.info(headers)
        logger.info('Endpoint:')
        logger.info(url)

        print(url)
        try:
            req = requests.post(url, params=params, data=data, headers=headers)
            if req.status_code == 200:
                print("good request")
                return req
            elif req.status_code == 400:
                print(req.content)
                raise MyAppLookupError(
                    'App id and/or rest authorization are incorrect')
            else:
                raise MyAppLookupError('SOMETHING WENT TERRIBLY WRONG')

        except Exception as error:
            logger.info(
                "There was an error obtaining the download url {}".format(error))

    # Downloads data from the onesignal app data url, and saves it with a
    # timestampped  filename. and outputs the filename for later use.
    @retryer(max_retries=20, timeout=10)
    def download_file(self, url):

        r = requests.models.Response
        # r.status_code = 400

        # counter = 1
        # while r.status_code != 200 and counter <= 90:
        #   print("ON TRY {}".format(counter))
        #   r = requests.get(url)
        #   time.sleep(10)
        #   counter += 1

        r = requests.get(url)

        if r.status_code != 200:
            print(
                "Warning, getting status code: {}, going to try again".format(
                    r.status_code))
            raise MyAppLookupError('Unable to download OneSignal data')

        utc = arrow.utcnow()
        local_time = utc.to('US/Pacific').format('YYYY-MM-DD_HH-mm-ss_ZZ')
        output_filename = local_time + "-download.csv.gz"

        with open(output_filename, "wb") as code:
            code.write(r.content)
            print("Download Complete!")
        return output_filename

    # Reads downloaded gzip file and outputs a Pandas dataframe.
    def read_gzip(self, filename):

        inF = gzip.open(filename, 'rb')
        reader = pd.read_csv(inF, chunksize=self.chunksize)
        return reader

    # Processes a Pandas data frame recieved from onesignal and subsequently
    # unzipped. Takes 2 arguments the dataframe to parse as well as the
    # onesignal app id passed down from the app_ids dictionary. This process
    # is run by the MultiProcessTool, hence recieves the app_id as a *args.
    @retryer(max_retries=3, timeout=5)
    def process_frame(self, df, app_id_arg):

        app_id = app_id_arg[0]

        df.rename(columns={'id': 'subscriber'}, inplace=True)
        df['is_active'] = df['invalid_identifier'].apply(
            self.t_and_f_to_boolean)
        df['id'] = df.index

        try:
            df = df.drop('ip', 1)
        except:
            pass

        # White list accepted tag keys
        accepted_tag_keys = [
            "sourcename_key",
            "subscriber_key",
            "ip_key",
            "os_key",
            "isp_key",
            "city_key",
            "brand_key",
            "model_key",
            "device_key",
            "region_key",
            "browser_key",
            "carrier_key",
            "osversion_key",
            "browserversion_key"]

        # White list accepted outputted columns:
        accepted_columns = [
            "id",
            "created_at",
            "updated_at",
            "player_id",
            "is_active",
            "thumbnail",
            "name",
            "image",
            "badge",
            "num_user_sent",
            "identifier",
            "session_count",
            "language",
            "sourcename",
            "subscriber",
            "ip",
            "os",
            "isp",
            "city",
            "brand",
            "model",
            "device",
            "region",
            "browser",
            "carrier",
            "osversion",
            "browserversion",
            "country",
            "timezone",
            "onesignal_created_at",
            "additional_tags",
            "last_active"]

        # Processes the tags field provieded in the inputted dataframe. The tag
        # field is a stringified JSON, hence it is delt with accordingly.
        total_tags = pd.DataFrame()

        # Iterates through each row of dataframe.
        for index, row in df.iterrows():
            try:
                # print('flag4')
                # Reads "tags" field parses its JSON content and converts all
                # keys from unicode to string.
                tags = {str(k): v for k, v in json.loads(row['tags']).items()}
                # Creates dataframe from tags json.
                row_json_df = pd.io.json.json_normalize(tags)

                # If subscriber not in tags, the rows subscriber is used.
                if "subscriber_key" not in row_json_df:
                    row_json_df["subscriber_key"] = row["subscriber"]

                # Creates json of non whitelisted tag keys and saves them in an
                # "addition_tags" column of the json dataframe
                additional_tags = dict(tags)
                for key in accepted_tag_keys:
                    if key in additional_tags:
                        del additional_tags[key]
                row_json_df["additional_tags"] = str(additional_tags)
                if row_json_df["subscriber_key"].iloc[0] == row["subscriber"]:
                    total_tags = pd.concat([total_tags, row_json_df])
                else:
                    pass
                # print('flag5')
            except:
                total_tags = pd.concat([total_tags, pd.DataFrame()])

        # Removes "_key" suffix from concatenated json dataframes.
        total_tags = total_tags.rename(columns=lambda x: re.sub('_key', '', x))

        # Merges concatenated json dataframes with initial inputted dataframe,
        # as "parsed_df".
        try:
            parsed_df = pd.merge(
                df,
                total_tags,
                on='subscriber',
                how='left',
                suffixes=(
                    '',
                    '_from_tags'))
        except:
            parsed_df = df

        # Remove duplicate rows (NOT NECESSARY)
        # parsed_df.drop_duplicates(subset=['subscriber'], keep='last', inplace=True)

        # Purges parsed_df of all non whitelisted outputted columns.
        for col_name in list(parsed_df):
            if col_name not in accepted_columns:
                parsed_df = parsed_df.drop(col_name, 1)

        # Passes in current datetime and onesignal app id to parsed_df
        parsed_df.rename(
            columns={
                'created_at': 'onesignal_created_at'},
            inplace=True)
        parsed_df["player_id"] = app_id
        parsed_df["created_at"] = str(datetime.datetime.today())

        # Drop all blank or NaN subscribers
        parsed_df['subscriber'].replace('', np.nan, inplace=True)
        parsed_df.dropna(subset=['subscriber'], inplace=True)

        for col_name in list(set(accepted_columns) - set(list(parsed_df))):
            parsed_df[col_name] = None

        # REORDER SO THAT COLUMNS ARE IN SAME ORDER AS POSTGRES TABLE:
        try:
            parsed_df = parsed_df[accepted_columns]
        except Exception as error:
            logger.info(
                'Error reordering columns to Postgres format {}'.format(error))

        return parsed_df

    # save_to_postgres, saves chunk of dataframe to postgres. This function is
    # run by the MultiprocessTool, hence the inputted data must be a chunk of
    # the total data to save, as well as having it's own postgres engine.
    @retryer(max_retries=3, timeout=5)
    def save_to_postgres(self, dataframe):
        global global_last_id
        global lock
        # REORDER SO THAT COLUMNS ARE IN SAME ORDER AS POSTGRES TABLE:
        try:
            dataframe = dataframe[["id",
                                   "created_at",
                                   "updated_at",
                                   "player_id",
                                   "is_active",
                                   "thumbnail",
                                   "name",
                                   "image",
                                   "badge",
                                   "num_user_sent",
                                   "identifier",
                                   "session_count",
                                   "language",
                                   "sourcename",
                                   "subscriber",
                                   "ip",
                                   "os",
                                   "isp",
                                   "city",
                                   "brand",
                                   "model",
                                   "device",
                                   "region",
                                   "browser",
                                   "carrier",
                                   "osversion",
                                   "browserversion",
                                   "country",
                                   "timezone",
                                   "onesignal_created_at",
                                   "additional_tags",
                                   "last_active"]]
        except Exception as error:
            logger.info(
                'Error reordering columns to Postgres format {}'.format(error))

        engine = create_engine(
            "postgresql://{0}:{1}@{2}/{3}".format(self.username, self.password, self.host, self.db))
        connection = engine.raw_connection()
        cur = connection.cursor()

        # check if there are subscribers to update.
        # get all subscribers from inputted dataframe

        dataframe_subscribers = tuple(dataframe["subscriber"])

        if len(dataframe_subscribers) > 0:
            try:

                # query subscribers, ids and created_ats
                cur.execute('SELECT id, subscriber, created_at FROM onesignal_users WHERE subscriber IN {};'.format(
                    dataframe_subscribers))

                # connection.commit()
                ids_subs_created_at_query_response = cur.fetchall()

                if ids_subs_created_at_query_response:

                    # Split 2 dimensional tuple into 3 separate tuples
                    ids, subs, created_ats = zip(
                        *ids_subs_created_at_query_response)

                    update_dataframe = dataframe[
                        dataframe['subscriber'].isin(subs)]
                    insert_dataframe = dataframe[
                        ~dataframe['subscriber'].isin(subs)]

                    # Format update_dataframe
                    update_dataframe.loc[
                        :, 'updated_at'] = update_dataframe['created_at']

                    for idx, sub in enumerate(subs):
                        update_dataframe.loc[
                            update_dataframe.subscriber == sub, [
                                'created_at', 'id']] = [
                            created_ats[idx], ids[idx]]

                    dataframe = pd.concat([insert_dataframe, update_dataframe])

                    # cur.execute('SELECT count(*) FROM onesignal_users;')
                    # print(cur.fetchone())
                    cur.execute(
                        'DELETE FROM onesignal_users WHERE id IN {}'.format(ids))
                    # print(ids)
                    # connection.commit()
                    # cur.execute('SELECT count(*) FROM onesignal_users;')
                    # print(cur.fetchone())

                else:
                    update_dataframe = pd.DataFrame()
                    insert_dataframe = dataframe.copy()

            except Exception as error:
                logger.info(
                    'AN ERROR SELECTION IDS, SUBSCRIBERS AND CREATED_AT {}'.format(error))

        # print("UPDATE DATA", update_dataframe.shape)
        # print("INSERT DATA",insert_dataframe.shape)
        lock.acquire()

        cur.execute('SELECT MAX(id) FROM onesignal_users;')
        last_onesignal_users_id = cur.fetchone()[0]
        # print("global last value id",global_last_id.value)
        # print("last onesignal users id",last_onesignal_users_id)

        if last_onesignal_users_id is None:
            last_onesignal_users_id = 0

        if global_last_id.value < last_onesignal_users_id:
            global_last_id.value = last_onesignal_users_id

        try:
            insert_dataframe.loc[
                :,
                'id'] = range(
                global_last_id.value +
                1,
                len(insert_dataframe) +
                global_last_id.value +
                1)
        except Exception as error:
            logger.info("UPDATING ID ERROR: ", error)
        global_last_id.value = len(dataframe) + global_last_id.value

        dataframe = pd.concat([insert_dataframe, update_dataframe])
        dataframe['id'] = dataframe['id'].astype(np.int64)

        output = cStringIO.StringIO()

        # print(dataframe)

        try:
            # ignore the index
            dataframe.to_csv(
                output,
                sep='\t',
                header=False,
                index=False,
                encoding='utf-8')
            # dataframe.to_csv('parsed_csv.csv', sep='|', encoding='utf-8')
        except Exception as error:
            logger.info('AN ERROR EXPORTING DATAFRAME TO CSV {}'.format(error))

        # jump to start of stream
        output.seek(0)
        contents = output.getvalue()
        # print(contents)

        # null values become ''
        try:
            cur.copy_from(output, 'onesignal_users', null="")
        except Exception as error:
            logger.info('ERROR COPYING TO DATABASE {}'.format(error))

        connection.commit()

        cur.close()

        lock.release()

    # Deletes previously created onesignal app gzip file
    def clean_up_files(self, filename):
        try:
            os.remove("{}".format(filename))
        except:
            pass

    # Creates connection to postgres
    def connect_to_postgres(self):
        logger.info('Establishing database connection...')
        self.conn = psycopg2.connect(
            database=self.db,
            user=self.username,
            password=self.password,
            host=self.host)
        self.cur = self.conn.cursor()
        logger.info("Database connection established.")

    # Closes connection to postgres
    def close_connection_to_postgres(self):
        self.cur.close()
        self.conn.commit()
        self.conn.close()

    def t_and_f_to_boolean(self, value):
        if value == 't':
            return True
        else:
            return False

    def main(self):
        global lock
        counter = 0
        """
    Loop through each app and make a request to update the given subscriber key in each app.
    """
        for app_id, rest_auth in app_ids.iteritems():
            # IF STATEMENT WILL BE REMOVED IN PRODUCTION
            if counter < len(app_ids):
                # if counter < 1:

                response = self.get_download_url(
                    app_id, rest_auth)  # ["csv_file_url"]

                url = json.loads(response.content)["csv_file_url"]
                print("THE URL: {}".format(url))

                filename = self.download_file(url)

                reader = self.read_gzip(filename)

                ##########
                # SKIP DOWNLOAD
                ##########
                # filename = 'download_insert.csv.gz'
                # filename = 'download_update.csv.gz'
                # filename = 'download_insert_update.csv.gz'
                # reader = self.read_gzip(filename)
                # for idx, intermediate_df in enumerate(reader):
                #   if idx < 1:
                #     print(list(intermediate_df))

                mpt = MultiprocessTool()

                lock = mpt.lock

                result = mpt.run_multiprocess(
                    self.process_frame, reader, app_id)

                print("FINISHED PROCESSING ONESIGNAL RESPONSE")

                result.to_csv('parsed_csv.csv', sep='|', encoding='utf-8')

                result = pd.read_csv("parsed_csv.csv", sep='|')
                ###################
                # COMMENTED OUT POSTGRES REQUEST TO CHECK IF THE ONESIGNAL USERS HAVE ALREADY EXIST.
                ##########

                # self.connect_to_postgres()
                # self.cur.execute("SELECT subscriber, id FROM onesignal_users WHERE subscriber IN {};".format(tuple(result['subscriber'].astype(str))))
                # sss = self.cur.fetchall()
                # print("THE REPEATED SUBSCRIBERS ARE: {}".format(len(sss)))
                # self.cur.execute("SELECT count(*) FROM onesignal_users")
                # print(self.cur.fetchall())
                # print("THE SHAPE IS {}".format(result.shape))

                start_time = time.time()

                # save_result = mpt.run_multiprocess(self.save_to_postgres, self.dataframe_chunker(output1))
                mpt.update_num_of_processes(1)
                save_result = mpt.run_multiprocess(
                    self.save_to_postgres, mpt.data_chunker(result, self.chunksize))
                # self.save_to_postgres(result)

                print(
                    "TOTAL TIME TO SAVE TO POSTGRES {}".format(
                        time.time() - start_time))
                # self.cur.execute("SELECT count(*) FROM onesignal_users")
                # print(self.cur.fetchall()[0])
                # print("FINISHED SAVING TO ONESIGNAL_USERS")

                # self.close_connection_to_postgres()

                self.clean_up_files(filename)
                self.clean_up_files('parsed_csv.csv')

            counter += 1


class UpdateOfferDetails(object):

    """UpdateOfferDetails polls Voluum for data available between the start_date and end_date arguments (defaulting to the last days interval).
    This is done by retrieving an accesses token and subsequently requesting the data. Afterwards the data is parsed into a format compatible with the offer_details Postgres table."""

    # Instanciates UpdateOfferDetails class and sets class variables as well
    # as initializing connection to postgres and gets new Voluum access_token.
    def __init__(self, username, password, host, db, table, access_key, access_key_id, start_date=str(
            datetime.date.today() - datetime.timedelta(30)), end_date=str(datetime.date.today()), chunksize=1500):
        super(UpdateOfferDetails, self).__init__()
        try:
            self.username = username
        except ValueError as error:
            logger.info('username is required')
        try:
            self.password = password
        except ValueError as error:
            logger.info('password is required')
        try:
            self.host = host
        except ValueError as error:
            logger.info('host is required')
        try:
            self.db = db
        except ValueError as error:
            logger.info('database is required')
        try:
            self.table = table
        except ValueError as error:
            logger.info('table is required')
        try:
            self.access_key = access_key
        except ValueError as error:
            logger.info('a Voluum acccess_key is required')
        try:
            self.access_key_id = access_key_id
        except ValueError as error:
            logger.info('A Voluum access_key_id is required')
        try:
            self.token = self.get_token()
        except ValueError as error:
            logger.info('unable to retreive Voluum token')
        try:
            self.chunksize = chunksize
        except ValueError as error:
            logger.info('chunksize is required')
        self.start_date = start_date
        self.end_date = end_date
        self.connect_to_postgres()

        # DECLARE SHARED GLOBAL VALUE FOR MultiprocessTool
        global global_last_id
        global_last_id = mp.Value('i', 0)

    # Creates connection to Postgres
    def connect_to_postgres(self):
        logger.info('Establishing database connection...')
        self.conn = psycopg2.connect(
            database=self.db,
            user=self.username,
            password=self.password,
            host=self.host)
        self.cur = self.conn.cursor()
        logger.info("Database connection established.")

    # Closes connection to postgres.
    def close_connection_to_postgres(self):
        self.cur.close()
        self.conn.commit()
        self.conn.close()

    # Requests a new access token from Voluum as these have an expiration date.
    def get_token(self):
        headers = {"Content-Type": "application/json; charset=utf-8",
                   "Accept": "application/json"}
        data = {"accessId": self.access_key_id,
                "accessKey": self.access_key}
        url = 'https://api.voluum.com/auth/access/session'
        req = requests.post(url, headers=headers, data=json.dumps(data))
        token = str(json.loads(req.content)["token"])
        print("GOT TOKEN! {}".format(token))
        return token

    # Requests data from Voluum, sorting by subs_key and offers. Retreiving
    # the subscriber_key, offerName, visits, conversions, revenue, offerId and
    # clicks fields.
    def get_voluum_report_csv(self):
        headers = {"Content-Type": "application/json; charset=utf-8",
                   "Accept": "text/csv",
                   "cwauth-token": self.token}

        url = 'https://api.voluum.com/report?from={0}&to={1}&tz=America%2FChicago&limit=100&sort=conversions&direction=desc&columns=customVariable6&columns=offerName&columns=visits&columns=conversions&columns=revenue&columns=offerId&columns=clicks&groupBy=custom-variable-6&groupBy=offer&offset=0&include=ACTIVE&conversionTimeMode=VISIT&filter1=campaign&filter1Value=0faecec5-56de-4a85-acb9-49fa4902d071'.format(
            self.start_date, self.end_date)
        req = requests.post(url, headers=headers)
        print("GOT CSV REPORT!")
        return req.content

    # removes replaces all subscriber keys that do not match a UUID4 format
    # with the string "unknown"
    def remove_all_non_base_16(self, string):

        regex_str = '[0-9a-zA-Z]{8}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{12}'
        prog = re.compile(regex_str)
        if isinstance(string, str):
            if bool(re.match(prog, string)):
                return string
            else:
                return "unknown"
        else:
            return "unknown"

    def clean_up_subscriber(self, string):
        if len(string) > 36:
            return string[:36]
        else:
            return string

    def trim_fraction(self, text):
        if isinstance(text, float):
            return int(text)
        return text

    @retryer(max_retries=3, timeout=5)
    # def save_to_postgres(self, dataframe, mp_lock):
    def save_to_postgres(self, dataframe):
        global global_last_id
        global lock

        # initiate posgres engine and cursor
        engine = create_engine(
            "postgresql://{0}:{1}@{2}/{3}".format(self.username, self.password, self.host, self.db))
        connection = engine.raw_connection()
        cur = connection.cursor()

        # declare accepted columns
        accepted_columns = [
            "id",
            "onesignal_user_id",
            "created_at",
            "updated_at",
            "subscriber",
            "offer",
            "offer_id",
            "visits",
            "conversions",
            "revenue",
            "clicks"]

        # Initial dataframe formatting:
        dataframe['id'] = dataframe.index
        dataframe = dataframe.drop("Unnamed: 0", 1)

        for col_name in list(set(accepted_columns) - set(list(dataframe))):
            dataframe[col_name] = 'NULL'

        dataframe['offer_id'] = dataframe['offer_id'].fillna('NULL')
        dataframe['onesignal_user_id'] = dataframe[
            'onesignal_user_id'].fillna('NULL')
        dataframe['updated_at'] = dataframe['updated_at'].fillna('NULL')

        # Apply trim fraction
        try:
            dataframe['onesignal_user_id'] = dataframe[
                'onesignal_user_id'].apply(self.trim_fraction)
        except Exception as error:
            logger.info('AN ERROR APPLYING trim_fracition {}'.format(error))

        # clean up subscribers length:
        try:
            dataframe['subscriber'] = dataframe[
                'subscriber'].apply(self.clean_up_subscriber)
        except Exception as error:
            logger.info(
                'AN ERROR APPLYING clean_up_subscriber {}'.format(error))

        # Get all subscriber offer pairs that are not null
        sub_offer_ids_tuple = tuple(zip(tuple(dataframe["subscriber"]), tuple(
            dataframe.loc[dataframe['offer_id'] != "NULL", 'offer_id'])))

        if len(sub_offer_ids_tuple) > 0:

            try:
                # Get existing DB subscriber data
                cur.execute('SELECT id, subscriber, offer_id, created_at FROM offer_details WHERE (subscriber, offer_id) IN {};'.format(
                    sub_offer_ids_tuple))
                ids_subs_offer_ids_created_ats_response = cur.fetchall()

                if ids_subs_offer_ids_created_ats_response:
                    # Split 2 dimensional tuple into 4 separate tuples
                    ids, subs, offer_ids, created_ats = zip(
                        *ids_subs_offer_ids_created_ats_response)

                    # Separate into 2 dataframes
                    update_dataframe = dataframe[
                        (dataframe['subscriber'].isin(subs)) & (
                            dataframe['offer_id'].isin(offer_ids))]
                    insert_dataframe = dataframe[~(dataframe['subscriber'].isin(
                        subs)) & (dataframe['offer_id'].isin(offer_ids))]

                    # Format update_dataframe
                    update_dataframe.loc[
                        :, 'updated_at'] = update_dataframe['created_at']
                    for idx, sub in enumerate(subs):
                        update_dataframe.loc[
                            (update_dataframe.subscriber == sub) & (
                                update_dataframe.offer_id == offer_ids[idx]), [
                                'created_at', 'id']] = [
                            created_ats[idx], ids[idx]]

                    sub_offer_ids_tuple = tuple(
                        zip(tuple(str(i) for i in subs), tuple(str(i) for i in offer_ids)))
                    query = "DELETE FROM offer_details WHERE id IN {0};".format(
                        ids)
                    cur.execute(query)

                else:
                    update_dataframe = pd.DataFrame()
                    insert_dataframe = dataframe.copy()

            except Exception as error:
                logger.info(
                    'AN ERROR SELECTION IDS, SUBSCRIBERS AND CREATED_AT {}'.format(error))

        lock.acquire()

        # Get last offer_details id and compare to global_last_id.value
        cur.execute('SELECT MAX(id) FROM offer_details;')
        last_offer_details_id = cur.fetchone()[0]

        if last_offer_details_id is None:
            last_offer_details_id = 0
        if global_last_id.value < last_offer_details_id:
            global_last_id.value = last_offer_details_id

        # increment id on new subscribers
        try:
            insert_dataframe.loc[
                :,
                'id'] = range(
                global_last_id.value +
                1,
                len(insert_dataframe) +
                global_last_id.value +
                1)
        except Exception as error:
            logger.info("UPDATING ID ERROR: ", error)

        global_last_id.value = len(dataframe) + global_last_id.value

        dataframe = pd.concat([insert_dataframe, update_dataframe])

        dataframe = dataframe[accepted_columns]
        dataframe['id'] = dataframe['id'].astype(np.int64)

        output = cStringIO.StringIO()

        try:
            # ignore the index
            dataframe.to_csv(
                output,
                sep='|',
                header=False,
                index=False,
                encoding='utf-8')

        except Exception as error:
            logger.info('AN ERROR EXPORTING DATAFRAME TO CSV {}'.format(error))

        # jump to start of stream
        output.seek(0)
        contents = output.getvalue()

        # null values become ''
        try:
            cur.copy_from(output, 'offer_details', null="NULL", sep="|")
        except Exception as error:
            logger.info('ERROR COPYING TO DATABASE {}'.format(error))

        connection.commit()

        cur.close()

        lock.release()

    def main(self):
        global lock
        # Requests Voluum CSV report
        csv = self.get_voluum_report_csv()

        # Parses Voluum CSV report into pandas dataframe
        df = pd.read_csv(StringIO(csv))

        # Sets dataframe column names
        df.columns = [
            'subscriber',
            'offer',
            'visits',
            'conversions',
            'revenue',
            'offer_id',
            'clicks']

        # Sets to "unknown" all non UUID4 subscribers
        df['subscriber'] = df['subscriber'].apply(self.remove_all_non_base_16)

        # Retreives all onesignal_user_ids corresponding to the subscribers
        # from the Voluum CSV report
        self.cur.execute(
            "SELECT subscriber, id FROM onesignal_users WHERE subscriber IN {};".format(
                tuple(
                    df['subscriber'])))
        response = self.cur.fetchall()

        subscribers_and_onesignal_user_ids = pd.DataFrame(
            response, columns=['subscriber', 'onesignal_user_id'])
        # subscribers_and_onesignal_user_ids["onesignal_user_id"] = subscribers_and_onesignal_user_ids["onesignal_user_id"].astype(np.int64)
        # print(subscribers_and_onesignal_user_ids['onesignal_user_id'])

        # Merges onesignal_user_ids with Voluum Report dataframe
        result = df.merge(
            subscribers_and_onesignal_user_ids,
            on='subscriber',
            how='outer')
        result['created_at'] = datetime.datetime.now()

        # print("THIS IS THE LOCK BEFORE MPT: ", lock)
        # Instanciates multiprocessor.
        mpt = MultiprocessTool()

        # print("THIS IS THE LOCK AFTER MPT: ", lock)
        lock = mpt.lock
        print("THIS IS THE LOCK AFTER MPT AND VAR SET: ", lock)

        result.to_csv('parsed_csv.csv', sep='|', encoding='utf-8')

        result = pd.read_csv("parsed_csv.csv", sep='|')

        start_time = time.time()

        # Saves Voluum Report dataframe to offer_details Postgres table
        save_result = mpt.run_multiprocess(
            self.save_to_postgres,
            mpt.data_chunker(result, self.chunksize))

        print(
            "TOTAL TIME TO SAVE TO POSTGRES {}".format(
                time.time() -
                start_time))

        self.close_connection_to_postgres()
        self.clean_up_files('parsed_csv.csv')


class UpdateOneSignalOfferGroupTags(object):
        # Instanciates UpdateOfferDetails class and sets class variables as well
        # as initializing connection to postgres and gets new Voluum
        # access_token.

    def __init__(
            self,
            app_ids,
            username,
            password,
            host,
            db,
            start_date=str(
                datetime.date.today() -
                datetime.timedelta(1)),
            end_date=str(
                datetime.date.today())):
        super(UpdateOneSignalOfferGroupTags, self).__init__()
        try:
            self.app_ids = app_ids
        except ValueError as error:
            logger.info('app ids are required')
        try:
            self.username = username
        except ValueError as error:
            logger.info('username is required')
        try:
            self.password = password
        except ValueError as error:
            logger.info('password is required')
        try:
            self.host = host
        except ValueError as error:
            logger.info('host is required')
        try:
            self.db = db
        except ValueError as error:
            logger.info('database is required')
        self.start_date = start_date
        self.end_date = end_date
        self.connect_to_postgres()

    # Creates connection to Postgres
    def connect_to_postgres(self):
        """
        Connect to AWS RDS Postgres
        """
        logger.info('Establishing database connection...')
        self.conn = psycopg2.connect(
            database=self.db,
            user=self.username,
            password=self.password,
            host=self.host)
        self.cur = self.conn.cursor()
        logger.info("Database connection established.")

    # Closes connection to postgres.
    def close_connection_to_postgres(self):
        """
        Disconnect from AWS RDS Postgres
        """
        self.cur.close()
        self.conn.commit()
        self.conn.close()

    # Retrieves the url to download onesignal app data
    @retryer(max_retries=20, timeout=10)
    def put_tag_update(self, onesignal_app_id,
                       rest_authorization, subscriber_key, offer_group_key):
        """
        Updates the offer_group_key in OneSignal users
        """
        rest_authorization = "Basic {}".format(rest_authorization)
        headers = {"Content-Type": "application/json; charset=utf-8",
                   "Authorization": rest_authorization}
        data = {"app_id": onesignal_app_id,
                "tags": {"offer_group_key": "{}".format(offer_group_key)}}
        params = {}
        url = "https://onesignal.com/api/v1/players/{}".format(
            subscriber_key)
        logger.info('Header:')
        logger.info(headers)
        logger.info('Endpoint:')
        logger.info(url)
        logger.info('Params:')
        logger.info(params)
        logger.info('Data:')
        logger.info(data)

        print(url)
        try:
            req = requests.put(
                url,
                params=params,
                data=json.dumps(data),
                headers=headers)
            if req.status_code == 200:
                print("good request")
                return req
            elif req.status_code == 400:
                print(req.content)
                raise MyAppLookupError(
                    'App id and/or rest authorization are incorrect')
            else:
                # raise Exception('SOMETHING WENT TERRIBLY WRONG')
                raise MyAppLookupError('SOMETHING WENT TERRIBLY WRONG')
        except Exception as error:
            print("THERE WAS AN ERROR! {}".format(error))

    def get_converted_subscribers_for_offer_id(self, offer_id):
        """
        Gets all subscribers who have converted on an offer
        """
        try:
            self.cur.execute(
                "select subscriber from offer_details where subscriber != 'unknown' and offer_id='{}' and conversions > 0 and created_at > now()::date - 7;".format(offer_id))
            subscribers = self.cur.fetchall()
            return subscribers
        except Exception as error:
            print("ERROR SELECTING CONVERTED USERS: offer_details", error)

    def get_unconverted_subscribers_for_offer_id(self, offer_id):
        """
        Gets all subscribers who have visited an offer >10 times
        without converting.
        """
        try:
            self.cur.execute(
                "select subscriber from offer_details where subscriber != 'unknown' and offer_id='{}' and conversions = 0 and visits > 10 and created_at > now()::date - 7;".format(offer_id))
            subscribers = self.cur.fetchall()
            return subscribers
        except Exception as error:
            print("ERROR SELECTING CONVERTED USERS: offer_details", error)

    def main(self):
        counter = 0
        """
        Loop through each app and make a request
        to update the given subscriber key in each app.
        """
        self.connect_to_postgres()

        converted_users = self.get_converted_subscribers_for_offer_id(
            '78e50b5a-9e6b-4198-88c9-a1d6a5f47db8')
        unconverted_users = self.get_unconverted_subscribers_for_offer_id(
            '78e50b5a-9e6b-4198-88c9-a1d6a5f47db8')
        start_time = time.time()
        tagged_converted_users = []
        tagged_unconverted_users = []

        for app_id, rest_auth in app_ids.iteritems():
            if counter < len(app_ids):
                for subscriber_key in converted_users:
                    offer_group_key = '2'
                    response = self.put_tag_update(
                        app_id, rest_auth, subscriber_key[0], offer_group_key)
                    if response:
                        if response.status_code == 200:
                            tagged_converted_users.append(subscriber_key[0])

                for subscriber_key in unconverted_users:
                    offer_group_key = '2-none'
                    response = self.put_tag_update(
                        app_id, rest_auth, subscriber_key[0], offer_group_key)
                    if response:
                        if response.status_code == 200:
                            tagged_unconverted_users.append(subscriber_key[0])
            converted_users = [
                user[0] for user in converted_users if not user[0] in tagged_converted_users]
            unconverted_users = [user[0] for user in unconverted_users if not user[
                0] in tagged_unconverted_users]

        print(
            "TOTAL TIME TO UPDATE TAGS: {}".format(
                time.time() - start_time))
        logger.info('Updating tags completed.')

if __name__ == "__main__":

    host = os.environ["PUSH_DB_HOST"]
    db = os.environ["PUSH_DB"]
    username = os.environ["PUSH_DB_USER"]
    password = os.environ["PUSH_DB_PASSWD"]
    onesignal_users_table = os.environ["PUSH_DB_ONESIGNAL_USERS"]
    offer_details_table = os.environ["PUSH_DB_OFFER_DETAILS"]
    voluum_access_key = os.environ["VOLUUM_ACCESS_KEY"]
    voluum_access_key_id = os.environ["VOLUUM_ACCESS_KEY_ID"]
    zeropark_access_key = os.environ["ZEROPARK_ACCESS_KEY"]

    # username = 'postgres'
    # password = 'postgres'
    # host = 'localhost'
    # db = 'pushengine'
    # onesignal_users_table = 'onesignal_users'
    # voluum_access_key_id = "aa14a894-9d68-4255-9980-5c07eb03aa16"
    # voluum_access_key = "EJGBMLqKxK8Whrat0sjEY-3df8YYrPnbrOdA"
    # offer_details_table = 'offer_details'
    """
    UpdateOneSignalUsers(
        app_ids,
        username,
        password,
        host,
        db,
        onesignal_users_table).main()
    """
    UpdateOfferDetails(
        username,
        password,
        host,
        db,
        offer_details_table,
        voluum_access_key,
        voluum_access_key_id).main()
    """
    UpdateOneSignalOfferGroupTags(
        app_ids,
        username,
        password,
        host,
        db,
        start_date=str(
            datetime.date.today() -
            datetime.timedelta(1)),
        end_date=str(
            datetime.date.today())).main()
    """

####################################
# POSTGRES onesignal_users RECIPIES:
####################################
########
# ONESIGNAL_USERS TABLE:
########


# DROP TABLE public.onesignal_users;

# OLD TABLE:
# CREATE TABLE public.onesignal_users (
#   id serial PRIMARY KEY,
#   created_at Timestamp,
#   updated_at Timestamp,
#   player_id text,
#   is_active text,
#   tags text,
#   thumbnail text,
#   name text,
#   image text,
#   badge text,
#   num_user_sent numeric(9,2),
#   identifier varchar(256),
#   session_count int,
#   language varchar(10),
#   sourcename text,
#   subscriber char(36) NOT NULL,
#   ip inet,
#   os text,
#   isp text,
#   city text,
#   brand text,
#   model text,
#   device text,
#   region text,
#   browser text,
#   carrier text,
#   osversion text,
#   browserversion text,
#   country char(2),
#   timezone int,
#   onesignal_created_at Timestamp
#   additional_tags text,
# );

# NEW TABLE
# CREATE TABLE public.onesignal_users (
#   id serial PRIMARY KEY,
#   created_at Timestamp,
#   updated_at Timestamp,
#   player_id char(36),
#   is_active boolean,
#   thumbnail varchar(255),
#   name varchar(255),
#   image varchar(255),
#   badge varchar(255),
#   num_user_sent numeric(9,2),
#   identifier varchar(256),
#   session_count int,
#   language varchar(10),
#   sourcename varchar(255),
#   subscriber char(36) NOT NULL,
#   ip inet,
#   os varchar(255),
#   isp varchar(255),
#   city varchar(255),
#   brand varchar(255),
#   model varchar(255),
#   device varchar(255),
#   region varchar(255),
#   browser varchar(255),
#   carrier varchar(255),
#   osversion varchar(255),
#   browserversion varchar(255),
#   country char(2),
#   timezone int,
#   onesignal_created_at Timestamp,
#   additional_tags text,
#   last_active Timestamp
# );

########
# ONESIGNAL_USERS  INDEX:
########


# DROP INDEX onesignal_users_index;

# CREATE UNIQUE INDEX onesignal_users_index
# ON onesignal_users (subscriber);


########
# ONESIGNAL_USERS  RULE:
########

# DROP RULE onesignal_users_insert ON onesignal_users;

# CREATE RULE onesignal_users_insert AS ON insert TO public.onesignal_users
#   WHERE EXISTS (SELECT * FROM onesignal_users WHERE subscriber = NEW.subscriber)
# DO INSTEAD UPDATE onesignal_users SET updated_at = NEW.created_at,
# player_id = NEW.player_id, is_active = NEW.is_active, additional_tags =
# NEW.additional_tags, thumbnail = NEW.thumbnail, name = NEW.name, badge =
# NEW.badge, num_user_sent = NEW.num_user_sent, identifier =
# NEW.identifier, session_count = NEW.session_count, language =
# NEW.language, sourcename = NEW.sourcename, ip = NEW.ip, os = NEW.os, isp
# = NEW.isp, city = NEW.city, brand = NEW.brand, model = NEW.model, device
# = NEW.device, region = NEW.region, browser = NEW.browser, carrier =
# NEW.carrier, osversion = NEW.osversion, browserversion =
# NEW.browserversion, country = NEW.country, timezone = NEW.timezone,
# onesignal_created_at = NEW.onesignal_created_at WHERE subscriber =
# NEW.subscriber;


# ######
# #CREATE OFFER DETAILS TABLE:
# #########

# DROP TABLE offer_details;

# CREATE TABLE public.offer_details (
#   id serial PRIMARY KEY,
#   onesignal_user_id int REFERENCES onesignal_users ON DELETE CASCADE,
#   created_at Timestamp,
#   updated_at timestamp,
#   subscriber char(36) NOT NULL,
#   offer text,
#   offer_id char(36) NOT NULL,
#   visits int NOT NULL,
#   conversions int NOT NULL,
#   revenue int NOT NULL,
#   clicks int NOT NULL,
#   UNIQUE (onesignal_user_id, offer_id)
# );

# ########
# #OFFER DETAILS INDEX:
# ########

# DROP INDEX offer_details_subscriber_offer_id_index;
# CREATE INDEX offer_details_subscriber_offer_id_index ON
# public.offer_details (subscriber, offer_id);


# INSERT INTO offer_details (onesignal_user_id, created_at, updated_at, subscriber, offer, offer_id, visits, conversions, revenue)
# VALUES (397666 , '2018-04-09 00:00:00', '2018-04-09 00:00:05', '0b6ec43e-4889-4077-8a67-ff09c00fc110', 'MundoMedia - Global - 32300 - Well Hello - LP 391888', '78e50b5a-9e6b-4198-88c9-a1d6a5f47db8', 11401, 59, 177);


# INSERT INTO offer_details (onesignal_user_id, created_at, updated_at, subscriber, offer, offer_id, visits, conversions, revenue)
# VALUES (397666 , '2018-04-03 00:00:00', NULL, '0b6ec43e-4889-4077-8a67-ff09c00fc110', 'MundoMedia - United States - 671434 - Billionaire Casino - All Traffic', '23620516-7c28-407f-a1aa-8b61f902cd09', 1, 1, 2);


# ########
# #OFFER DETAILS RULE:
# ########

# DROP RULE offer_details_insert ON offer_details;


# CREATE RULE offer_details_insert AS ON insert TO public.offer_details
#   WHERE EXISTS (SELECT * FROM offer_details WHERE subscriber = NEW.subscriber AND offer_id = New.offer_id) AND (New.subscriber <> 'unknown')
# DO INSTEAD UPDATE offer_details SET updated_at = NEW.created_at, revenue
# = NEW.revenue, visits = NEW.visits, conversions = NEW.conversions WHERE
# subscriber = NEW.subscriber AND offer_id = NEW.offer_id;


##############
# DELETE ALL:
########

# DROP RULE offer_details_insert ON offer_details;
# DROP INDEX offer_details_subscriber_offer_id_index;
# DROP TABLE offer_details;
# DROP RULE onesignal_users_insert ON onesignal_users;
# DROP INDEX onesignal_users_index;
# DROP TABLE public.onesignal_users;
# CREATE TABLE public.onesignal_users (
#   id serial PRIMARY KEY,
#   created_at Timestamp,
#   updated_at Timestamp,
#   player_id char(36),
#   is_active boolean,
#   thumbnail varchar(255),
#   name varchar(255),
#   image varchar(255),
#   badge varchar(255),
#   num_user_sent numeric(9,2),
#   identifier varchar(256),
#   session_count int,
#   language varchar(10),
#   sourcename varchar(255),
#   subscriber char(36) NOT NULL,
#   ip inet,
#   os varchar(255),
#   isp varchar(255),
#   city varchar(255),
#   brand varchar(255),
#   model varchar(255),
#   device varchar(255),
#   region varchar(255),
#   browser varchar(255),
#   carrier varchar(255),
#   osversion varchar(255),
#   browserversion varchar(255),
#   country char(2),
#   timezone int,
#   onesignal_created_at Timestamp,
#   additional_tags text,
#   last_active Timestamp
# );

# CREATE UNIQUE INDEX onesignal_users_index
# ON onesignal_users (subscriber);
# CREATE UNIQUE INDEX onesignal_users_index
# ON onesignal_users (subscriber);

# CREATE RULE onesignal_users_insert AS ON insert TO public.onesignal_users
#   WHERE EXISTS (SELECT * FROM onesignal_users WHERE subscriber = NEW.subscriber)
# DO INSTEAD UPDATE onesignal_users SET updated_at = NEW.created_at,
# player_id = NEW.player_id, is_active = NEW.is_active, additional_tags =
# NEW.additional_tags, thumbnail = NEW.thumbnail, name = NEW.name, badge =
# NEW.badge, num_user_sent = NEW.num_user_sent, identifier =
# NEW.identifier, session_count = NEW.session_count, language =
# NEW.language, sourcename = NEW.sourcename, ip = NEW.ip, os = NEW.os, isp
# = NEW.isp, city = NEW.city, brand = NEW.brand, model = NEW.model, device
# = NEW.device, region = NEW.region, browser = NEW.browser, carrier =
# NEW.carrier, osversion = NEW.osversion, browserversion =
# NEW.browserversion, country = NEW.country, timezone = NEW.timezone,
# onesignal_created_at = NEW.onesignal_created_at WHERE subscriber =
# NEW.subscriber;


# CREATE TABLE public.offer_details (
#   id serial PRIMARY KEY,
#   onesignal_user_id int REFERENCES onesignal_users ON DELETE CASCADE,
#   created_at Timestamp,
#   updated_at timestamp,
#   subscriber varchar(46) NOT NULL,
#   offer text,
#   offer_id char(36) NOT NULL,
#   visits int NOT NULL,
#   conversions int NOT NULL,
#   revenue float NOT NULL,
#   clicks int NOT NULL,
#   UNIQUE (onesignal_user_id, offer_id)
# );

# CREATE INDEX offer_details_subscriber_offer_id_index ON
# public.offer_details (subscriber, offer_id);

# CREATE RULE offer_details_insert AS ON insert TO public.offer_details
#   WHERE EXISTS (SELECT * FROM offer_details WHERE subscriber = NEW.subscriber AND offer_id = New.offer_id) AND (New.subscriber <> 'unknown')
# DO INSTEAD UPDATE offer_details SET updated_at = NEW.created_at, revenue
# = NEW.revenue, visits = NEW.visits, conversions = NEW.conversions WHERE
# subscriber = NEW.subscriber AND offer_id = NEW.offer_id;
