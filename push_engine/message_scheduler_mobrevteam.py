#!/usr/bin/env python
# -*- coding: ascii -*-

"""
Message Scheduler Deluxe

This is the new message scheduler integration for sending scheduled messages w/ assigned message elements and tracking URLs
via the send-fcm lambda.

"""

from __future__ import print_function
__author__ = 'David McHale (dmchale@mchaleconsulting.net)'
__copyright__ = 'Copyright (c) 2012-2018 David McHale'
__license__ = 'GPL 3.0'
__vcs_id__ = '$Id$'
__version__ = '1.4.0'  # Versioning: http://www.python.org/dev/peps/pep-0386/


import logging
import random
import sys
from datetime import datetime
import multiprocessing
import time

import arrow
import psycopg2
import pycountry
import requests

sys.path.insert(0, '../aux_tools')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create a file handler
handler = logging.FileHandler(
    '/home/ubuntu/push_engine/message_scheduler_mobrevteam.log')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)

traffic_sources = {
    "TrafficStars": "dUAA3y5OGsDCunODuTNs",
    "TrafficHunt": "Cad7abiTEloFNpWt8qHR",
    "ExoClick": "xwrl1gDaaSNrdL7ueAY9",
    "PopAds": "Qt9xZ5sayu46amCoRrsIIw",
    "PopCash": "7Y36ZHPYtvfyn11zy5R4NQ",
    "TrafficHaus": "vvgyDm7Rs8dUQK123zSF",
    "PropellorAds": "U75n0bcuSVjvGGu5o1Xc",
    "Adcash": "1Z7F2oWvSMsZm4XySehF",
    #"Clickadu": "MXMzzGIxSXbKCFnWRdKu",
    "Zeropark": "JysrZjjmUqx9g98xEfld",
    "Unknown": "wFMvpasJrvvO_O4zh5FNbA",
    "Backflow": "wFMvpasJrvvO_O4zh5FNbA",
    #"Reporo": "3LVE9sdseQIEpMGuR7Ud",
    #"TrafficForce": "9V95EwUTJUeU2sIuWQ1S",
    #"TrafficShop": "YMfSahHLWliSJSGLzxrx",
    #"ActiveRevenue": "ousumM7ZqMZ3KdyphH8q",
    "JuicyAds": "ZyL7WtHR4j4l9DaPJqy9",
    #"Tonic": "QkNGHlMcdb12lqefGztO",
    #"TrafficJunky": "JdEPtfXksUCQm3mfCawn",
    #"MediaHub": "1XwkDpBqv2UfUOELchnH",
    #"PlugRush": "I2axTANYbAOloQ3XF5hV",
    #"Bidvertiser": "GyyjcYqG8XLv0dQTNhnZ",
    #"ReachEffect": "LrLYa47F2Wgw3YaX3zCR",
    #"AdXpansion": "XlACoKfo30TuNh9nRi9q",
    #"EroAdvertising": "5ruSix1w3c06s74gqkOM",
    #"Adnium": "Z8mPD7ULj6pXvxK31IsV",
    "Advertizer": "NKR4WyW6HjmEaULZlZDq"
}


def push_worker(headline, message, icon,
                category_name, category_url, placement,
                tag, badge, image, registration_ids):
    logging.info('Spinning up push worker...')
    try:
        logger.info('Creating data object')
        payload = {
            "headline": headline,
            "message": message,
            "icon": icon,
            "category_name": category_name,
            "category_url": category_url,
            "placement": placement,
            "tag": tag,
            "badge": badge,
            "image": image,
            "registration_ids": registration_ids
        }
        try:
            logger.info('Posting data to push_engine lambda')
            response = requests.post(
                'https://9ux58ofhp6.execute-api.us-east-1.amazonaws.com/dev',
                json=payload,
                timeout=10)
            logger.info(response)
            logger.info(response.text)
            logger.info(response.status_code)
        except Exception:
            logger.exception('Push Request Timed Out')
    except Exception:
        logging.exception('Critical error occurred in push worker...')


