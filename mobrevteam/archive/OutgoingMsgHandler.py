#!/usr/bin/python

# OutgoingMsgHandler.py

# Module for sending daily messages to subscribers 
# (and retrying every hour if subscribers have 
# not confirmed receipt.)

"""
Send Message Function: 
Create row in outgoing_messages for each message sent out


Write a sending utility to be run on a recurring basis 
based on whether or not a subscriber has been messaged that day
"""

import datetime
import json
import time

import psycopg2

import xmltodict
from blackbox import Blackbox

# Loop which will retrieve all subscribers which haven't 
# acknowledged message receipt for the day, then send a 
# message through the shortcode they're associated with. 

# Setup API credentials
api_key = "af23046bff4abfc22ffb21fa57c7a9ee" 
# Check under Settings->API Keys in Blackbox
api_signature = "QeWgu7HTnlE+3nOy4mSvZcyumvC1CFTp53OF7/a0o9jDAkbNwxEyyRQHJCUl3+xqsCF6Og/38fnR+cyugaCaBZoeKQZsSKXYfVJ3lQPNhNBcs7QNUWaHb+z7umdlA/OiwVzFWKtY7pwbOAwErkAXkq3Z+74ZWzFYOCfFxiyKKLk=" # Check under Settings->API Keys in Blackbox
# Make API request
blackbox = Blackbox(api_key, api_signature) # Instantiate API library

print('Establishing database connection...')
conn = psycopg2.connect(database="blackbox", 
						user="root", 
						password="agdevil1", 
						host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com", 
						port="5432")

print("Database connection established.")
conn.set_session(autocommit=True)
cur = conn.cursor()

# Select subscriber number, shortcode, and keyword from blackbox.subscribers
sql = "SELECT DISTINCT subscriber, shortcode, keyword from subscribers where active_subscriber = 'true' and sent_today = 'false';"
cur.execute(sql)

# Fetch array of results
rows = cur.fetchall()
# Assign today's datetime
date = datetime.date.today()
print(rows)

for row in rows:
	subscriber = row[0]
	# Generate SMS message with date and subscriber link
	message = "Hujambo! Here are your football highlights for {}: www.footballinfo.net/{}".format(date, subscriber) 
	# Queue message for sending
	blackbox.queue_sms(row[0], message, row[1], row[2])

time.sleep(1)
blackbox.send_sms() # Initiate API call to send messages

# Get API response
# print blackbox.status # View status either (SUCCESS or FAIL)
# print blackbox.message # Returns SMS available (Credits balance)
# print blackbox.description # Returns a status message
# print blackbox.response_xml # Returns full xml response
# print blackbox.response_json # Returns full json response

xml = blackbox.response_xml
response = xmltodict.parse(xml)
for sms in response['response']['content']['messages']['request']['sms']:
    print(sms)
    # Log all outgoing messages and update subscribers.sent_today
    event_type = sms['event']
    recipient = sms['recipient']
    message = sms['message']
    sender = sms['sender']
    keyword = sms['keyword']
    reference = sms['reference']
    status = sms['status']
    status_description = sms['status_description']
    message_date = sms['date']

    # Log outgoing message
    sql = "INSERT INTO outgoing_messages(event, from_num, to_num, keyword, message, reference, status, status_description, date) \
    VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');".format(event_type,
                                                                           sender,
                                                                           recipient,
                                                                           keyword,
                                                                           message,
                                                                           reference,
                                                                           status, 
                                                                           status_description,
                                                                           message_date)
    cur.execute(sql)

    # Update subscribers.sent_today
    if status == 'FAILED':
        sql = "UPDATE subscribers set sent_today = 'false' where subscriber = '{}' and keyword = '{}' and shortcode = '{}';".format(recipient, keyword, sender)
        cur.execute(sql)
    if status == 'SCHEDULED' or status == 'SENT':
        sql = "UPDATE subscribers set sent_today = 'true' where subscriber = '{}' and keyword = '{}' and shortcode = '{}';".format(recipient, keyword, sender)
        cur.execute(sql)

print("Committing changes...")
conn.commit()
print("Changes committed.")

print("Closing database connection...")
conn.close()
print("Connection closed.")
# Close DB connection
