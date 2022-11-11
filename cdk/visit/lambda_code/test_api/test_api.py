
import os
import logging
import requests
import boto3
from datetime import datetime


#TODO: pass in api url as a parameter, don't hardcode if possible
class TestAPIFunction():
    """
    This function will be used to wrap the functionality of the lambda
    so we can more easily test with pytest.
    """

    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)


    def handle_test_api(self):
        # datetime object containing current date and time
        now = datetime.now()
        
        dt_string = now.strftime("%d/%m/%Y_%H:%M:%S")


        api_url = "https://r90fend561.execute-api.us-east-1.amazonaws.com/prod/"

        visit_data = {"username":"PIPELINE_DEV_TEST_"+dt_string,"location":"Watt","tool":"Visiting"}


        visit_response = requests.post(api_url + "visit", json = visit_data)

        if visit_response.status_code != 200:
            raise Exception("Visit API Call Failed")

        register_data = {
            "username": "PIPELINE_DEV_VISIT_"+dt_string,
            "firstName": "TEST",
            "lastName": "USER",
            "Gender": "Male",
            "DOB": "01/01/2000",
            "UserPosition": "Undergraduate Student",
            "GradSemester": "Fall",
            "GradYear": "2023",
            "Major": ["Mathematical Sciences"],
            "Minor": ["Business Administration"]
        }

        reg_response = requests.post(api_url + "register", json = register_data)

        if reg_response.status_code != 200:
            raise Exception("Register API Call Failed")

        print("success")


        return visit_response.status_code == 200 and reg_response.status_code== 200
        


test_api_function = TestAPIFunction()

def handler():
    # This will be hit in prod, and will connect to the stood-up dynamodb
    # and Simple Email Service clients.
    return test_api_function.handle_test_api()


