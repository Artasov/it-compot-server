from urllib.parse import urlencode

import requests
from django.conf import settings


class HolliHopApiV2SyncManager:
    def __init__(self, domain: str = settings.HOLLIHOP_DOMAIN, authkey: str = settings.HOLLIHOP_AUTHKEY):
        if not all((domain, authkey)):
            raise ValueError('domain and authkey required')
        self.domain = domain
        self.authkey = authkey

    @staticmethod
    def fetch(url):
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def fetch_all(self, url, params, maxTake=10000, batchSize=1000):
        results = []
        for skip in range(0, maxTake, batchSize):
            batch_params = params.copy()
            batch_params['skip'] = skip
            batch_params['take'] = min(batchSize, maxTake - skip)
            batch_url = f"{url}?{urlencode(batch_params, safe='/', encoding='utf-8')}"
            results.append(self.fetch(batch_url))
        return results

    def api_call_pagination(self, endpoint, maxTake=10000, batchSize=1000, **kwargs):
        url = f"https://{self.domain}/Api/V2/{endpoint}"
        kwargs['authkey'] = self.authkey
        return self.fetch_all(url, kwargs, maxTake=maxTake, batchSize=batchSize)

    def api_call(self, endpoint, **params):
        url = f"https://{self.domain}/Api/V2/{endpoint}"
        params['authkey'] = self.authkey
        response = self.fetch(f"{url}?{urlencode(params)}")
        return response

    @staticmethod
    def post_fetch(url, data):
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {'success': True} if response.status_code == 200 else {'success': False}

    def api_post_call(self, endpoint, **params):
        url = f"https://{self.domain}/Api/V2/{endpoint}?authkey={self.authkey}"
        if params.get('like_array'):
            response = self.post_fetch(url, data=params['like_array'])
        else:
            response = self.post_fetch(url, data=params)
        return response

    def setStudentPasses(self, **kwargs):
        response = self.api_post_call('SetStudentPasses', **kwargs)
        return response

    def getTeachers(self, **kwargs):
        teachers = self.api_call('GetTeachers', **kwargs)
        return teachers.get('Teachers', [])
