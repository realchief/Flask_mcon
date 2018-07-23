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

import base64
import datetime
import json
import logging
import random
import sys
import time

import psycopg2
import requests
from faker import Faker
from pyfcm import FCMNotification

import push_helper as ph

# Instantiate PyFCM With API Key
push_service = FCMNotification(
    api_key="AAAAkWfmn0k:APA91bFaHkrZQH6X7HlnUVlRXotiGOphHGsI4Uyjto0dh-cZQQsLOjhktEfKnw3niwy_6xO866KXKVyhrqEDVcFnh-Yp7uM2qnekeEiRJM-hCvJcp1zIhIR-aBQNZoYfmHyiecHd_cfG")
# Instantiate logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Create a file handler
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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


def lambda_handler(event, context):
    # logger.info(base64.b64decode(str(json.loads(event)["body"])))
    logger.info('Debug Output: ')
    # logger.info(event.keys())
    # logger.info(event.get('wsgi.input').getvalue())
    content = json.loads(event.get('wsgi.input').getvalue())
    try:
        headline = content["headline"]
    except Exception as e:
        logger.exception('Could not load headline from request')
        headline = None
    try:
        message = content["message"]
    except Exception as e:
        logger.exception('Could not load message from request')
        message = None
    try:
        thumbnail = content["thumbnail"]
    except Exception as e:
        logger.exception('Could not load thumbnail from request')
        thumbnail = None
    try:
        campaign = content["campaign"]
    except Exception as e:
        logger.exception('Could not load campaign from request')
        campaign = None
    try:
        delay = content["send_time"]
    except Exception as e:
        logger.exception('Could not load send_time from request')
        delay = None
    try:
        offer = content["offer"]
    except Exception as e:
        logger.exception('Could not load offer from request')
        offer = None
    try:
        badge = content["badge"]
    except Exception as e:
        logger.exception('Could not load badge from request')
        badge = None
    try:
        image = content["image"]
    except Exception as e:
        logger.exception('Could not load image from request')
        image = None
    try:
        placement = content["placement"]
    except Exception as e:
        logger.exception('Could not load placement from request')
        placement = None
    try:
        registration_ids = list(content["registration_ids"])
    except Exception as e:
        logger.exception('Could not load registration ids from request')
        registration_ids = None
    process_id = random.randint(1, 1000)
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
    if not offer:
        offer = 'default'
    if not image:
        image = ''
    if not badge:
        badge = ph.generateBadge()
    if not offer:
        offer = 'default'
    if not placement:
        placement = 'uUnone' 
    if not registration_ids:
        registration_ids = None
        logger.exception('No registration ids found!')
    logger.info('Campaign: ' + campaign)
    logger.info('Headline: ' + headline)
    logger.info('Message: ' + message)
    logger.info('Thumbnail: ' + thumbnail)
    logger.info('Name: ' + name)
    logger.info('Number of Messages: ' + str(number_messages))
    logger.info('Badge Image: ' + badge)
    requests.post(
        'https://hooks.slack.com/services/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',
        json={
            "text": "Push Notifications Active: {}".format(process_id)})
    fcm_path = 'fcm'
    # Wait for 1-5 minutes, or until scheduled time if defined
    if delay:
        logger.info('Sleeping for: ' + str(delay))
        time.sleep(delay)
    fcm_tracking_url = "http://trk.clickchaser.com/0faecec5-56de-4a85-acb9-49fa4902d071?message={}&headline={}&campaign={}&thumbnail={}&name={}&num_messages={}&badge={}&offer={}&placement={}&path={}".format(
        message, headline, campaign, thumbnail, name, number_messages, badge,
        offer, placement, fcm_path)
    logger.info('FCM Tracking URL:')
    logger.info(fcm_tracking_url)
    # tag = str(datetime.datetime.now().hour)
    # Define Tag for Stacking Purposes
    tag = "fcm"
    extra_kwargs = {
        'renotify': True
    }
    # FCM Sending
    multi_result = None
    try:
        multi_result = push_service.notify_multiple_devices(
            registration_ids=registration_ids,
            message_title=headline,
            message_body=message,
            message_icon=thumbnail,
            click_action=fcm_tracking_url,
            badge=badge,
            tag=tag,
            timeout=20,
            extra_notification_kwargs=extra_kwargs)
        logger.info(multi_result)
    except Exception as e:
        logger.exception(e)
    logger.info('Finished sending push notifications, processing responses')
    requests.post(
        'https://hooks.slack.com/services/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',
        json={"text": "Push Notifications Finished: {} - Success: {} - Failure: {} - Placement: {}".format(process_id,
                                                                                                           multi_result['success'], multi_result['failure'], placement)})
