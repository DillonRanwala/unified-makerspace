
import os
import logging
from botocore.vendored import requests
import boto3
from datetime import datetime
import json
import urllib3
import time



http = urllib3.PoolManager()  #- lambda might not be able to use requests


dev_url = "https://d1byeqit66b8mv.cloudfront.net/"

frontend_response = http.request('GET', str(dev_url))

if frontend_response.status != 200:
    raise Exception("Front End Curl Failed")


if frontend_response.data.find(b"Makerspace Visitor Console") == -1:
   raise Exception("HTML from Front End Error")

now = datetime.now()
dt_string = now.strftime("%d/%m/%Y_%H:%M:%S")

unix_timestamp_for_ttl = int(time.time()+120) # Triggers ttl removal 2 minutes in future 

api_url = "https://r90fend561.execute-api.us-east-1.amazonaws.com/prod/"

visit_data = {"username":"PIPELINE_DEV_TEST_"+dt_string,"location":"Watt","tool":"Visiting","ttl_expiration":(unix_timestamp_for_ttl)}
visit_data = json.dumps(visit_data)

visit_data_unregistered = {"username":"PIPELINE_DEV_TEST_UNREGISTERED"+dt_string,"location":"Watt","tool":"Visiting","ttl_expiration":(unix_timestamp_for_ttl)}
visit_data_unregistered  = json.dumps(visit_data_unregistered )

visit_response = http.request('POST', str(api_url)+"visit",body=visit_data)
visit_response_unregistered = http.request('POST', str(api_url)+"visit",body=visit_data_unregistered)

if visit_response.status != 200 or visit_response_unregistered.status != 200:
    raise Exception("Visit API Call Failed")

register_data = {
    "username": "PIPELINE_DEV_TEST_"+dt_string,
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

print(reg_response.status)
if reg_response.status != 200: 
     raise Exception("Register API Call Failed")


print(visit_response.status == 200 and reg_response.status== 200 and frontend_response.status==200)

# if register has wrong inputs --> throws 502 status code


