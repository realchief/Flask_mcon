"""
Module for monitoring and deleting duplicate FCM IDs from the fcm_users table to speed up DB commands and reduce risk of duplicate sendings (this is already covered by a distinct clause in the send and is an additional cautionary step)
"""

import psycopg2
conn = psycopg2.connect(
    database="pushengine",
    user="root",
    password="VK%Gu?kNdlS{",
    host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com",
    port="5432")
cur = conn.cursor()
sql = """
DELETE
FROM
fcm_users a
USING fcm_users b
WHERE
a.id < b.id
AND a.fcm = b.fcm;
"""
cur.execute(sql)
