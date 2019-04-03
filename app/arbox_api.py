import json
from requests import Request, Session


class ArboxApi:

    def __init__(self, email, creds) -> None:
        self.email = email
        self.creds = creds
        self.session: Session = Session()
        self.user_id: str = ''
        self.membership_user: str = ''
        self.box: str = ''
        self.token: str = ''

    def api_session(self):
        # Login, get API token
        url = 'https://apiapp.arboxapp.com/index.php/api/v1/user/' + self.email + '/session'
        self.session.headers.update({'Content-Type': 'application/json;charset=UTF-8'})

        req = Request('OPTIONS', url, data=json.dumps(self.creds))
        prepped = self.session.prepare_request(req)
        resp = self.session.send(prepped)
        print('OPTIONS:' + str(resp.status_code))

        req = Request('POST', url, data=json.dumps(self.creds))
        prepped = self.session.prepare_request(req)
        resp = self.session.send(prepped)
        return resp

    def api_membership(self):
        url = 'https://apiapp.arboxapp.com/index.php/api/v1/membership/' + self.user_id
        req = Request('GET', url)
        prepped = self.session.prepare_request(req)
        resp = self.session.send(prepped)
        return resp

    def login(self):
        resp = self.api_session()
        if resp.status_code != 200:
            print("Fail to call session api")
            return False

        resp_json = resp.json()
        self.user_id = str(resp_json[u"user"][u"id"])
        self.token = resp_json[u"token"]
        self.box = str(resp_json[u"user"][u"locationBox"][u"boxFk"])
        print("userID: " + str(self.user_id) + "\ntoken: " + str(self.token) + "\nbox: " + str(self.box))

        self.session.headers.update({'accessToken': self.token})

        resp = self.api_membership()
        if resp.status_code != 200:
            print("Fail to call membership api")
            return False

        resp_json = resp.json()
        self.membership_user = str(resp_json[0]['id'])

        return True

    def schedule_by_date_list(self, date):
        query_params = self.box + '/?date=' + date + '&userId=' + self.user_id
        url = 'https://apiapp.arboxapp.com/index.php/api/v1/scheduleByDateList/' + query_params
        req = Request('GET', url)
        prepped = self.session.prepare_request(req)
        return self.session.send(prepped)

    def schedule_user(self, schedule_id):
        url = 'https://apiapp.arboxapp.com/index.php/api/v1/scheduleUser'

        data_dic = dict()
        data_dic['membershipUserFk'] = self.membership_user
        data_dic['scheduleFk'] = schedule_id
        data_dic['userFk'] = self.user_id
        data = json.dumps(data_dic)
        print('Data = ' + data)

        req = Request('POST', url, data=data)
        prepped = self.session.prepare_request(req)
        return self.session.send(prepped)
