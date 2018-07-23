#!/usr/bin/python
# ResetSentStatus.py
# Module for checking user expirations

"""
At the beginning of the day, set sent_today to 0 for all subscribers.
Attempt to send from 8am to 8pm
"""

import psycopg2

print('Establishing database connection...')
conn = psycopg2.connect(database="jestflix", 
						user="root", 
						password="agdevil1", 
						host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com", 
						port="5432")

print("Database connection established.")
cur = conn.cursor()

# Update subscribers.sent_today
sql = "UPDATE public.user SET active_subscriptio=False WHERE expiration_date <= timeofday()::DATE;"
cur.execute(sql)

print("Committing changes...")
conn.commit()
print("Changes committed.")

print("Closing database connection...")
conn.close()
print("Connection closed.")
