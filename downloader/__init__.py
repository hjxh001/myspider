#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Author: caleb<cale.huang@gmail.com>
#
# Created on 2016-01-05
import time
import copy
import json
import logging
import six

import tornado.ioloop
import tornado.httpclient
from tornado import httputil
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado.simple_httpclient import SimpleAsyncHTTPClient

#logger = logging.getLogger('fetcher')

class MyCurlAsyncHTTPClient(CurlAsyncHTTPClient):

    def free_size(self):
        return len(self._free_list)

    def size(self):
        return len(self._curls) - self.free_size()

class Downloader(object):
    default_user_agent = "MySpider/%s"
    default_user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20131029 Firefox/17.0"

    default_options = {
        'method': 'GET',
        'headers': {
        },
        'use_gzip': True,
        'connect_timeout':120,
        'request_timeout': 120,
    }

    def __init__(self, poolsize=10, proxy=None, async=True):

        self.poolsize = poolsize
        self._running = False
        self._quit = False
        self.proxy = proxy
        self.async = async
        self.ioloop = tornado.ioloop.IOLoop()

        if self.async:
            self.http_client = MyCurlAsyncHTTPClient(max_clients=self.poolsize)
        else:
            self.http_client = tornado.httpclient.HTTPClient(
                MyCurlAsyncHTTPClient, max_clients=self.poolsize
            )

    def handle_response(self,response):
            print response.code
            #print response.headers.get('Etag')
            if not response.code == 200:
                for name,values in response.headers.get_all():
                    print name,values
            return response
    
    def handle_error(self,e):
        return e
    
    allowed_options = ['method', 'data', 'timeout', 'cookies', 'use_gzip']

    def fetch_request(self,url,task = {},callback = None):
        start_time = time.time()
        request=copy.deepcopy(self.default_options)
        request['headers']['User-Agent'] = self.default_user_agent
        request['url']=url
        task_fetch = task.get('fetch',{})
        for r in self.allowed_options:
            if r in task_fetch:
                request[r] = task_fetch[r]
        request['headers'].update(task_fetch.get('headers',{}))
        
        #print request
        #etag  如果etag未变化，返回304
        if 'etag' in request['headers']:
            _t = None
            if isinstance(request['headers'].get('etag'), six.string_types):
                _t = request['headers'].get('etag')
            if _t:
                request['headers'].setdefault('If-None-Match', _t)
            del request['headers']['etag']

        # last modifed 如果last_modified未发生变化，返回304
        if 'last_modified' in request['headers']:
            _t = None
            if isinstance(request['headers'].get('last_modified'), six.string_types):
                _t = request['headers'].get('last_modified')
            if _t:
                request['headers'].setdefault('If-Modified-Since', _t)
            del request['headers']['last_modified']



        if 'data' in task_fetch:
            if request['method']=='POST':
                if isinstance(task_fetch['data'],dict):
                    task_fetch['data']=json.dumps(task_fetch['data'])
                request['body'] = task_fetch['data']
            del request['data']

        if 'timeout' in task_fetch:
            request['connect_timeout'] = request['request_timeout'] = task_fetch['timeout']
            del request['timeout']


        def make_request(fetch):
            try:

                http_request = tornado.httpclient.HTTPRequest(**fetch)
                if self.async:
                    self.http_client.fetch(http_request, self.handle_response)
                else:
                    return self.handle_response(self.http_client.fetch(http_request))
            except tornado.httpclient.HTTPError as e:
                if e.response:
                    return self.handle_response(e.response)
                else:
                    return self.handle_error(e)
            except Exception as e:
                logging.exception(fetch)
                return self.handle_error(e)


        make_request(request)


def main():
    if ASYNC==True:
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.add_callback(scrapeEverything)
        ioloop.start()
    else:
        scrapeEverything()
def scrapeEverything():
    fetcher = Downloader(async=ASYNC)
    
    listOfIds = [23423, 52356, 63462, 34673, 67436]
    
    last_modified = httputil.format_timestamp(1447947700)
    etag = "FjKmlXHHV1J_HN4OzRgbKuga-XSK.gz"
    fetch = {"fetch":{"headers":{"Cache-Control":"max-age=0","Connection":"keep-alive"},"timeout":300,"connect_timeout":100,"data":"111"}}

    for id in listOfIds:
        fetcher.fetch_request("http://mydatasite.com/?data_id=%d" % id,fetch)

    fetch['fetch']['headers'].update({"last_modified":last_modified,"etag":etag})
    fetcher.fetch_request("http://static.baifendian.com/api/2.0/bcore.min.js",fetch)

if __name__ == '__main__':
    global ASYNC
    ASYNC = True
    main()
    #CurlAsyncHTTPClient()


