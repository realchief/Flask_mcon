import unittest
import requests
import sys
import json
import os
import pandas
import datetime
import inspect
# import unittest, sys, json, datetime, pymysql, keepaAPI
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
import push_engine
from mock import patch, Mock, MagicMock
import ast
import re
from freezegun import freeze_time




@freeze_time("2017-10-30")
class TestPushEngien(unittest.TestCase):
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
