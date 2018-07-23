# virus_total scan for all below, email alert as Lander Status: FLAGGED to
# andrew and self

import time
import psycopg2
import requests
import os
import sys

api_key = "23ab38afbec04a23e2e755b5a46491fbc8180438f14cf7b647aaae0d7f99e799"


def send_positive_email(url, permalink):
    return requests.post(
        "https://api.mailgun.net/v3/mg.mchaleconsulting.net/messages",
        auth=(
            "api",
            "key-4770babc9ef75c04ad1152983f6ef4a8"),
        data={
            "from": "MCON Monitor <postmaster@mg.mchaleconsulting.net>",
            "to": [
                "andrew@mobrevmedia.com",
                "dmchale@mchaleconsulting.net"],
            "subject": "Lander Status: {} Changed to FLAGGED".format(url),
            "text": "Lander Status for URL: {} has changed. Scan Results: {}".format(
                    url,
                permalink)})


monitored_domains = []
scan_queue = []
try:

    host = os.environ["PUSH_DB_HOST"]
    db = os.environ["PUSH_DB"]
    username = os.environ["PUSH_DB_USER"]
    password = os.environ["PUSH_DB_PASSWD"]

    conn = psycopg2.connect(database=db, user=username, password=password, host=host, port="5432")
    cur = conn.cursor()

    cur.execute("SELECT url FROM public.virus_checks WHERE monitor_active = True ORDER BY id ASC;")
    monitored_domains = cur.fetchall()
except psycopg2.Error as e:
    print("Error occurred")
    conn.close()
    sys.exc_info()[1]


print('Queuing Scans for Landers')
for target_domain in monitored_domains:
    try:
        params = {'apikey': api_key, 'url': target_domain}
        response = requests.post(
            'https://www.virustotal.com/vtapi/v2/url/scan',
            params=params)
        time.sleep(15)
    except Exception as error:
        print(error)
        print('Queuing scan failed for ' + target_domain)

# Retrieving scans
print('Retrieving Scans for Landers')
for target_domain in monitored_domains:
    try:
        params = {'apikey': api_key, 'resource': target_domain}
        response = requests.get(
            'https://www.virustotal.com/vtapi/v2/url/report',
            params=params)
        print(response.status_code)
        print(response.text)
        print(response.json())
        response_data = response.json()
        # Number of positives
        positives = response_data['positives']
        # URL being scanned
        url = response_data['url']
        # URL for scan
        permalink = response_data['permalink']
        if positives > 0:
            # Send email to andrew@mobrevmedia.com /
            # dmchale@mchaleconsulting.net
            send_positive_email(url, permalink)
        time.sleep(15)
    except Exception as error:
        print(error)
        print('Retrieving scan failed for ' + target_domain)
