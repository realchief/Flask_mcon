#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coding: utf8

"""
Push Notification Engine
Schedule a cron job to run me at 8,9,10pm, 1,2,3pm and 6,7,8pm
This module generates message templates which are then sent out to OneSignal for sending
Additionally it records the message components in postgresql
It then polls voluum (tracking platform) and onesignal (messaging platform)
to attach performance data to those message components
"""

__author__ = 'McHale Consulting (dmchale@mchaleconsulting.net)'
__copyright__ = 'Copyright (c) 2018 McHale Consulting'
__license__ = 'New-style BSD'
__vcs_id__ = '$Id$'
__version__ = '1.4.3'  # Versioning: http://www.python.org/dev/peps/pep-0386/

import json
import logging
import os
import random
import sys
import time
import boto

import psycopg2
import requests
from faker import Faker
from twisted.internet import defer
from twisted.internet.task import react
from txrequests import Session

import push_helper as ph

session = Session(maxthreads=10)
responses = []

# Instantiate logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Create a file handler
handler = logging.FileHandler('/home/ubuntu/push_engine/push_engine.log')
handler.setLevel(logging.ERROR)

# Create a logging format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(handler)

# Establish connection to Postgres RDS
logger.info('Establishing database connection...')
conn = psycopg2.connect(
    database="pushengine",
    user="root",
    password="VK%Gu?kNdlS{",
    host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com",
    port="5432")
cur = conn.cursor()
logger.info("Database connection established.")

# Define PushEngine class


