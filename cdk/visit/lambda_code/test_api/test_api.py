
import os
import logging
from botocore.vendored import requests
import boto3
from datetime import datetime
import json
import urllib3
import time

class TestAPIFunction():
    """
    This function will be used to wrap the functionality of the lambda
    so we can more easily test with pytest.
    """

    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.env = os.environ["ENV"]


    def handle_test_api(self):
        http = urllib3.PoolManager()  

        if self.env == "Dev": #"Beta"
            print("https://beta-visit.cumaker.space/")
            print("https://beta-api.cumaker.space/")
        elif self.env == "Prod":
            print("https://visit.cumaker.space/")
            print("https://api.cumaker.space/")
            
        frontend_url = "https://d1byeqit66b8mv.cloudfront.net/"
       

        frontend_response = http.request('GET', str(frontend_url))

        if frontend_response.status != 200:
            raise Exception("Front End Curl Failed")

        if frontend_response.data.find(b"Makerspace Visitor Console") == -1:
            raise Exception("HTML from Front End Error")

        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y_%H:%M:%S")
        
        unix_timestamp_for_ttl = int(time.time()+120) # Triggers ttl removal 2 minutes in future 

        api_url = "https://r90fend561.execute-api.us-east-1.amazonaws.com/prod/"

        visit_data = {"username":"CANARY_DEV_TEST_"+dt_string,"location":"Watt","tool":"Visiting","ttl_expiration":(unix_timestamp_for_ttl)}
        visit_data = json.dumps(visit_data)

        visit_response = http.request('POST', str(api_url)+"visit",body=visit_data)


        visit_data_unregistered = {"username":"CANARY_DEV_TEST_UNREGISTERED"+dt_string,"location":"Watt","tool":"Visiting","ttl_expiration":(unix_timestamp_for_ttl)}
        visit_data_unregistered  = json.dumps(visit_data_unregistered )

        visit_response = http.request('POST', str(api_url)+"visit",body=visit_data)
        visit_response_unregistered = http.request('POST', str(api_url)+"visit",body=visit_data_unregistered)

        if visit_response.status != 200 or visit_response_unregistered.status != 200:
            raise Exception("Visit API Call Failed")

        register_data = {
            "username": "CANARY_DEV_TEST_"+dt_string,
            "firstName": "TEST",
            "lastName": "USER",
            "Gender": "Male",
            "DOB": "01/01/2000",
            "UserPosition": "Undergraduate Student",
            "GradSemester": "Fall",
            "GradYear": "2023",
            "Major": ["Mathematical Sciences"],
            "Minor": ["Business Administration"],
            "ttl_expiration":(unix_timestamp_for_ttl)
        }

        register_data = json.dumps(register_data)

        reg_response = http.request('POST', str(api_url)+"register",body=register_data)

        if reg_response.status != 200: 
            raise Exception("Register API Call Failed")


        return visit_response.status == 200 and reg_response.status== 200 and frontend_response.status==200
        


test_api_function = TestAPIFunction()

def handler(request, context):
    # This will be hit in prod, and will connect to the stood-up dynamodb
    # and Simple Email Service clients.
    return test_api_function.handle_test_api()


