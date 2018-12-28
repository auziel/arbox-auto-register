import json
from requests import Request, Session
import datetime

WOD = 'W.O.D'
OPEN_GYM = 'Open Gym'

s = Session()
userID: str = ''
membershipUser: str = ''
box: str = ''

# Find next friday

today = datetime.date.today()
sunday = (today + datetime.timedelta((6-today.weekday()) % 7))
monday = (today + datetime.timedelta((0-today.weekday()) % 7))
tuesday = (today + datetime.timedelta((1-today.weekday()) % 7))
wednesday = (today + datetime.timedelta((2-today.weekday()) % 7))
thursday = (today + datetime.timedelta((3-today.weekday()) % 7))
friday = (today + datetime.timedelta((4-today.weekday()) % 7))


def book_class(schedule):
    global s
    global userID
    global membershipUser
    global box

    for (class_date, class_time, category) in schedule:
        class_date_str = class_date.strftime("%Y-%m-%d")
        print(f'*** Trying to schedule {category} class for {class_date} at {class_time}')

        # Get the day schedule
        query_params = box + '/?date=' + class_date_str + '&userId=' + userID
        url = 'https://apiapp.arboxapp.com/index.php/api/v1/scheduleByDateList/' + query_params
        req = Request('GET', url)
        prepped = s.prepare_request(req)
        resp = s.send(prepped)
        print('GET scheduleByDateList:' + str(resp.status_code))

        # schedule_day = json.dumps(resp.json(), indent=4, separators=(',', ':'))
        # with open('data.json', 'w') as outfile:
        #     outfile.write(schedule_day)
        # outfile.close()

        day_schedule = resp.json()['Kfar-Saba']

        for c in day_schedule[0]:
            if c['category'] == category and c['schedule']['time'] == class_time:
                print('Category: ' + c['category'])
                print('Schedule ID: ' + str(c['schedule']['id']))
                print('Schedule: ' + c['schedule']['time'])
                url = 'https://apiapp.arboxapp.com/index.php/api/v1/scheduleUser'
                data = '{' \
                    f'"membershipUserFk": "{str(membershipUser)}",' \
                    f'"scheduleFk": "{str(c["schedule"]["id"])}",' \
                    f'"userFk": "{str(userID)}"' \
                    '}'

                print('Data = ' + data)

                req = Request('POST', url, data=data)
                prepped = s.prepare_request(req)
                resp = s.send(prepped)
                print('POST scheduleUser:' + str(resp.status_code) + str(resp.content))
                if resp.status_code == 200:
                    print(f'+++ Successfully register {class_date_str}, {class_date.strftime("%A")} at {class_time}')
                else:
                    print(f'--- Fail to register {class_date_str}, {class_date.strftime("%A")} at {class_time}')


def arbox_login():
    global s
    global userID
    global membershipUser
    global box

    # Login, get API token
    url = 'https://apiapp.arboxapp.com/index.php/api/v1/user/avi.uziel@gmail.com/session'
    data = '''{
      "email": "avi.uziel@gmail.com",
      "password": "avicf"
    }'''
    s.headers.update({'Content-Type': 'application/json;charset=UTF-8'})

    req = Request('OPTIONS', url, data=data)
    prepped = s.prepare_request(req)
    resp = s.send(prepped)
    print('OPTIONS:' + str(resp.status_code))

    req = Request('POST', url, data=data)
    prepped = s.prepare_request(req)
    resp = s.send(prepped)
    print('POST: ' + str(resp.status_code))
    content = resp.json()
    print(content)

    userID = str(content[u"user"][u"id"])
    token = content[u"token"]
    box = str(content[u"user"][u"locationBox"][u"boxFk"])
    print("userID: " + str(userID) + "\ntoken: " + str(token) + "\nbox: " + str(box))

    s.headers.update({'accessToken': token})

    url = 'https://apiapp.arboxapp.com/index.php/api/v1/membership/' + userID
    req = Request('GET', url)
    prepped = s.prepare_request(req)
    resp = s.send(prepped)
    print('GET membership: ' + str(resp.status_code))
    content = resp.json()
    print(content)
    membershipUser = content[0]['id']


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        {
            "resource": "Resource path",
            "path": "Path parameter",
            "httpMethod": "Incoming request's method name"
            "headers": {Incoming request headers}
            "queryStringParameters": {query string parameters }
            "pathParameters":  {path parameters}
            "stageVariables": {Applicable stage variables}
            "requestContext": {Request context, including authorizer-returned key-value pairs}
            "body": "A JSON string of the request payload."
            "isBase64Encoded": "A boolean flag to indicate if the applicable request payload is Base64-encode"
        }

        https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

    Attributes
    ----------

    context.aws_request_id: str
         Lambda request ID
    context.client_context: object
         Additional context when invoked through AWS Mobile SDK
    context.function_name: str
         Lambda function name
    context.function_version: str
         Function version identifier
    context.get_remaining_time_in_millis: function
         Time in milliseconds before function times out
    context.identity:
         Cognito identity provider context when invoked through AWS Mobile SDK
    context.invoked_function_arn: str
         Function ARN
    context.log_group_name: str
         Cloudwatch Log group name
    context.log_stream_name: str
         Cloudwatch Log stream name
    context.memory_limit_in_mb: int
        Function memory

        https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict
        'statusCode' and 'body' are required

        {
            "isBase64Encoded": true | false,
            "statusCode": httpStatusCode,
            "headers": {"headerName": "headerValue", ...},
            "body": "..."
        }

        # api-gateway-simple-proxy-for-lambda-output-format
        https: // docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    arbox_login()

    book_class([
        (sunday, '08:00:00', WOD),
        (monday, '09:00:00', WOD),
        (wednesday, '09:00:00', WOD),
        (thursday, '08:00:00', WOD),
        (friday, '9:00:00', WOD)
        ])

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)
    #
    #     raise e
    #
    # return {
    #     "statusCode": 200,
    #     "body": json.dumps(
    #         {"message": "hello world", "location": ip.text.replace("\n", "")}
    #     ),


if __name__ == '__main__':
    lambda_handler(None, None)
