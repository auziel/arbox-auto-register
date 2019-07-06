from collections import namedtuple
import json
import pprint

import pytest
from pytest import fixture

from app import app


@pytest.fixture()
def apigw_event():
    """ Generates API GW Event"""

    return {
        "body": '{ "test": "body"}',
        "resource": "/{proxy+}",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "identity": {
                "apiKey": "",
                "userArn": "",
                "cognitoAuthenticationType": "",
                "caller": "",
                "userAgent": "Custom User Agent String",
                "user": "",
                "cognitoIdentityPoolId": "",
                "cognitoIdentityId": "",
                "cognitoAuthenticationProvider": "",
                "sourceIp": "127.0.0.1",
                "accountId": "",
            },
            "stage": "prod",
        },
        "queryStringParameters": {"foo": "bar"},
        "headers": {
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "Accept-Language": "en-US,en;q=0.8",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Mobile-Viewer": "false",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "CloudFront-Viewer-Country": "US",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-Port": "443",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "X-Forwarded-Proto": "https",
            "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "CloudFront-Is-Tablet-Viewer": "false",
            "Cache-Control": "max-age=0",
            "User-Agent": "Custom User Agent String",
            "CloudFront-Forwarded-Proto": "https",
            "Accept-Encoding": "gzip, deflate, sdch",
        },
        "pathParameters": {"proxy": "/examplepath"},
        "httpMethod": "POST",
        "stageVariables": {"baz": "qux"},
        "path": "/examplepath",
    }


@fixture
def schedule():
    return {
        "schedules": [
            {
                "creds": {
                    "email": "avi.uziel@gmail.com",
                    "password": "avicf"
                },
                "classes": [
                    {
                        "box": "Atir-Yeda",
                        "day": "thursday",
                        "time": "06:00:00",
                        "class_type": "W.O.D"
                    },
                    {
                        "box": "Atir-Yeda",
                        "day": "friday",
                        "time": "09:00:00",
                        "class_type": "W.O.D"
                    }
                ]
            },
            {
                "creds": {
                    "email": "anat.uziel@gmail.com",
                    "password": "anatcf"
                },
                "classes": [
                    {
                        "box": "Atir-Yeda",
                        "day": "thursday",
                        "time": "12:00:00",
                        "class_type": "W.O.D"
                    },
                    {
                        "box": "Atir-Yeda",
                        "day": "friday",
                        "time": "12:00:00",
                        "class_type": "W.O.D"
                    }
                ]
            }
        ]
    }


@fixture()
def slack_res():
    return {"NOT booked": [(("W.O.D",
                             "thursday",
                             "2019-07-11",
                             "06:00:00"),
                            "avi.uziel@gmail.com"),
                           (("W.O.D",
                             "friday",
                             "2019-07-12",
                             "09:00:00"),
                            "avi.uziel@gmail.com")],
            "NOT booked (Class doesn\"t exist)": [("friday;12: 00:00",
                                                   "anat.uziel@gmail.com"),
                                                  ("thursday;12:00:00",
                                                   "anat.uziel@gmail.com")]}


def test_lambda_handler(apigw_event, mocker):
    res = app.lambda_handler(None, None)
    

def test_schedule_two_class_one_user(schedule):
    booked_classes_res = app.book_schedule_for_user(schedule['schedules'][0])
    print(booked_classes_res)


def test_schedule_two_class_two_users(schedule):
    booked_classes_res = app.book_all_users(schedule['schedules'])
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(booked_classes_res)


def test_slack_message(slack_res):
    res = app.send_slack_res(slack_res)
    assert res.status_code == 200