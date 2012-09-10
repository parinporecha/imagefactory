# encoding: utf-8

#   Copyright 2011 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import oauth2 as oauth
#from imgfac.ApplicationConfiguration import ApplicationConfiguration
#import socks
import logging
import pycurl
import httplib2
import urllib
import urllib2
import requests
from oauth_hook import OAuthHook

class ProxyHelper(object):

    def __init__(self, oauth=False, key = None, secret = None, proxy = False, proxy_host = None, proxy_port = None):
        self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

        #appconfig = ApplicationConfiguration().configuration
        #if proxy:
        #    self.http =  httplib2.Http(proxy_info = httplib2.ProxyInfo(socks.PROXY_TYPE_HTTP, proxy_host, proxy_port))
        #else:
        #    self.http = httplib2.Http()
        self.oauth = oauth
        self.key = key
        self.secret = secret
        if proxy:
            self.proxies = { "http": "%s:%s" % (proxy_host, proxy_port),
                             "https": "%s:%s" % (proxy_host, proxy_port) }
        else:
            self.proxies = None
            
    def _oauth_headers(self, url, http_method):
        consumer = oauth.Consumer(key=self.key,
                                  secret=self.secret)
        sig_method = oauth.SignatureMethod_HMAC_SHA1()

        # Annoyingly, this module variable name changes between 1.2 and 1.5
        oauth_version = None
        try:
            oauth_version = oauth.OAUTH_VERSION
        except AttributeError:
            oauth_version = oauth.VERSION

        params = {'oauth_version':oauth_version,
                  'oauth_nonce':oauth.generate_nonce(),
                  'oauth_timestamp':oauth.generate_timestamp(),
                  'oauth_signature_method':sig_method.name,
                  'oauth_consumer_key':consumer.key}
        req = oauth.Request(method=http_method, url=url, parameters=params)
        sig = sig_method.sign(req, consumer, None)
        req['oauth_signature'] = sig
        return req.to_header()

    def request(self, url, method, body = None, content_type = 'text/plain', files = None):

        if self.oauth:
            oauth_hook = OAuthHook(consumer_key=self.key, consumer_secret=self.secret, header_auth = True)
            hooks = { 'pre_request': oauth_hook }
        else:
            hooks = { }

        try:
            #headers['content-type'] = content_type
            if method == "GET":
                response = requests.get(url, proxies=self.proxies, verify=False)
            elif method == "POST":
                response = requests.post(url, data=body, hooks=hooks, proxies=self.proxies, verify=False)
            elif method == "POSTFILE":
                #if 'content-type' in headers:
                #    del headers['content-type']
                response = requests.post(url, files=files, hooks = hooks, verify=False)
            elif method == "PUT":
                response = requests.put(url, data=body, headers=headers, proxies=self.proxies)
            else:
                raise Exception("Unable to process HTTP method (%s)" % (method) )

            #print dir(response)
            #print response.error
            #print response.status_code
            #print response.content
            response_body = response.content
            response_headers = response.headers
            status = response.status_code
            #request = urllib2.Request(url, body, headers)
            # This is a bit hackey but it works
            #if method == 'PUT':
            #    request.get_method = lambda: 'PUT'
            #response = urllib2.urlopen(request)
            #response_body = response.read()
            #response_headers = response.info() 
            #response_headers, response = self.http.request(url, method, body, headers=headers)
            #status = int(response_headers["status"])
            # Log additional detail if the HTTP resonse code is abnormal
            if(399 < status < 600):
                self.log.debug("HTTP request to (%s) returned status (%d) with message: %s" % (url, status, response_body))
            return (response_headers, response_body)
        except Exception, e:
            raise
            #raise Exception("Problem encountered trying to execute HTTP request to (%s). Please check that your target service is running and reachable.\nException text: %s" % (url, e))

    def _http_get(self, url):
        return self.request(url, 'GET')[1]

    def _http_post(self, url, body, content_type):
        return self.request(url, 'POST', body, content_type)[1]

    def _http_post_file(self, url, files):
        return self.request(url, 'POSTFILE', files=files)

    def _http_put(self, url, body = None):
        self.request(url, 'PUT', body)[1]