def check_messages():
    try:
        conn = psycopg2.connect(
            database="pushengine",
            user="root",
            password="VK%Gu?kNdlS{",
            host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com",
            port="5432")
    except Exception as error:
        logger.info('Error connecting to DB', error)
    logger.info('Checking messages')
    start_time = datetime.now()
    # Create a list of active campaigns to send messages w/ translations to
    # by source and geo
    active_campaigns = []
    # Pull all campaigns
    with conn, conn.cursor() as cur:
        sql = "SELECT all_day_notification, start_at, end_at, time_zone, frequency, id, stacking FROM frontend_campaigns WHERE status='t';"
        logger.info(sql)
        cur.execute(sql)
        campaigns = cur.fetchall()
    logger.info(campaigns)
    for campaign in campaigns:
        # if all_day_notification is True, only send in the scheduled hours
        all_day_notification = campaign[0]
        start_at = campaign[1]
        end_at = campaign[2]
        # This is the offset used for calculating whether a given campaign
        # is within it's active scheduled range
        offset = campaign[3]
        frequency = campaign[4]
        campaign_id = campaign[5]
        stacking = campaign[6]
        now = arrow.utcnow().shift(hours=offset)
        # Figure out if it's time to send to campaign
        if all_day_notification:
            if now.time() > start_at and now.time() < end_at:
                logger.info('Inside active sending hours.')
                # Check whether it's the appropriate minute to send in
                if now.time().minute % frequency == 0:
                    logger.info("It's the right minute to send this message.")
                    active_campaigns.append(campaign_id)
                else:
                    logger.info("It's not the right minute to send this message")
                    continue
        else:
            logger.info('All hours active sending hours')
            # Check whether it's the appropriate minute to send in
            if now.time().minute % frequency == 0:
                logger.info("It's the right minute to send this message.")
                active_campaigns.append(campaign_id)
            else:
                logger.info("It's not the right minute to send this message.")
                continue
    for frontend_campaign_id in active_campaigns:
        # pull associated geos
        with conn, conn.cursor() as cur:
            sql = "SELECT geo_id FROM geos_frontend_campaigns WHERE frontend_campaign_id = '{}';".format(
                frontend_campaign_id)
            logger.info(sql)
            cur.execute(sql)
            geos = cur.fetchall()
        logger.info(geos)
        # pull all associated groups
        with conn, conn.cursor() as cur:
            sql = "SELECT frontend_group_id FROM frontend_groups_frontend_campaigns WHERE frontend_campaign_id='{}' and status='t';".format(
                frontend_campaign_id)
            logger.info(sql)
            cur.execute(sql)
            groups = cur.fetchall()
        active_frontend_group_ids = []
        for group in groups:
            active_frontend_group_ids.append(group[0])
        # Retrieve last group sent information
        with conn, conn.cursor() as cur:
            try:
                sql = "SELECT last_group_sent FROM frontend_campaigns WHERE id = {};".format(frontend_campaign_id)
                logger.info(sql)
                cur.execute(sql)
                last_group_sent = cur.fetchone()[0]
            except:
                last_group_sent = None
        # select one of the active groups in campaign to use for URL and
        # message data
        if last_group_sent and len(active_frontend_group_ids) > 1:
            active_frontend_group_ids.remove(last_group_sent)
            active_frontend_group_id = random.choice(active_frontend_group_ids)
        else:
            try:
                active_frontend_group_id = random.choice(active_frontend_group_ids)
            except: 
                active_frontend_group_id = 5 
        # Update campaign with active_frontend_group_id to send
        with conn, conn.cursor() as cur:
            sql = "UPDATE frontend_campaigns set last_group_sent = {} WHERE id = {};".format(active_frontend_group_id,
            frontend_campaign_id)
            logger.info(sql)
            cur.execute(sql)
        # Pull group data
        with conn, conn.cursor() as cur:
            sql = "SELECT frontend_category_id FROM frontend_groups WHERE id='{}' and status='t';".format(
                active_frontend_group_id)
            cur.execute(sql)
            result = cur.fetchone()
        frontend_category_id = result[0]
        # Pull category data for URL
        with conn, conn.cursor() as cur:
            sql = "SELECT url, name FROM frontend_categories WHERE id='{}';".format(
                frontend_category_id)
            cur.execute(sql)
            result = cur.fetchone()
        category_url = result[0]
        category_name = result[1]
        # pull message data
        with conn, conn.cursor() as cur:
            sql = """SELECT headline, content, frontend_badge_id, frontend_badge_tag_id, frontend_icon_id,
            frontend_icon_tag_id, frontend_image_id, frontend_image_tag_id, id FROM frontend_messages WHERE
            frontend_group_id='{}' and status='t' ORDER BY random() LIMIT 1;""".format(active_frontend_group_id)
            cur.execute(sql)
            message_data = cur.fetchone()
        logger.info(message_data)
        headline = message_data[0]
        content = message_data[1]
        frontend_badge_id = message_data[2]
        frontend_badge_tag_id = message_data[3]
        frontend_icon_id = message_data[4]
        frontend_icon_tag_id = message_data[5]
        frontend_image_id = message_data[6]
        frontend_image_tag_id = message_data[7]
        frontend_message_id = message_data[8]
        # Set badges, icons, and images. If tag, select random from tag
        # group
        if frontend_badge_id:
            with conn, conn.cursor() as cur:
                sql = "SELECT frontend_badge_url FROM frontend_badges WHERE id = %s" % (
                    frontend_badge_id)
                logger.info(sql)
                cur.execute(sql)
                frontend_badge = cur.fetchone()[0]
        else:
            if frontend_badge_tag_id:
                with conn, conn.cursor() as cur:
                    sql = "SELECT frontend_badge_id FROM frontend_tags_frontend_badges WHERE frontend_tag_id=%s order by random() limit 1;" % (frontend_badge_tag_id)
                    logger.info(sql)
                    cur.execute(sql)
                    frontend_badge_id = cur.fetchone()[0]
                with conn, conn.cursor() as cur:
                    sql = "SELECT frontend_badge_url FROM frontend_badges WHERE id = %s" % (
                        frontend_badge_id)
                    logger.info(sql)
                    cur.execute(sql)
                    frontend_badge = cur.fetchone()[0]
            else:
                frontend_badge = None
        if frontend_icon_id:
            with conn, conn.cursor() as cur:
                sql = "SELECT frontend_icon_url FROM frontend_icons WHERE id = %s" % (
                    frontend_icon_id)
                logger.info(sql)
                cur.execute(sql)
                frontend_icon = cur.fetchone()[0]
        else:
            if frontend_icon_tag_id:
                with conn, conn.cursor() as cur:
                    sql = "SELECT frontend_icon_id FROM frontend_tags_frontend_icons WHERE frontend_tag_id=%s order by random() limit 1;" % (frontend_icon_tag_id)
                    logger.info(sql)
                    cur.execute(sql)
                    frontend_icon_id = cur.fetchone()[0]
                with conn, conn.cursor() as cur:
                    sql = "SELECT frontend_icon_url FROM frontend_icons WHERE id = %s" % (
                        frontend_icon_id)
                    logger.info(sql)
                    cur.execute(sql)
                    frontend_icon = cur.fetchone()[0]
            else:
                frontend_icon = None
        if frontend_image_id:
            with conn, conn.cursor() as cur:
                sql = "SELECT frontend_image_url FROM frontend_images WHERE id = %s" % (
                    frontend_image_id)
                logger.info(sql)
                cur.execute(sql)
                frontend_image = cur.fetchone()[0]
        else:
            if frontend_image_tag_id:
                with conn, conn.cursor() as cur:
                    sql = "SELECT frontend_image_id FROM frontend_tags_frontend_images WHERE frontend_tag_id=%s order by random() limit 1;" % (frontend_image_tag_id)
                    logger.info(sql)
                    cur.execute(sql)
                    frontend_image_id = cur.fetchone()[0]
                with conn, conn.cursor() as cur:
                    sql = "SELECT frontend_image_url FROM frontend_images WHERE id = %s" % (
                        frontend_image_id)
                    logger.info(sql)
                    cur.execute(sql)
                    frontend_image = cur.fetchone()[0]
            else:
                frontend_image = None
        # Select based on source, language, and geo
        with conn, conn.cursor() as cur:
            sql = "SELECT headline, content, language FROM translations WHERE frontend_message_id = '{}';".format(
                frontend_message_id)
            cur.execute(sql)
            translations = cur.fetchall()
        # Select country names to send to
        with conn, conn.cursor() as cur:
            sql = cur.mogrify(
                "SELECT name FROM geos WHERE id = ANY(%s);", (geos,))
            cur.execute(sql)
            countries = cur.fetchall()
        # Retrieve stacking configuration for campaign: never, by group, or
        # always
        tag = 'default'
        if stacking == 'No':
            tag = 'None'
        if stacking == 'By Group':
            tag = category_name
        if stacking == 'Always':
            tag = 'default'
        # Send by sourcename, then translation to all countries for
        # campaign (Campaign #1 ExoClick English, Campaign #1 ExoClick
        # French, Campaign #1 TrafficHunt English etc)
        for sourcename in traffic_sources:
            for translation in translations:
                try:
                    language_alpha_2 = '%' + \
                        pycountry.languages.get(
                            name=translation[2]).alpha_2 + '%'
                    # Insert send tracking code here
                    with conn, conn.cursor() as cur:
                        sql = cur.mogrify("SELECT count(fcm) FROM fcm_users WHERE language LIKE %s AND sourcename = %s AND country = ANY(%s);", (language_alpha_2,
                             sourcename,
                             countries))
                        logger.info(sql)
                        cur.execute(sql)
                        num_sent = cur.fetchone()[0]
                    if num_sent > 0:
                        with conn, conn.cursor() as cur:
                            sql = """INSERT into frontend_send_reports (sourcename, country, campaign, group_id, category, num_sent) VALUES ('{}', '{}', {}, {}, {}, {});""".format(sourcename, 
                                                              translation[2], 
                                                              frontend_campaign_id, 
                                                              active_frontend_group_id, 
                                                              frontend_category_id, 
                                                              num_sent)
                                                                               
                            logger.info(sql)
                            cur.execute(sql)
                except Exception:
                    logger.exception('Error logging send report')
                
                try:    
                    cursor_name = 'fetch_{}_result'.format(sourcename + '-' + language_alpha_2)
                    with conn, conn.cursor(name=cursor_name) as cur:
                        cur.itersize = 30000
                        sql = cur.mogrify(
                            "SELECT distinct(fcm) FROM fcm_users WHERE language LIKE %s AND sourcename = %s AND country = ANY(%s);",
                            (language_alpha_2,
                             sourcename,
                             countries))
                        print('SQL Statement:', sql)
                        cur.execute(sql)
                        #fcm_registration_ids = cur.fetchall()
                        logger.info('Message Output:')
                        #print('User Count:', fcm_registration_ids)
                        logger.info('Countries: %s', countries)
                        logger.info('Language: %s', translation[2])
                        logger.info('Headline: %s', translation[0])
                        headline = translation[0]
                        logger.info('Content: %s', translation[1])
                        message = translation[1]
                        logger.info('Icon URL: %s', frontend_icon)
                        icon = frontend_icon
                        logger.info('Icon Tag ID: %s', frontend_icon_tag_id)
                        logger.info('Badge URL: %s', frontend_badge)
                        badge = frontend_badge
                        logger.info('Badge Tag ID: %s', frontend_badge_tag_id)
                        logger.info('Image URL: %s', frontend_image)
                        image = frontend_image
                        logger.info('Image Tag ID: %s', frontend_image_tag_id)
                        logger.info('Stacking Status: %s', stacking)
                        logger.info('FCM Tag: %s', tag)
                        logger.info('Traffic Source: %s', sourcename)
                        logger.info(
                            'Traffic Source Placement: %s',
                            traffic_sources[sourcename])
                        placement = traffic_sources[sourcename]
                        logger.info('Placement: %s', placement)
                        logger.info('Category URL: %s', category_url)
                        logger.info('Category Name: %s', category_name)
                        jobs = []
                        while True:
                            try:
                                # consume result over a series of iterations
                                # with each iteration fetching 30000 records
                                records = cur.fetchmany(size=30000)
                                if not records:
                                    logger.info('No records found...')
                                    break
                                logger.info('Records found...')
                                registration_ids = [item[0] for item in records]
                                print(headline, message, icon,
                                  category_name, category_url, placement,
                                  tag, badge, image, len(registration_ids))
                                p = multiprocessing.Process(
                                    target=push_worker,
                                    args=(headline, message, icon,
                                    category_name, category_url, placement,
                                    tag, badge, image, registration_ids))
                                jobs.append(p)
                                p.start()
                            except Exception:
                                logger.exception('Could not create push worker')
                except Exception:
                    logger.exception('Could not send message')
    end_time = datetime.now()
    logger.info('Duration: {}'.format(end_time - start_time))


def test():
    """ Testing Docstring"""
    pass

if __name__ == '__main__':
    logger.info('Retrieving messages')
    check_messages()
    logger.info('All scheduled_messages finished')
    # conn.close()
