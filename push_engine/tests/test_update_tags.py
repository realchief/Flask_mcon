import unittest
import requests
import sys
import json
import os
import pandas
import datetime
# import unittest, sys, json, datetime, pymysql, keepaAPI
sys.path.append("..")
from update_tags import UpdateOneSignalUsers, UpdateOfferDetails
from mock import patch, Mock, MagicMock
import ast
import re
from freezegun import freeze_time




@freeze_time("2017-10-30")
class TestUpdateOneSignalUsers(unittest.TestCase):
  #CREATE METHODS TO INITIALIZE TESTING EXAMPLES, BEFORE EACH TEST CASE

  
  def setUp(self):
    self.good_id = "cb48c5f8-083e-4893-a330-2162ec73ce73"
    self.good_auth = "MTc4NGE3MzItZjZkMC00NjczLWE3NzAtZWYxYjFlM2Q2MDFj"
    self.bad_id = "I DO NOT EXIST"
    self.bad_auth = "I AM NOT AUTHORIZED"
    self.good_url = "https://onesignal.s3.amazonaws.com/csv_exports/cb48c5f8-083e-4893-a330-2162ec73ce73/users_a5f04c879dda67fa7d51327d811d268b_2018-04-11.csv.gz"
    self.bad_url = "THIS IS NOT A URL"
    self.good_filename = "./download.csv.gz"
    self.bad_filename = "THIS FILE DOES NOT EXIST"
    self.app_ids = {"cb48c5f8-083e-4893-a330-2162ec73ce73": 
                   "MTc4NGE3MzItZjZkMC00NjczLWE3NzAtZWYxYjFlM2Q2MDFj",
                   "26d0af0e-1eb1-4773-8df5-172b2382bccb":
                   "ZGU2ZDc1OTUtOTg0Ni00MTY3LWExNjUtMmVkMzMxNDhkMjE1L"}
    self.username = "test_username"
    self.password = "test_password"
    self.host = "test_host"
    self.db = "test_db"
    self.table = "test_table"

    dataframe_rows = [
                      #1) Row with no subscriber and no tags (should be deleted)
                      ("", "number_1", 111, "xx", 11, "", "Windows", "MOBILE", "tablet", "", '', datetime.datetime.now()-datetime.timedelta(1), "", "", datetime.datetime.now()-datetime.timedelta(10), "", ""),
                      #2) Row with no subscriber and tags (should be deleted)
                      ("", "number_2", 222, "xx", 22, "", "Android", "MOBILE", "Sony Erickson", "", '{"subscriber_key": "", "region_key": "number_2", "another_made_up_tag": "bleep bloop"}', datetime.datetime.now()-datetime.timedelta(2), "", "", datetime.datetime.now()-datetime.timedelta(20), "", ""),
                      #3) Row with subscriber, no tags
                      ("row_with_no_tags", "number_3", 333, "en", 33, "", "Android", "MOBILE", "Samsung S7", "", "{}", datetime.datetime.now()-datetime.timedelta(3), "", "", datetime.datetime.now()-datetime.timedelta(30), "", ""),
                      #4) Row with subscriber and whitelisted tags
                      ("row_with_whitelisted_tags", "number_4", 444, "es", 44, "", "Apple", "MOBILE", "Iphone X", "", '{"subscriber_key": "row_with_whitelisted_tags", "region_key": "number_4"}', datetime.datetime.now()-datetime.timedelta(4), "", "", datetime.datetime.now()-datetime.timedelta(40), "", ""),
                      #5) Row with subscriber and additional tags
                      ("row_with_additional_tags", "number_5", 555, "ch", 55, "", "Huawei", "MOBILE", "phone", "", '{"subscriber_key": "row_with_additional_tags", "region_key": "number_5", "some_made_up_tag": "blah blah blah"}', datetime.datetime.now()-datetime.timedelta(5), "", "", datetime.datetime.now()-datetime.timedelta(50), "", ""),
                      #6) Row with non matching row["subscriber"] and tags["subscriber_key"] (NON EXISTANT SUBSCRIBER_KEY)
                      ("non_matching_row_and_tags_subs", "number_6", 666, "xx", 66, "", "Windows", "MOBILE", "tablet", "", '{"subscriber_key": "non_matching_tags_and_row_subs", "region_key": "number_6", "another_made_up_tag": "bleep bloop"}', datetime.datetime.now()-datetime.timedelta(6), "", "", datetime.datetime.now()-datetime.timedelta(60), "", ""),
                      # #7,8) Multiple rows with same subscriber same tags
                      # ("same_subscriber_same_tags", "number_7", 777, "xx", 77, "", "Windows", "MOBILE", "tablet", "", '{"subscriber_key": "same_subscriber_same_tags", "region_key": "number_7and8", "aux_tag": "from_7"}', datetime.datetime.now()-datetime.timedelta(7), "", "", datetime.datetime.now()-datetime.timedelta(70), "", ""),
                      # ("same_subscriber_same_tags", "number_8", 888, "xx", 88, "", "Windows", "MOBILE", "tablet", "", '{"subscriber_key": "same_subscriber_same_tags", "region_key": "number_7and8", "aux_tag":"from_8"}', datetime.datetime.now()-datetime.timedelta(8), "", "", datetime.datetime.now()-datetime.timedelta(80), "", ""),
                      # #9,10) Multiple rows with same subscriber different tags:
                      # ("same_subscriber_diff_tags", "number_9", 999, "xx", 99, "", "Windows", "MOBILE", "tablet", "", '{"subscriber_key": "same_subscriber_diff_tags", "region_key": "number_9"}', datetime.datetime.now()-datetime.timedelta(9), "", "", datetime.datetime.now()-datetime.timedelta(90), "", ""),
                      # ("same_subscriber_diff_tags", "number_10", 101010, "xx", 10, "", "Windows", "MOBILE", "tablet", "", '{"subscriber_key": "same_subscriber_diff_tags", "region_key": "number_10"}', datetime.datetime.now()-datetime.timedelta(10), "", "", datetime.datetime.now()-datetime.timedelta(100), "", ""),

                      # #11,12) 2 rows with same subscriber only second with tags:
                      # ("2_rows_same_sub_tags_only_on_second", "number_11", 111111, "xx", 110, "", "Windows", "MOBILE", "tablet", "", '', datetime.datetime.now()-datetime.timedelta(11), "", "", datetime.datetime.now()-datetime.timedelta(110), "", ""),
                      # ("2_rows_same_sub_tags_only_on_second", "number_12", 121212, "xx", 120, "", "Windows", "MOBILE", "tablet", "", '{"subscriber_key": "2_rows_same_sub_tags_only_on_second", "region_key": "number_12"}', datetime.datetime.now()-datetime.timedelta(12), "", "", datetime.datetime.now()-datetime.timedelta(120), "", ""),
                      # #2 rows, second rows's tag subscriber_key = row1[subscriber]:
                      # ("2_rows_same_sub_tags_only_on_second", "number_13", 131313, "xx", 130, "", "Windows", "MOBILE", "tablet", "", '', datetime.datetime.now()-datetime.timedelta(13), "", "", datetime.datetime.now()-datetime.timedelta(130), "", ""),
                      # ("2_rows_same_sub_tags_only_on_second", "number_14", 141414, "xx", 140, "", "Windows", "MOBILE", "tablet", "", '{"subscriber_key": "2_rows_same_sub_tags_only_on_second", "region_key": "number_14"}', datetime.datetime.now()-datetime.timedelta(14), "", "", datetime.datetime.now()-datetime.timedelta(14), "", ""),



                      # #Row with subscriber and tags subscriber_key referencing non existant subscriber.
                      # ("non_matching_row_and_tags_subs", "number_4", 777, "xx", 10, "", "Windows", "MOBILE", "tablet", "", '{"subscriber_key": "non_matching_tags_and_row_subs", "region_key": "north"}', datetime.datetime.now()-datetime.timedelta(1), "", "", datetime.datetime.now()-datetime.timedelta(2), "", "")

                      ]
    dataframe_columns = ['id', 'identifier', 'session_count', 'language', 'timezone', 'game_version', 'device_os', 'device_type', 'device_model', 'ad_id', 'tags', 'last_active', 'playtime', 'amount_spent', 'created_at', 'invalid_identifier', 'badge_count']
    self.sample_intermediate_df = pandas.DataFrame(dataframe_rows, columns=dataframe_columns)
    self.ouu = UpdateOneSignalUsers(self.app_ids, self.username, self.password, self.host, self.db, self.table)


  def test_setup(self):
    self.assertEqual(self.good_id, "cb48c5f8-083e-4893-a330-2162ec73ce73")
    self.assertEqual(self.good_auth, "MTc4NGE3MzItZjZkMC00NjczLWE3NzAtZWYxYjFlM2Q2MDFj")

  def test_get_download_url_200_response(self):
    response = self.ouu.get_download_url(self.good_id, self.good_auth)
    self.assertEqual(response.status_code, 200)
    self.assertIsInstance(response.content, str)
    self.assertTrue("csv_file_url" in json.loads(response.content))

  def test_get_download_url_400_response_wrong_id(self):
    response = self.ouu.get_download_url(self.bad_id, self.good_id)
    self.assertRaises(Exception, response)
    

  def test_get_download_url_400_response_wrong_auth(self):
    response = self.ouu.get_download_url(self.good_id, self.bad_auth)
    self.assertRaises(Exception, response)

  def test_download_file(self):
    self.ouu.download_file(self.good_url)
    self.assertTrue(os.path.isfile("./download.csv.gz"))

  def test_read_gzip(self):
    #test none existant gzip file
    self.assertRaises(IOError, self.ouu.read_gzip, self.bad_filename)
    #test output as pandas text reader
    reader = self.ouu.read_gzip(self.good_filename)
    self.assertIsInstance(reader, pandas.io.parsers.TextFileReader)

  def test_process_frame(self):
    # reader = self.ouu.read_gzip(self.good_filename)
    # for intermediate_df in reader:
    #   print(type(intermediate_df))
    #   print(list(intermediate_df))
    output_df = self.ouu.process_frame(self.sample_intermediate_df.copy(), (self.good_id,))

    # check process frame renames id column as subscriber.
    self.assertFalse("id" in output_df.columns)
    self.assertTrue("subscriber" in output_df.columns)
    self.assertTrue('id' in self.sample_intermediate_df)
    # self.assertEqual(set(self.sample_intermediate_df['id']), set(output_df["subscriber"]))

    #Check rows with no subscriber field are removed
    self.assertEqual(output_df.ix[output_df['subscriber']==""].shape[0], 0)
    self.assertEqual(output_df.ix[output_df['subscriber']!=""].shape[0], 4)
    self.assertFalse("" in output_df['subscriber'])
    self.assertFalse("number_1" in output_df['identifier'])
    self.assertFalse("number_2" in output_df['identifier'])
    self.assertFalse("number_2" in output_df['region'])

     
    #Check rows do not have tags from another row ()
    # print(output_df.ix[(output_df['identifier']!=output_df['region']) & (output_df['region'].isnull() != True)][['subscriber', 'identifier', 'region', 'additional_tags']])
    # print(output_df.ix[(output_df['identifier'][-2:]==output_df['region'][-2:])])
    # print(output_df[['identifier', 'region']])
    # print(output_df.ix[(output_df['identifier']=="number_3")]['region'])
    # print(output_df.ix[(output_df['identifier']=="number_3")]['region'].isnull())

    # print(output_df[output_df.duplicated(["subscriber"])].groupby(('onesignal_created_at')).max())
    # print(output_df[output_df.duplicated(["subscriber"], keep=False)])
    # output_df = output_df.groupby(['subscriber'], sort=False)['onesignal_created_at'].max()
    # output_df.drop_duplicates(subset=['subscriber'], keep='last', inplace=True)
    # print(output_df[['subscriber', 'identifier', 'region', 'additional_tags']])
    # print(output_df[['subscriber', 'identifier', 'region', 'onesignal_created_at']])



