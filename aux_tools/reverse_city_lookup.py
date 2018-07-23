import psycopg2
from geopy.geocoders import Nominatim
import time
language = 'en'
geolocator = Nominatim(user_agent="MobRev")

conn = psycopg2.connect(
    database="pushengine",
    user="root",
    password="VK%Gu?kNdlS{",
    host="blackbox.c5oicakkxsxn.us-west-2.rds.amazonaws.com",
    port="5432")
cur = conn.cursor()
sql = "select country from fcm_users group by country;"
cur.execute(sql)
region_list = [item[0] for item in cur.fetchall()]

for region in region_list:
	try:
		if region != '':
			location = geolocator.geocode(query=region, language=language)
			time.sleep(1)
			country = location.raw['display_name'].split(',')[-1].lstrip()
			print('Region:', region)
			print('Location:', location.address)
			print('Country:', country)
		else:
			country = 'United States'
		if country == 'United States of America':
			country = 'United States'
		if country != region:
			sql = "UPDATE fcm_users set country = '%s' where country = '%s'" % (country, region)
			print('SQL:', sql)
			cur.execute(sql)
			conn.commit()
		else:
			print('Country and Region are the same, no change needed.')
	except:
		print('Could not save region: ', region)
