#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from urllib import quote
import urllib2

from setting import BASE_URL
##
authorize_url = 'https://graph.qq.com/oauth2.0/authorize'
token_url = 'https://graph.qq.com/oauth2.0/token'
callback_url = '%s/qqcallback'%BASE_URL

get_open_id_url = 'https://graph.qq.com/oauth2.0/me'
get_user_info_url = 'https://graph.qq.com/user/get_user_info'

##
def _obj_hook(pairs):
    o = JsonObject()
    for k, v in pairs.iteritems():
        o[str(k)] = v
    return o

class JsonObject(dict):
    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value

def _encode_params(**kw):
    args = []
    for k, v in kw.iteritems():
        qv = v.encode('utf-8') if isinstance(v, unicode) else str(v)
        args.append('%s=%s' % (k, quote(qv)))
    return '&'.join(args)

class APIClient(object):
    def __init__(self, app_key, app_secret, redirect_uri=None, response_type='code'):
        self.client_id = app_key
        self.client_secret = app_secret
        self.redirect_uri = redirect_uri
        self.response_type = response_type
        self.access_token = None

    def get_authorize_url(self):
        return '%s?%s' % (authorize_url, \
                _encode_params(client_id = self.client_id, \
                        response_type = 'code', \
                        scope = 'get_user_info', \
                        redirect_uri = callback_url))

    def request_access_token(self, code):
        data = _encode_params(grant_type='authorization_code', \
                    client_id = self.client_id, \
                    client_secret= self.client_secret, \
                    code= code, \
                    state= 'gobaby', \
                    redirect_uri = callback_url)
        req = urllib2.Request("%s?%s"%(token_url, data))
        response = urllib2.urlopen(req)
        content = response.read()
        ##access_token=D503B95E21F0D70BC121EC2D96C90F78&expires_in=7776000
        if content and 'access_token' in content:
            ps = content.split('&')
            c_dic = {}
            for p in ps:
                pkv = p.split('=')
                c_dic[pkv[0]] = pkv[1]
            return c_dic
        else:
            return {}
    
    def get_open_id(self, access_token):
        req = urllib2.Request("%s?access_token=%s"% (get_open_id_url, access_token))
        response = urllib2.urlopen(req)
        content = response.read()
        if content:
            content = content.replace('callback(','').replace(');','')
            jdata = json.loads(content)
            return jdata['openid']
        else:
            return None
    
    def get_user_info(self, access_token, openid):
        '''
        return { "ret":0, "msg":"", "nickname":"qq name", "figureurl":"http://qzapp.qlogo.cn/qzapp/100254539/5BDCA5E6321B273E44720E532B1379ED/30", "figureurl_1":"http://qzapp.qlogo.cn/qzapp/100254539/5BDCA5E6321B273E44720E532B1379ED/50", "figureurl_2":"http://qzapp.qlogo.cn/qzapp/100254539/5BDCA5E6321B273E44720E532B1379ED/100", "gender":"男", "vip":"0", "level":"0" }
        '''
        data = _encode_params(access_token = access_token, oauth_consumer_key = self.client_id, openid = openid)
        req = urllib2.Request("%s?%s"%(get_user_info_url,data))
        response = urllib2.urlopen(req)
        content = response.read()
        if content:
            return json.loads(content, object_hook=_obj_hook)
        else:
            return None
