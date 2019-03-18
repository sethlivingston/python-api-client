import logging
from typing import Iterable
from urllib.parse import urljoin

from requests import Session, PreparedRequest, Request, Response
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from urllib3 import Retry

MODULE_NAME = __name__


class API(object):
    def __init__(
            self,
            url_root: str,
            headers: dict = None,
            params: dict = None,
            json: dict = None,
            auth: AuthBase = None,
            retry_count: int = 0,
            retry_backoff_factor: float = 1,
            retry_status_forcelist: Iterable = None,
            logger_name: str = MODULE_NAME,
    ):
        self.url_root = url_root
        self.headers = headers or {}
        self.params = params or {}
        self.json = json or {}
        self.auth = auth
        if retry_count > 0:
            self.retries = Retry(retry_count,
                                 backoff_factor=retry_backoff_factor,
                                 status_forcelist=retry_status_forcelist)
        else:
            self.retries = None
        self.logger = logging.getLogger(logger_name)

    def create_session(self):
        adapter = HTTPAdapter(max_retries=self.retries)
        s = Session()
        s.auth = self.auth
        s.mount(self.url_root, adapter)
        return s


class APIEndpoint(object):
    def __init__(
            self,
            api: API,
            path: str,
            method: str = 'get',
            headers: {} = None,
            params: {} = None,
            json: {} = None,
            results_getter: callable = lambda x: x,
            nexturl_getter: callable = lambda x: None,
    ):
        self.api = api
        self.path = path
        self.method = method
        self.headers = headers or {}
        self.params = params or {}
        self.json = json or {}
        self.results_getter = results_getter
        self.nexturl_getter = nexturl_getter

        self.url = urljoin(self.api.url_root, self.path)
        self.req = None
        self.res = None

    def fetch(
            self,
            headers: dict = None,
            params: dict = None,
            json: dict = None,
    ) -> dict:
        merged_headers = self._merge_with_defaults('headers', headers)
        merged_params = self._merge_with_defaults('params', params)
        merged_json = self._merge_with_defaults('json', json)

        nexturl = None
        results = None

        with self.api.create_session() as session:
            res = self._send(session, merged_headers, merged_json,
                             merged_params)
            if res.content:
                json = res.json()
                results = self.results_getter(json)
                nexturl = self.nexturl_getter(json)

            while nexturl:
                res = session.request(self.method, nexturl,
                                      headers=merged_headers)
                res.raise_for_status()
                if res.content:
                    json = res.json()
                    results += self.results_getter(json)
                    nexturl = self.nexturl_getter(json)
                else:
                    nexturl = None

        return results

    def _send(
            self,
            session: Session,
            headers: dict,
            params: dict,
            json: dict,
    ):
        self.req = None
        self.res = None

        self.req = Request(self.method, self.url, headers=headers,
                           params=params, json=json)
        self.req = session.prepare_request(self.req)
        self.res = session.send(self.req)

        formatted_req = self._format_request(self.req)
        formatted_res = self._format_response(self.res)
        log = self.api.logger.info if 200 <= self.res.status_code <= 299 \
            else self.api.logger.error
        log(formatted_req)
        log(formatted_res)

        self.res.raise_for_status()
        return self.res

    def _merge_with_defaults(self, name: str, local: dict):
        result = {}
        result.update(getattr(self.api, name, {}))
        result.update(getattr(self, name, {}))
        result.update(local or {})
        return result

    @staticmethod
    def _format_request(req: PreparedRequest) -> str:
        formatted = ['%s %s\n' % (req.method, req.url)]
        for k, v in req.headers.items():
            formatted.append('%s: %s\n' % (k, v or ''))
        formatted.append(req.body.decode('utf-8') or '')
        return ''.join(formatted)

    @staticmethod
    def _format_response(res: Response) -> str:
        formatted = ['%d\n' % res.status_code]
        for k, v in res.headers.items():
            formatted.append('%s: %s\n' % (k, v or ''))
        formatted.append('\n')
        formatted.append(res.text or '')
