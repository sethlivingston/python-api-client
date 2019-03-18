import unittest
from operator import itemgetter
from typing import List

from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth

from apiendpoints import API, APIEndpoint


class ReadmeTest(unittest.TestCase):

    @unittest.skip('integration')
    def test_readme(self):
        api = API('https://webhook.site/')
        endpoint = APIEndpoint(api, '/75b8e281-bb6d-4611-8cca-860d9d083545')

        response = endpoint.fetch()

        print(response)


class TestAPI(unittest.TestCase):

    def test_minimal_constructor(self):
        url = 'https://acme.com/api/v1/'

        api = API(url)

        self.assertEqual(api.url_root, url)
        self.assertDictEqual(api.headers, {})
        self.assertDictEqual(api.params, {})
        self.assertDictEqual(api.json, {})
        self.assertIsNone(api.auth)
        self.assertIsNone(api.retries)
        self.assertIsNotNone(api.logger)
        self.assertTrue(len(api.logger.name) > 0)

    def test_complete_constructor(self):
        url = 'https://acme.com/api/v1/'
        headers = {'one': 'apple'}
        params = {'two': 'banana'}
        json = {'three': 'grape'}
        auth = HTTPBasicAuth('username', 'password')
        retries = 5
        backoff_factor = 0.5
        forcelist = [500, 501, 502, 403]
        logger_name = 'test logger'

        api = API(url, headers=headers, params=params, json=json, auth=auth,
                  retry_count=retries, retry_backoff_factor=backoff_factor,
                  retry_status_forcelist=forcelist, logger_name=logger_name)

        self.assertEqual(api.url_root, url)
        self.assertDictEqual(api.headers, headers)
        self.assertDictEqual(api.params, params)
        self.assertDictEqual(api.json, json)
        self.assertEqual(api.auth, auth)
        self.assertEqual(api.retries.total, retries)
        self.assertEqual(api.retries.backoff_factor, backoff_factor)
        self.assertListEqual(api.retries.status_forcelist,
                             forcelist)

    def test_create_session(self):
        url = 'https://acme.com/api/v1/'
        auth = HTTPBasicAuth('username', 'password')
        retries = 5
        backoff_factor = 0.5
        forcelist = [500, 501, 502, 403]

        api = API(url, auth=auth, retry_count=retries,
                  retry_backoff_factor=backoff_factor,
                  retry_status_forcelist=forcelist)

        with api.create_session() as session:
            self.assertIsNotNone(session.auth)
            found_adapter = False
            adapters: List[HTTPAdapter] = session.adapters.values()
            for adapter in adapters:
                if adapter.max_retries == api.retries:
                    self.assertEqual(adapter.max_retries.total, retries)
                    self.assertEqual(adapter.max_retries.backoff_factor,
                                     backoff_factor)
                    self.assertListEqual(adapter.max_retries.status_forcelist,
                                         forcelist)
                    found_adapter = True
            self.assertTrue(found_adapter)


class TestAPIEndpoint(unittest.TestCase):

    def test_minimal_constructor(self):
        api = create_api()
        path = '/path/to/somewhere/'

        endpoint = APIEndpoint(api, path)

        self.assertEqual(endpoint.api, api)
        self.assertTrue(path in endpoint.url)
        self.assertEqual(endpoint.method, 'get')

    def test_complete_constructor(self):
        api = create_api()
        path = '/path/to/somewhere/'
        method = 'post'
        headers = {'four': 'apple'}
        params = {'five': 'mango'}
        json = {'six': 'papaya'}
        results_getter = itemgetter('items')
        nexturl_getter = itemgetter('next_page')

        endpoint = APIEndpoint(api, path, method=method, headers=headers,
                               params=params, json=json,
                               results_getter=results_getter,
                               nexturl_getter=nexturl_getter)

        self.assertEqual(endpoint.api, api)
        self.assertTrue(path in endpoint.url)
        self.assertEqual(endpoint.method, method)
        self.assertDictEqual(endpoint.headers, headers)
        self.assertDictEqual(endpoint.params, params)
        self.assertDictEqual(endpoint.json, json)
        self.assertEqual(endpoint.results_getter, results_getter)
        self.assertEqual(endpoint.nexturl_getter, nexturl_getter)

    def test_merge_with_defaults_unique(self):
        api = create_api()
        path = '/path/to/somewhere/'
        endpoint_headers = {'four': 'apple'}
        endpoint_params = {'five': 'mango'}
        endpoint_json = {'six': 'papaya'}
        fetch_headers = {'seven': 'honeydew'}
        fetch_params = {'eight': 'star'}
        fetch_json = {'nine': 'pear'}
        endpoint = APIEndpoint(api, path, headers=endpoint_headers,
                               params=endpoint_params, json=endpoint_json)

        merged_headers = endpoint._merge_with_defaults('headers', fetch_headers)
        merged_params = endpoint._merge_with_defaults('params', fetch_params)
        merged_json = endpoint._merge_with_defaults('json', fetch_json)

        for k, v in api.headers.items():
            self.assertIn(k, merged_headers)
            self.assertEqual(api.headers[k], merged_headers[k])
        for k, v in endpoint_headers.items():
            self.assertIn(k, merged_headers)
            self.assertEqual(endpoint_headers[k], merged_headers[k])
        for k, v in fetch_headers.items():
            self.assertIn(k, merged_headers)
            self.assertEqual(fetch_headers[k], merged_headers[k])

        for k, v in api.params.items():
            self.assertIn(k, merged_params)
            self.assertEqual(api.params[k], merged_params[k])
        for k, v in endpoint_params.items():
            self.assertIn(k, merged_params)
            self.assertEqual(endpoint_params[k], merged_params[k])
        for k, v in fetch_params.items():
            self.assertIn(k, merged_params)
            self.assertEqual(fetch_params[k], merged_params[k])

        for k, v in api.json.items():
            self.assertIn(k, merged_json)
            self.assertEqual(api.json[k], merged_json[k])
        for k, v in endpoint_json.items():
            self.assertIn(k, merged_json)
            self.assertEqual(endpoint_json[k], merged_json[k])
        for k, v in fetch_json.items():
            self.assertIn(k, merged_json)
            self.assertEqual(fetch_json[k], merged_json[k])

    def test_merge_with_defaults_overlapping(self):
        api = create_api()
        path = '/path/to/somewhere/'
        endpoint_headers = {'key': 'endpoint value'}
        fetch_headers = {'key': 'fetch value'}
        endpoint = APIEndpoint(api, path, headers=endpoint_headers)

        merged_headers = endpoint._merge_with_defaults('headers', fetch_headers)

        for k, v in api.headers.items():
            self.assertEqual(api.headers[k], merged_headers[k])
        for k, v in endpoint_headers.items():
            self.assertNotEqual(endpoint_headers[k], merged_headers[k])
        for k, v in fetch_headers.items():
            self.assertEqual(fetch_headers[k], merged_headers[k])


def create_api():
    url = 'https://acme.com/api/v1/'
    headers = {'one': 'apple'}
    params = {'two': 'banana'}
    json = {'three': 'grape'}
    auth = HTTPBasicAuth('username', 'password')
    retries = 5
    backoff_factor = 0.5
    forcelist = [500, 501, 502, 403]
    logger_name = 'test logger'

    api = API(url, headers=headers, params=params, json=json, auth=auth,
              retry_count=retries, retry_backoff_factor=backoff_factor,
              retry_status_forcelist=forcelist, logger_name=logger_name)

    return api
