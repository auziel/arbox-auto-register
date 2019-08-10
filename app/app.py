import concurrent
import datetime
import json
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

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


def book_a_class(creds, schedule):
    ''' schedule one class, by using it in a thread we can parallel the calls to
    all class schedule
    '''
    arbox_api = ArboxApi(creds['email'], creds)
    if not arbox_api.login():
        raise Exception("Login failed")

    class_date_str = date_of_day_in_next_week(schedule["day"]).strftime("%Y-%m-%d")
    print('*** Trying to schedule: ' + creds['email'] + '; ' + schedule["class_type"] +
          ' class for ' + schedule["day"] + ' at ' + schedule["time"])

    resp = arbox_api.schedule_by_date_list(class_date_str)
    print('GET scheduleByDateList:' + str(resp.status_code))
    print(str(class_date_str) + " res = " + str(resp.content))
    if schedule['box'] == BOX_ATIR_YEDA_USER_SCHEDULE:
        box_str = BOX_ATIR_YEDA_API
    elif schedule['box'] == BOX_HATAAS_USER_SCHEDULE:
        box_str = BOX_HATAAS_API
    else:
        print("Box input is wrong, skipping")
        return 'bad input', None

    res_tuple = ("NOT booked (Class doesn't exist)", str(schedule['day'] + ';' + schedule['time']), creds['email'])
    day_schedule = resp.json()[box_str]
    # Iterate all classes in day and find the one matching our class request
    if len(day_schedule) > 0:
        for c in day_schedule[0]:
            if c['category'] == schedule['class_type'] and c['schedule']['time'] == schedule['time']:
                print('Category: ' + c['category'])
                print('Schedule ID: ' + str(c['schedule']['id']))
                print('Schedule: ' + c['schedule']['time'])
                # register if class is not full
                if c['numberOfUsers'] < c['schedule']['maxUsers']:
                    resp = arbox_api.schedule_user(c["schedule"]["id"])
                    print('POST scheduleUser: {} {}'.format(str(resp.status_code), str(resp.content)))
                    class_info = (schedule['class_type'], schedule["day"], class_date_str, c['schedule']['time'])
                    if resp.status_code == 200:
                        msg = '+++ Successfully register'
                        res_tuple = 'Booked', class_info, creds['email']
                    else:
                        msg = '--- Fail register'
                        res_tuple = res_tuple = 'NOT booked', class_info, creds['email']

                else:  # schedule for standby
                    resp = arbox_api.schedule_standby(c["schedule"]["id"])
                    print('POST scheduleStandby: {} {}'.format(str(resp.status_code), str(resp.content)))
                    class_info = (schedule['class_type'], schedule["day"], class_date_str, c['schedule']['time'])
                    if resp.status_code == 200:
                        msg = '+++ Successfully added to standby'
                        res_tuple = 'Standby', class_info, creds['email']
                    else:
                        msg = '--- Fail register'
                        res_tuple = 'NOT booked', class_info, creds['email']

                print(msg + ' ' + class_date_str + '\n' +
                      date_of_day_in_next_week(schedule["day"]).strftime("%A") + ' at ' + schedule["time"])

                break

    # we found the class for this day, move to next class
    return res_tuple


def get_schedule():
    schedule_folder = os.path.dirname(os.path.abspath(__file__))

    data = None
    try:
        with open(os.path.join(schedule_folder, 'schedule.json')) as f:
            data = json.load(f)
    except IOError as e:
        print("Fail to open schedule file. Error: " + e)

    return data


def book_all_users(all_schedule):
    res_dict = defaultdict(list)
    future_to_schedules = dict()
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        for user_schedule in all_schedule:
            f = {executor.submit(book_a_class, user_schedule['creds'], schedule): schedule
                                   for schedule in user_schedule['classes']}
            future_to_schedules = {**f, **future_to_schedules}

    for future in concurrent.futures.as_completed(future_to_schedules):
        schedule = future_to_schedules[future]
        try:
            data = future.result()
        except Exception as exc:
            print('%r generated an exception: %s' % (schedule, exc))
        else:
            res_dict[data[0]].append((data[1], data[2]))
            print('%r page is %d bytes' % (schedule, len(data)))

    return res_dict


def send_slack_res(booking_res):
    slack_payload = {"text": str(booking_res)}
    return requests.post('https://hooks.slack.com/services/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',
                         data=json.dumps(slack_payload, indent=4))


def lambda_handler(event, context):
    schedule_config = get_schedule()

    if schedule_config is None:
        print('No schedule config file found')
        exit(1)

    booked_classes_res = book_all_users(schedule_config['schedules'])
    res = send_slack_res(booked_classes_res)

    print('post to slack result = ' + str(res))


if __name__ == '__main__':
    lambda_handler(None, None)