class PushEngine:

    def __init__(self, headline=None, message=None,
                 thumbnail=None, campaign=None, send_time=None):
        # Check whether push engine sending active
        logger.info('Checking send_status...')
        response = requests.get('http://mobrevteam.com/kill-switch-status')
        send_status = eval(response.content)
        if send_status:
            logger.info('Send status is true, continuing with push.')
        else:
            logger.info('Send status is false, aborting sending.')
            sys.exit(0)
        # Set time in seconds for messages to live
        self.ttl = 2419200
        # Set priority of message (10 will buzz phone, anything less will not)
        self.priority = 10
        # Set Locale for Faker
        self.fake = Faker('en_US')
        self.name = self.fake.first_name_female()
        self.number_messages = random.randint(2, 7)
        self.headline_type = ph.generateHeadlineType()
        if not campaign:
            self.campaign = ph.generateCampaignType()
        else:
            self.campaign = campaign
        if not thumbnail:
            self.thumbnail = ph.generateThumbnail()
        else:
            self.thumbnail = thumbnail
        if not message:
            self.message = ph.generateMessage(
                self.number_messages, self.headline_type, self.name)
        else:
            self.message = message
        if not headline:
            self.headline = ph.generateHeadline()
        else:
            self.headline = headline
        if not send_time:
            self.delay = None
            #self.delay = random.randint(60, 300)
        else:
            self.delay = send_time
        self.image = ''
        self.badge = ph.generateBadge()
        self.offer = 'default'

        logger.info('Campaign: ' + self.campaign)
        logger.info('Headline: ' + self.headline)
        logger.info('Message: ' + self.message)
        logger.info('Thumbnail: ' + self.thumbnail)
        logger.info('Name: ' + self.name)
        logger.info('Number of Messages: ' + str(self.number_messages))
        logger.info('Badge Image: ' + self.badge)

    def main(self):
        request_number = 0
        requests.post(
            'https://hooks.slack.com/services/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',
            json={
                "text": "Push Notifications Active: {}".format(os.getpid())})
        # Define offer group based on OneSignal tag
        path = '{{ offer_group_key | default : "1" }}'
        # Define subscriber_key based on OneSignal tag
        subscriber_key = '{{ subscriber_key | default: "unknown" }}'

        # Wait for 1-5 minutes, or until scheduled time if defined
        if self.delay:
            logger.info('Sleeping for: ' + str(self.delay))
            time.sleep(self.delay)

        # for id in app_ids, loop through and send a message
        app_ids = {
            "aa50f2ae-77c7-4b01-97dc-b67775371a27":
            "NmQ5NGRhODAtZDU5NS00OTgyLThjNDItNTVkZTVjNTdhZjA1",
            "650bceb6-cb6d-4b92-8a03-25d6c224efb1":
            "MDZiMWVkNWItNzNkZC00ODY4LWJkZTMtNWViYTk0ZWE1NTA0",
            "49db6ad5-8436-4fd6-b73d-d8b666c22865":
            "ZWMxMGI5MDAtMTQ0Ni00YjVlLTg4MzAtZGNlZThmZmYwYjg3",
            "cb48c5f8-083e-4893-a330-2162ec73ce73":
            "MTc4NGE3MzItZjZkMC00NjczLWE3NzAtZWYxYjFlM2Q2MDFj",
            "63fd492e-472b-448b-b764-b9325c56ec65":
            "OTk1M2MwMTktYWYzMC00ZDQ5LTlhN2QtNWVjNjgxMjViN2Jl",
            "d6ad3116-9a9e-4b08-a986-a68a0a094086":
            "ODZkM2FmZGYtOWJmNi00N2ZiLThjMjYtODdiNmExNjYyMTgz",
            "12a15cae-3ffd-4265-97e2-99ebd07a7472":
            "ZjQ5MmE3MzMtODBlNi00MjU4LTkzMmQtZjkwYzM0MmIyNjM4",
            "48075596-a4e5-4b88-8a27-982cc4eca9a2":
            "OWQ4YmJiMWUtMTRhMS00ZDA1LTljYTQtMWRhOTY5ZjNiMGE3",
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
            "26d0af0e-1eb1-4773-8df5-172b2382bccb":
            "ZGU2ZDc1OTUtOTg0Ni00MTY3LWExNjUtMmVkMzMxNDhkMjE1",
            "0dd61234-7d87-4955-93e6-ac0c060934d1":
            "ODljNTVkZjEtOGFjOS00MTlkLTg0OGMtN2FkNGExODllZjE5",
            "64474374-1bbb-4203-9384-3e549de62399":
            "ODUzN2ViMTQtNGI5OS00YTY5LWExNmEtNTlhZGRlYjY3ZjM4",
            "83b27f34-6ca8-4411-9d4b-90f05153a552":
            "NTZiOGJiZDYtMWRmMC00NmNkLWJiNDktZTE3MGRlM2Y0MDRm",
            "2bc2b31f-f454-4167-bebc-0b98b2e9fef0":
            "OTY5OThlNzYtOGYzYy00NzNmLTkwNzQtNmZhZjdkNDZhOTgx",
            "731b88df-dac6-4bcc-ac52-ef402241ea26":
            "NjIyYzQ0NzItODhlMi00YmU2LWIxMDQtZDRjYWQ0YzMzNDlh",
            "8f42fbfe-7b2f-4903-a50d-f0813b831be0":
            "ODExYmZjMWQtOWQ4Ny00MDY0LTg2MjItNzI5YTRjZDk5NDFk",
            "e6d33370-65c6-4c05-b8ad-de61944c02f5":
            "M2U0NmY0NmUtZDJiOC00NTFmLWIxMWItNDU0MjE3ZTM2YTZj",
            "83b64539-0300-44cd-a37f-bd2414a67bc6":
            "ZDZmNjZiZWEtMmZlOS00ZGNhLTg5NTMtMWJmMmNhNjlkZTUw",
            "4c3bfb3d-54c8-4e4b-a82f-ab35c6dac4a5":
            "NGUwYTkwNDYtZThkOS00MTdhLWI3YmEtNzBjMWNjYjM1ZjVm",
            "aa50f2ae-77c7-4b01-97dc-b67775371a27":
            "NmQ5NGRhODAtZDU5NS00OTgyLThjNDItNTVkZTVjNTdhZjA1",
            "6c25ab3a-53a2-48f5-b71c-59bdef510d33":
            "MzQxYjEzZGYtOWRlMS00NmE4LTgxZGMtZGMyNDM5YjZiYTE3"
        }
        traffic_sources = {
            "TrafficHunt": "Cad7abiTEloFNpWt8qHR",
            "ExoClick": "xwrl1gDaaSNrdL7ueAY9",
            "TrafficStars": "dUAA3y5OGsDCunODuTNs",
            "PopAds": "Qt9xZ5sayu46amCoRrsIIw",
            "PopCash": "7Y36ZHPYtvfyn11zy5R4NQ",
            "TrafficHaus": "vvgyDm7Rs8dUQK123zSF",
            "PropellorAds": "U75n0bcuSVjvGGu5o1Xc",
            "Adcash": "1Z7F2oWvSMsZm4XySehF",
            "Clickadu": "MXMzzGIxSXbKCFnWRdKu",
            "Zeropark": "JysrZjjmUqx9g98xEfld",
            "Unknown": "wFMvpasJrvvO_O4zh5FNbA",
            "Backflow": "wFMvpasJrvvO_O4zh5FNbA",
            "Reporo": "3LVE9sdseQIEpMGuR7Ud",
            "TrafficForce": "9V95EwUTJUeU2sIuWQ1S",
            "TrafficShop": "YMfSahHLWliSJSGLzxrx",
            "ActiveRevenue": "ousumM7ZqMZ3KdyphH8q",
            "JuicyAds": "ZyL7WtHR4j4l9DaPJqy9",
            "Tonic": "QkNGHlMcdb12lqefGztO",
            "TrafficJunky": "JdEPtfXksUCQm3mfCawn",
            "MediaHub": "1XwkDpBqv2UfUOELchnH",
            "PlugRush": "I2axTANYbAOloQ3XF5hV",
            "Bidvertiser": "GyyjcYqG8XLv0dQTNhnZ",
            "ReachEffect": "LrLYa47F2Wgw3YaX3zCR",
            "AdXpansion": "XlACoKfo30TuNh9nRi9q",
            "EroAdvertising": "5ruSix1w3c06s74gqkOM",
            "Adnium": "Z8mPD7ULj6pXvxK31IsV",
            "Advertizer": "NKR4WyW6HjmEaULZlZDq"
        }
        """
        traffic_sources = {
            "Unknown": "wFMvpasJrvvO_O4zh5FNbA"
        }
        """
        notification_id_list = {}
        # Message Sending Loop
        for source in traffic_sources.keys():
            request_number += 1
            if request_number % 1 == 0:
                logger.info('Pausing for 1s to avoid OneSignal rate-limiting')
                time.sleep(1)
            logger.info('Source: ' + source)
            placement = traffic_sources[source]
            traffic_filter = [
                {"field": "tag",
                 "key": "maxcleaner",
                 "relation": "not_exists"},
                {"field": "tag",
                 "key": "sourcename_key",
                 "relation": "=",
                 "value": "{}".format(source)}]
            if source is 'Backflow':
                traffic_filter = [
                    {"field": "tag",
                     "key": "maxcleaner",
                     "relation": "not_exists"},
                    {"field": "tag",
                     "key": "sourcename_key",
                     "relation": "=",
                     "value": "Backflow"},
                    {"operator": "OR"},
                    {"field": "tag",
                     "key": "sourcename_key",
                     "relation": "=",
                     "value": "Push Backflow"},
                    {"operator": "OR"},
                    {"field": "tag",
                     "key": "sourcename_key",
                     "relation": "=",
                     "value": "Push Traffic - Backflow"}]
            if source is 'Unknown':
                traffic_filter = [
                    {"field": "tag",
                     "key": "maxcleaner",
                     "relation": "not_exists"},
                    {"field": "tag",
                     "key": "sourcename_key",
                     "relation": "=",
                     "value": "&countryname=United States"},
                    {"operator": "OR"},
                    {"field": "tag",
                     "key": "sourcename_key",
                     "relation": "not_exists"},
                    {"operator": "OR"},
                    {"field": "tag",
                     "key": "sourcename_key",
                     "relation": "=",
                     "value": "Push"},
                    {"operator": "OR"},
                    {"field": "tag",
                     "key": "sourcename_key",
                     "relation": "=",
                     "value": "&countryname=United Kingdom"},
                    {"operator": "OR"},
                    {"field": "tag",
                     "key": "sourcename_key",
                     "relation": "=",
                     "value": "&amp;countryname=United States"}]

            tracking_url = "http://trk.clickchaser.com/0faecec5-56de-4a85-acb9-49fa4902d071?message={}&headline={}&campaign={}&thumbnail={}&name={}&num_messages={}&badge={}&offer={}&placement={}&path={}&subscriber_key={}".format(
                self.message, self.headline, self.campaign, self.thumbnail, self.name, self.number_messages, self.badge,
                self.offer, placement, path, subscriber_key)
            logger.info('Sending Affiliate Link')
            logger.info('Tracking URL:')
            logger.info(tracking_url)
            for onesignal_app_id in app_ids:
                rest_authorization = "Basic {}".format(
                    app_ids[onesignal_app_id])
                header = {"Content-Type": "application/json; charset=utf-8",
                          "Authorization": rest_authorization}
                payload = {"app_id": onesignal_app_id,
                           #"included_segments": ["All"],
                           "ttl": self.ttl,
                           "url": tracking_url,
                           "filters": traffic_filter,
                           "contents": {"en": "{}".format(self.message)},
                           #"contents": contents,
                           "headings": {"en": "{}".format(self.headline)},
                           #"headings": headings,
                           "chrome_web_icon": self.thumbnail,
                           "chrome_web_badge": self.badge,
                           #"priority": priority,
                           "large_icon": self.thumbnail,
                           "small_icon": self.thumbnail,
                           "collapse_id": "collapse"}
                logger.info('Payload:')
                logger.info(payload)
                # responses.append(session.post("https://onesignal.com/api/v1/notifications",
                #                    headers=header,
                #                    data=json.dumps(payload)))
                try:
                    result = requests.post("https://onesignal.com/api/v1/notifications",
                                           headers=header,
                                           data=json.dumps(payload))
                    push_results = result.json()
                    logger.info(result.json())
                    notificationId = push_results['id']
                    num_user_sent = push_results['recipients']
                    total_recipients += num_user_sent
                except Exception as error:
                    logger.info(
                        'Error retrieving results of push notification')
                    notificationId = 'unknown'
                    num_user_sent = 0
                logger.info('Status Code: ' + str(result.status_code))
                logger.info('Response Text: ' + str(result.text))
                logger.info('Notification ID: ' + str(notificationId))
                logger.info('Users Reached: ' + str(num_user_sent))
        #logger.info('Finished sending push notifications, processing responses')
        requests.post(
            'https://hooks.slack.com/services/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',
            json={"text": "Push Notifications Finished: {}".format(os.getpid())})
        # react(process_responses)


@defer.inlineCallbacks
def process_responses(reactor):
    time.sleep(10)
    total_recipients = 0
    for response in responses:
        result = yield response
        try:
            push_results = result.json()
            logger.info(result.json())
            notificationId = push_results['id']
            num_user_sent = push_results['recipients']
            total_recipients += num_user_sent
        except Exception as error:
            logger.info(
                'Error retrieving results of push notification')
            notificationId = 'unknown'
            num_user_sent = 0
        logger.info('Status Code: ' + str(result.status_code))
        logger.info('Response Text: ' + str(result.text))
        logger.info('Notification ID: ' + str(notificationId))
        logger.info('Users Reached: ' + str(num_user_sent))
    # End Message Sending Loop
    logger.info(
        'Total Recipients for PID {}: {}'.format(
            os.getpid(),
            total_recipients))
    session.close()


def test():
    """ Testing Docstring"""
    logger.info("Test Successful")
    pass

if __name__ == '__main__':
    push = PushEngine()
    push.main()
