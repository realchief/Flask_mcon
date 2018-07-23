# This locust test script example will simulate a user 
# browsing the Locust documentation on http://docs.locust.io

import random
from locust import HttpLocust, TaskSet, task
from pyquery import PyQuery


class BrowseDocumentation(TaskSet):
    @task(10)
    def index_page(self):
        r = self.client.get("/2be26f33-b8a3-45be-a225-52dbf6cd34ee")
        #r = self.client.get("/click.php?key=7ayjozfczdcdlw6mr62o")

class AwesomeUser(HttpLocust):
    task_set = BrowseDocumentation
    host = "http://trk.clickchaser.com"
    #host = "https://clicktrackerz.com"
    
    # we assume someone who is browsing the Locust docs, 
    # generally has a quite long waiting time (between 
    # 20 and 600 seconds), since there's a bunch of text 
    # on each page
    min_wait = 1  * 1000
    max_wait = 1 * 1000
