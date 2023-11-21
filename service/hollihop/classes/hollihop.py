from pprint import pprint

import requests
from requests import HTTPError, RequestException
from urllib.parse import urlencode

from config.settings import HOLLIHOP_DOMAIN, HOLLIHOP_AUTHKEY


class HolliHopApiV2Manager:
    def __init__(self, domain: str = HOLLIHOP_DOMAIN, authkey: str = HOLLIHOP_AUTHKEY):
        self.domain = domain
        self.authkey = authkey

    def getTeachers(self, id=None, officeOrCompanyId=None, term=None, byAgents=False, descending=False, skip=None,
                    take=1000):
        params = {'authkey': self.authkey}

        if id is not None:
            params['id'] = id
        if officeOrCompanyId is not None:
            params['officeOrCompanyId'] = officeOrCompanyId
        if term is not None:
            params['term'] = term
        if byAgents:
            params['byAgents'] = 'true'
        if descending:
            params['descending'] = 'true'
        if skip is not None:
            params['skip'] = skip
        if take is not None:
            params['take'] = take

        url = f"https://{self.domain}/Api/V2/GetTeachers?{urlencode(params)}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()['Teachers']
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
        except RequestException as err:
            print(f'Error occurred: {err}')
        except Exception as e:
            print(f'Other error occurred: {e}')

        return None