@freeze_time("2017-10-30")
class TestUpdateOfferDetails(unittest.TestCase):
  #CREATE METHODS TO INITIALIZE TESTING EXAMPLES, BEFORE EACH TEST CASE

  
  def setUp(self):
    self.good_id = "cb48c5f8-083e-4893-a330-2162ec73ce73"
    self.good_auth = "MTc4NGE3MzItZjZkMC00NjczLWE3NzAtZWYxYjFlM2Q2MDFj"
    self.bad_id = "I DO NOT EXIST"
    self.bad_auth = "I AM NOT AUTHORIZED"
    self.good_url = "https://onesignal.s3.amazonaws.com/csv_exports/cb48c5f8-083e-4893-a330-2162ec73ce73/users_a5f04c879dda67fa7d51327d811d268b_2018-04-11.csv.gz"
    self.bad_url = "THIS IS NOT A URL"
    self.good_filename = "./download.csv.gz"
    self.bad_filename = "THIS FILE DOES NOT EXIST"
    self.username = "test_username"
    self.password = "test_password"
    self.host = "test_host"
    self.db = "test_db"
    self.table = "test_table"

    dataframe_columns = ['id', 'identifier', 'session_count', 'language', 'timezone', 'game_version', 'device_os', 'device_type', 'device_model', 'ad_id', 'tags', 'last_active', 'playtime', 'amount_spent', 'created_at', 'invalid_identifier', 'badge_count']
    self.sample_intermediate_df = pandas.DataFrame(dataframe_rows, columns=dataframe_columns)
    self.oud = UpdateOfferDetails(self.username, self.password, self.host, self.db, self.table)


  def test_setup(self):
    self.assertEqual(self.good_id, "cb48c5f8-083e-4893-a330-2162ec73ce73")

if __name__ == "__main__":

  unittest.main()
