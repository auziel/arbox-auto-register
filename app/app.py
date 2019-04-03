import datetime
import json
import os
from collections import defaultdict

import requests

from arbox_api import ArboxApi

WOD = 'W.O.D'
OPEN_GYM = 'Open Gym'
BOX_ATIR_YEDA_API = ' CFKS - Atir Yeda'
BOX_HATAAS_API = 'CFKS - HaTaas'
BOX_ATIR_YEDA_USER_SCHEDULE = 'Atir-Yeda'
BOX_HATAAS_USER_SCHEDULE = 'Hataas'

MONDAY_INDEX = 0
TUESDAY_INDEX = 1
WEDNESDAY_INDEX = 2
THURSDAY_INDEX = 3
FRIDAY_INDEX = 4
SATURDAY_INDEX = 5
SUNDAY_INDEX = 6


def date_of_day_in_next_week(day):
    today = datetime.date.today()
    dates = {
        'monday': (today + datetime.timedelta((MONDAY_INDEX - today.weekday()) % 7)),
        'tuesday': (today + datetime.timedelta((TUESDAY_INDEX - today.weekday()) % 7)),
        'wednesday': (today + datetime.timedelta((WEDNESDAY_INDEX - today.weekday()) % 7)),
        'thursday': (today + datetime.timedelta((THURSDAY_INDEX - today.weekday()) % 7)),
        'friday': (today + datetime.timedelta((FRIDAY_INDEX - today.weekday()) % 7)),
        'saturday': (today + datetime.timedelta((SATURDAY_INDEX - today.weekday()) % 7)),
        'sunday': (today + datetime.timedelta((SUNDAY_INDEX - today.weekday()) % 7))
    }

    return dates.get(day)


def book_class(arbox_api, schedules):
    print(schedules)

    booking_res = defaultdict(list)
    for schedule in schedules:
        class_date_str = date_of_day_in_next_week(schedule["day"]).strftime("%Y-%m-%d")
        print('*** Trying to schedule ' + schedule["class_type"] + ' class for ' + schedule["day"] + ' at ' + schedule[
            "time"])

        resp = arbox_api.schedule_by_date_list(class_date_str)
        print('GET scheduleByDateList:' + str(resp.status_code))
        if schedule['box'] == BOX_ATIR_YEDA_USER_SCHEDULE:
            box_str = BOX_ATIR_YEDA_API
        elif schedule['box'] == BOX_HATAAS_USER_SCHEDULE:
            box_str = BOX_HATAAS_API
        else:
            print("Box input is wrong, skipping")
            continue

        day_schedule = resp.json()[box_str]
        for c in day_schedule[0]:
            if c['category'] == schedule['class_type'] and c['schedule']['time'] == schedule['time']:
                print('Category: ' + c['category'])
                print('Schedule ID: ' + str(c['schedule']['id']))
                print('Schedule: ' + c['schedule']['time'])
                resp = arbox_api.schedule_user(c["schedule"]["id"])
                print('POST scheduleUser: {} {}'.format(str(resp.status_code), str(resp.content)))
                class_info = (schedule['class_type'], schedule["day"], class_date_str, c['schedule']['time'])
                if resp.status_code == 200:
                    msg = '+++ Successfully register'
                    booking_res['Booked'].append(class_info)
                else:
                    booking_res['NOT booked'].append(class_info)
                    msg = '--- Fail register'

                print(msg + ' ' + class_date_str + '\n' +
                      date_of_day_in_next_week(schedule["day"]).strftime("%A") + ' at ' + schedule["time"])

                # we found the class for this day, move to next class
                break

    return booking_res


def get_schedule():
    schedule_folder = os.path.dirname(os.path.abspath(__file__))

    data = None
    try:
        with open(os.path.join(schedule_folder, 'schedule.json')) as f:
            data = json.load(f)
    except IOError as e:
        print("Fail to open schedule file. Error: " + e)

    return data


def lambda_handler(event, context):
    schedule_config = get_schedule()

    if schedule_config is None:
        print('No schedule config file found')
        exit(1)

    for schedule in schedule_config["schedules"]:
        arbox_api = ArboxApi(schedule["creds"]["email"], schedule["creds"])
        arbox_api.login()
        booked_classes = book_class(arbox_api, schedule["classes"])
        print(str(booked_classes))

        slack_msg = "Booked successfully:\n" + str(booked_classes['Booked']) + "\nFail to book:\n" + str(booked_classes['NOT booked'])
        slack_payload = {"text": slack_msg}
        res = requests.post('https://hooks.slack.com/services/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',
                            data=json.dumps(slack_payload, indent=4))
        print('post to slack result = ' + str(res))


if __name__ == '__main__':
    lambda_handler(None, None)
