#!/usr/bin/python

# ResetSentStatus.py

# Module for resetting sent_today status for all subscribers

"""
At the beginning of the day, set sent_today to 0 for all subscribers.
Attempt to send from 8am to 8pm
"""

import psycopg2

print('Establishing database connection...')
conn = psycopg2.connect(database="blackbox", 
						user="root", 
						password="agdevil1", 
						host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com", 
						port="5432")

print("Database connection established.")
cur = conn.cursor()

# Update subscribers.sent_today
sql = "UPDATE subscribers set sent_today = 'false';"
cur.execute(sql)

print("Committing changes...")
conn.commit()
print("Changes committed.")

print("Closing database connection...")
conn.close()
print("Connection closed.")
