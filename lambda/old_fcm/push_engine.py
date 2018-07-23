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
__version__ = '1.5.4'  # Versioning: http://www.python.org/dev/peps/pep-0386/

import json
import logging
import os
import random
import sys
import time

import psycopg2
import requests
from faker import Faker
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request, url_for)
from pyfcm import FCMNotification

import push_helper as ph

app = Flask(__name__)


# Instantiate PyFCM With API Key
push_service = FCMNotification(
    api_key="AAAAkWfmn0k:APA91bFaHkrZQH6X7HlnUVlRXotiGOphHGsI4Uyjto0dh-cZQQsLOjhktEfKnw3niwy_6xO866KXKVyhrqEDVcFnh-Yp7uM2qnekeEiRJM-hCvJcp1zIhIR-aBQNZoYfmHyiecHd_cfG")

# Establish connection to Postgres RDS
conn = psycopg2.connect(
    database="pushengine",
    user="root",
    password="VK%Gu?kNdlS{",
    host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com",
    port="5432")
conn.autocommit = True
cur = conn.cursor()

# Define PushEngine class
@app.route("/", methods=["GET", "POST"])
def default():
    content = request.get_json()
    try:
        headline = content["headline"]
    except Exception, e:
        print('Could not load headline from request')
        headline = None
    try:
        message = content["message"]
    except Exception, e:
        print('Could not load message from request')
        message = None
    try:
        thumbnail = content["thumbnail"]
    except Exception, e:
        print('Could not load thumbnail from request')
        thumbnail = None
    try:
        campaign = content["campaign"]
    except Exception, e:
        print('Could not load campaign from request')
        campaign = None
    try:
        delay = content["send_time"]
    except Exception, e:
        print('Could not load send_time from request')
        delay = None
    try:
        offer = content["offer"]
    except Exception, e:
        print('Could not load offer from request')
        offer = None
    try:
        badge = content["badge"]
    except Exception, e:
        print('Could not load badge from request')
        badge = None
    try:
        image = content["image"]
    except Exception, e:
        print('Could not load image from request')
        image = None
    # Check whether push engine sending active
    print('Checking send_status...')
    response = requests.get('http://mobrevteam.com/kill-switch-status')
    send_status = eval(response.content)
    if send_status:
        print('Send status is true, continuing with push.')
    else:
        print('Send status is false, aborting sending.')
        sys.exit(0)
    # Set time in seconds for messages to live
    ttl = 2419200
    # Set priority of message (10 will buzz phone, anything less will not)
    priority = 10
    # Set Locale for Faker
    fake = Faker('en_US')
    name = fake.first_name_female()
    number_messages = random.randint(2, 7)
    headline_type = ph.generateHeadlineType()
    if not campaign:
        campaign = ph.generateCampaignType()
    if not thumbnail:
        thumbnail = ph.generateThumbnail()
    if not message:
        message = ph.generateMessage(
            number_messages, headline_type, name)
    if not headline:
        headline = ph.generateHeadline()
    if not image:
        image = ''
    if not badge:
        badge = ph.generateBadge()
    if not offer:
        offer = 'old-fcm'
    print('Campaign: ' + campaign)
    print('Headline: ' + headline)
    print('Message: ' + message)
    print('Thumbnail: ' + thumbnail)
    print('Name: ' + name)
    print('Number of Messages: ' + str(number_messages))
    print('Badge Image: ' + badge)
    request_number = 0
    requests.post(
        'https://hooks.slack.com/services/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',
        json={
            "text": "Push Notifications Active: {}".format(os.getpid())})
    # Define offer group based on OneSignal tag
    fcm_path = 'test'
    # Define subscriber_key based on OneSignal tag
    # Wait for 1-5 minutes, or until scheduled time if defined
    if delay:
        print('Sleeping for: ' + str(delay))
        time.sleep(delay)
    # for id in app_ids, loop through and send a message
    traffic_sources = {
        "TrafficStars": "dUAA3y5OGsDCunODuTNs",
        "TrafficHunt": "Cad7abiTEloFNpWt8qHR",
        "ExoClick": "xwrl1gDaaSNrdL7ueAY9",
        #"PopAds": "Qt9xZ5sayu46amCoRrsIIw",
        #"PopCash": "7Y36ZHPYtvfyn11zy5R4NQ",
        #"TrafficHaus": "vvgyDm7Rs8dUQK123zSF",
        #"PropellorAds": "U75n0bcuSVjvGGu5o1Xc",
        #"Adcash": "1Z7F2oWvSMsZm4XySehF",
        #"Clickadu": "MXMzzGIxSXbKCFnWRdKu",
        #"Zeropark": "JysrZjjmUqx9g98xEfld",
        "Unknown": "wFMvpasJrvvO_O4zh5FNbA",
        "Backflow": "wFMvpasJrvvO_O4zh5FNbA",
        #"Reporo": "3LVE9sdseQIEpMGuR7Ud",
        #"TrafficForce": "9V95EwUTJUeU2sIuWQ1S",
        #"TrafficShop": "YMfSahHLWliSJSGLzxrx",
        #"ActiveRevenue": "ousumM7ZqMZ3KdyphH8q",
        #"JuicyAds": "ZyL7WtHR4j4l9DaPJqy9",
        #"Tonic": "QkNGHlMcdb12lqefGztO",
        #"TrafficJunky": "JdEPtfXksUCQm3mfCawn",
        #"MediaHub": "1XwkDpBqv2UfUOELchnH",
        #"PlugRush": "I2axTANYbAOloQ3XF5hV",
        #"Bidvertiser": "GyyjcYqG8XLv0dQTNhnZ",
        #"ReachEffect": "LrLYa47F2Wgw3YaX3zCR",
        #"AdXpansion": "XlACoKfo30TuNh9nRi9q",
        #"EroAdvertising": "5ruSix1w3c06s74gqkOM",
        #"Adnium": "Z8mPD7ULj6pXvxK31IsV",
        #"Advertizer": "NKR4WyW6HjmEaULZlZDq"
    }
    # Message Sending Loop
    for source in traffic_sources.keys():
        print('Source: ' + source)
        placement = traffic_sources[source]
        # Use for selecting distinct IPs (though may be multiple users per IP so use with caution)
        # select distinct on (ip) fcm from fcm_users where sourcename = 'PopCash';
        print('Selecting users from source %s' % source)
        fcm_sql = "SELECT fcm FROM fcm_users WHERE sourcename = '%s'" % source
        cur.execute(fcm_sql)
        fcm_registration_ids = [item[0] for item in cur.fetchall()]
        # print(fcm_registration_ids)
        fcm_tracking_url = "http://trk.clickchaser.com/0faecec5-56de-4a85-acb9-49fa4902d071?message={}&headline={}&campaign={}&thumbnail={}&name={}&num_messages={}&badge={}&offer={}&placement={}&path={}".format(
            message, headline, campaign, thumbnail, name, number_messages, badge,
            offer, placement, fcm_path)
        print('FCM Tracking URL:')
        print(fcm_tracking_url)
        #tag = str(datetime.datetime.now().hour)
        tag = "fcm"
        # FCM Sending
        try:
            multi_result = push_service.notify_multiple_devices(
                registration_ids=fcm_registration_ids,
                message_title=headline,
                message_body=message,
                message_icon=thumbnail,
                click_action=fcm_tracking_url,
                badge=badge,
                tag=tag)
            print(multi_result)
        except Exception as e:
            print(e)
    print('Finished sending push notifications, processing responses')
    requests.post(
        'https://hooks.slack.com/services/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',
        json={"text": "Push Notifications Finished: {}".format(os.getpid())})

