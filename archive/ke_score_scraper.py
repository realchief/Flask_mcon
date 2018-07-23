"""
Microservice for connecting to livescore,
retrieving a full page screenshot,
and cropping into mobile-ready sore snapshot
"""
import datetime
import os
import sys
import time
import unittest
from bs4 import BeautifulSoup as bs
import subprocess

import boto3
from botocore.client import Config
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

import util


class Test(unittest.TestCase):
    """ Demonstration: Get Chrome to generate fullscreen screenshot """

    def setUp(self):
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36")

        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = user_agent
        dcap["phantomjs.page.settings.javascriptEnabled"] = True

        self.browser = webdriver.PhantomJS(
            service_log_path=os.path.devnull,
            executable_path="/home/ubuntu/phantomjs",
            service_args=['--ignore-ssl-errors=true'],
            desired_capabilities=dcap)

    def tearDown(self):
        self.browser.quit()

    def test_retrieve_score_html(self):
	""" 
	Generate HTML template for footballinfo.net every ten minutes
	"""
        url = "http://www.flashscore.com"
        path = '/home/ubuntu/tmp/'
        country = 'KE'
        sport = 'soccer'
        now = datetime.datetime.now()
	today_date = str(now.year) + '-' + str(now.month) + '-' + str(now.day)
        
	# Retrieve score page
	self.browser.get(url)
	time.sleep(5)
        
	# Find score container
        element = self.browser.find_element_by_id('fs')
	
	# Create prettified Score HTML
	score_html = bs(element.get_attribute('innerHTML'), "lxml")
	
	# Modify width of all col elements to 10%
	for col in score_html.find_all("col"):
	    col['width'] = '10%'

	# Modify width of all table elements to 100%
	for table in score_html.find_all("table"):
	    table['width'] = '100%'

	# Add table-striped to table-main
	for div in score_html.find_all("div", {'class':'table-main'}):
	    div['class'] = 'table-main table-striped'

	# Clean td.head_aa
	for td in score_html.find_all("td", {'class':'head_aa'}):
	    td.decompose()

	# Clean td.icons
	for td in score_html.find_all("td", {'class':'icons'}): 
	    td.decompose()

	# Clean td.comparison
	for td in score_html.find_all("td", {'class':'comparison'}): 
	    td.decompose()

	# Clean span.stats
	for span in score_html.find_all("span", {'class':'stats'}): 
	    span.decompose()

	# Clean span.stats-draw
	for span in score_html.find_all("span", {'class':'stats-draw'}): 
	    span.decompose()

	# Clean head tags
	for head in score_html.find_all("head"):
	    head.decompose()	
	
	score_html = score_html.prettify()

	# Clear contents of template	
	open('/home/ubuntu/soccer-news-serv/templates/{}-scores.html'.format(today_date), 'w').close()
	print('Template cleared.')
	
	# Save updates contents of template in UTF-8
	with open('/home/ubuntu/soccer-news-serv/templates/{}-scores.html'.format(today_date), 'a') as f:
	    f.write(score_html.encode('utf-8'))
	
	print('Template updated successfully.')

	print('Restarting apache gracefully to update templates...')
	subprocess.call(['sudo', 'apachectl', '-k', 'graceful'])
	print('Apache restarted gracefully.')
	
"""
    def test_get_sport_screenshot(self):
        ''' Generate document-height screenshot '''
        url = "http://www.flashscore.com"
        path = '/home/ubuntu/tmp/'
        country = 'KE'
        sport = 'soccer'
        now = datetime.datetime.now()
	today_date = str(now.year) + '-' + str(now.month) + '-' + str(now.day)
        filetype = '.jpg'
        sport_snapshot = country + '-' + sport + '-' + \
            str(now.year) + '-' + str(now.month) + '-' + \
            str(now.day) + '-' + str(now.hour) + filetype
        self.browser.get(url)
	
        self.browser.set_window_size(1400, 15000)
        
	time.sleep(10)
        
	util.fullpage_screenshot(self.browser, path + sport_snapshot)

        # now that we have the preliminary stuff out of the way time to get
        # that image :D
        # find part of the page you want image of
        element = self.browser.find_element_by_id('fs')
	print element

        location = element.location
	print location
        size = element.size
	print size
        # uses PIL library to open image in memory
        image_input = Image.open(path + sport_snapshot)
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']

	print left
	print top
	print right
	print bottom

        # defines crop points and crops
        image_input = image_input.crop((left, top, right - 135, bottom))
	# loads in header image
	header_input = Image.open(path + 'ke-soccer-header.jpg')

        (width1, height1) = header_input.size
    	(width2, height2) = image_input.size

    	result_width = max(width1, width2)
    	result_height = height1 + height2

    	result = Image.new('RGB', (result_width, result_height))
    	result.paste(im=header_input, box=(0, 0))
    	result.paste(im=image_input, box=(0, height1))
	quality = 75
        result.save(
            path + sport_snapshot,
            format='JPEG',
            quality=quality,
            progressive=True,
            optimize=True)  # saves new cropped image

        ACCESS_KEY = 'AKIAJ2BJ3NVTAWWT44ZA'
        SECRET_KEY = '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'

        client = boto3.client(
            's3',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            config=Config(signature_version='s3v4')
        )

        client.upload_file(
            path + sport_snapshot,
            'smsresource',
            sport_snapshot)
"""
if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
