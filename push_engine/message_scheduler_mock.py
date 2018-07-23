#!/usr/bin/env python
# -*- coding: ascii -*-

"""
Message Scheduler

Checks the message scheduler database for outgoing messages
in next hour and spins up push_notification_engine instances
with the required arguments

Checks each hour to intitiate push_notification_engine calls from scheduled messages

Called each hour which checks for messages going out in the next hour and makes a subprocess call to pushEngine.py w/ delay + args for message to send (just set as different from current and then can trigger override if not None)

database pushengine
table
scheduled_messages
id
headline
message
thumbnail
category
recurring
datetime
"""

__author__ = 'David McHale (dmchale@mchaleconsulting.net)'
__copyright__ = 'Copyright (c) 2012-2018 David McHale'
__license__ = 'GPL 3.0'
__vcs_id__ = '$Id$'
__version__ = '1.0.0'  # Versioning: http://www.python.org/dev/peps/pep-0386/

import ast
import json
import logging
import multiprocessing
import sys
from datetime import timedelta

import arrow
import requests

from push_engine import PushEngine

sys.path.insert(0, '../aux_tools')


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create a file handler
handler = logging.FileHandler('/home/ubuntu/push_engine/message_scheduler_mock.log')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)


def get_messages():
    """
    Retrieve messages from push_engine db for next hour
    """
    try:
        logger.info('Checking for scheduled messages in next hour')
        response = requests.get(
            "https://www.mobrevteam.com/get-scheduled-messages")
        logger.info(response.text)
        rows = ast.literal_eval(response.text)
        rows.sort(key=lambda item: item['message_time'], reverse=False)
        logger.info(rows)
    except Exception:
        logger.exception('Failed to retrieve scheduled messages for next hour')
    # Find all rows which are within the accepted delay FIRST and create an array of their delay and message elements, then
    # spin off threads to generate each push engine class
    send_queue = []
    for row in rows:
        try:
            message_time = row['message_time']
            msg_time = arrow.get(message_time, 'HH:mm:ss').time()
            current_time = arrow.now('US/Central').time()
            logger.info('\n Message Time:')
            logger.info(msg_time)
            logger.info('Current Time:')
            logger.info(current_time)
        except Exception:
            logger.exception('Failed to set variables for scheduled message')
        try:
            x = timedelta(
                hours=msg_time.hour,
                minutes=msg_time.minute,
                seconds=msg_time.second)
            y = timedelta(
                hours=current_time.hour,
                minutes=current_time.minute,
                seconds=current_time.second)
            delay = (x - y).total_seconds()
            logger.info("Row Time Delta:")
            logger.info(x)
            logger.info("Current Time Delta:")
            logger.info(y)
            logger.info('Delay:')
            logger.info(delay)
            row['delay'] = delay
        except Exception:
            logger.exception(
                'Failed to calculate time deltas for scheduled message')
        if delay < 60 and delay > 0:
            send_queue.append(row)
    return send_queue


def push_worker(recurring, mid, headline, message, thumbnail, category, delay):
    logging.info('Spinning up push worker...')
    try:
        if 'once' in recurring:
            try:
                logger.info('Removing one time message')
                delete_response = requests.get(
                    "https://www.mobrevteam.com/delete-push?id={}".format(mid))
                logger.info(delete_response.text)
                logger.info(delete_response.status_code)
            except Exception:
                logger.exception('Failed to remove one time message.')
                logger.info('Instantiating engine.')
                # Create the JSON object to pass to the Lambda endpoint
        logger.info('Creating data object')
        payload = {
            "headline": headline,
            "message": message,
            "thumbnail": thumbnail,
            "campaign": category,
            "send_time": "",
            "offer": "",
            "badge": "",
            "image": ""
        }
        try:
            logger.info('Posting data to push_engine lambda')
            response = requests.post(
                'https://d9koy6lyk3.execute-api.us-east-1.amazonaws.com/dev',
                json=payload,
                timeout=300)
            logger.info(response)
        except Exception:
            logger.exception('Push Request Timed Out')
    except Exception:
        logging.exception('Critical error occurred in push worker...')


def test():
    """ Testing Docstring"""
    pass

if __name__ == '__main__':
    logger.info('Retrieving messages')
    try:
        push_queue = get_messages()
    except Exception:
        logger.exception('Could not retrieve messages')
        print('Could not retrieve messages')
    logger.info(push_queue)
    results = []
    jobs = []
    for push in push_queue:
        try:
            p = multiprocessing.Process(
                target=push_worker,
                args=(push['recurring'], push['id'], push['headline'], push['message'], push['thumbnail'], push['category'],
                      push['delay']))
            jobs.append(p)
            p.start()
        except Exception:
            logger.exception('Could not create push worker')
    logger.info('All scheduled_messages finished')
