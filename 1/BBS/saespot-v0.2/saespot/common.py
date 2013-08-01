# -*- coding: utf-8 -*-

import logging
import re
import os.path
from traceback import format_exc
from urllib import unquote, quote
from time import mktime, time
from datetime import datetime, timedelta

from google.appengine.api import memcache

import tenjin
from tenjin.helpers import *
from tenjin.html import nl2br

import yui

from setting import *

#####

def unquoted_unicode(string, coding='utf-8'):
    return unquote(string).decode(coding)

def quoted_string(unicode, coding='utf-8'):
    return quote(unicode.encode(coding))

def cur_time():
    return int(time())

def safe_encode(con):
    return con.replace("<","&lt;").replace(">","&gt;")

def safe_decode(con):
    return con.replace("&lt;","<").replace("&gt;",">")

_re_html=re.compile('<.*?>|\&.*?\;', re.UNICODE|re.I|re.M|re.S)
def textilize(s):
    return _re_html.sub("", s).strip()

_re_call = re.compile(r'\B\@([a-z0-9]+)', re.UNICODE|re.I|re.M|re.S)#同上
def call_member(text):
    members = _re_call.findall(text)
    if len(members) > 0:
        return set([member for member in members])
    else:
        return None

# autolink
import string
LEADING_PUNCTUATION  = ['(', '<', '&lt;']
TRAILING_PUNCTUATION = ['.', ',', ')', '>', '\n', '&gt;']
punctuation_re = re.compile('^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % \
    ('|'.join([re.escape(x) for x in LEADING_PUNCTUATION]),
    '|'.join([re.escape(x) for x in TRAILING_PUNCTUATION])))
word_split_re = re.compile(r'(\s+)')
simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')
def autolink(text, trim_url_limit=None, nofollow=True):
    trim_url = lambda x, limit=trim_url_limit: limit is not None and (x[:limit] + (len(x) >=limit and '...' or ''))  or x
    words = word_split_re.split(text)
    nofollow_attr = nofollow and ' rel="nofollow"' or ''
    for i, word in enumerate(words):
        match = punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            if middle.startswith('www.') or ('@' not in middle and not middle.startswith('http://') and not middle.startswith('https://') and \
                    len(middle) > 0 and middle[0] in string.letters + string.digits and \
                    (middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
                middle = '<a href="http://%s"%s target="_blank">%s</a>' % (middle, nofollow_attr, trim_url(middle))
            if middle.startswith('http://') or middle.startswith('https://'):
                middle = '<a href="%s"%s target="_blank">%s</a>' % (middle, nofollow_attr, trim_url(middle))
            if '@' in middle and not middle.startswith('www.') and not ':' in middle \
                and simple_email_re.match(middle):
                middle = '<a href="mailto:%s">%s</a>' % (middle, middle)
            if lead + middle + trail != word:
                words[i] = lead + middle + trail
    return ''.join(words)

# autolink end

#_re_imgs = re.compile('(http[s]?://?\S*\w\.(jpg|jpe|jpeg|gif|png))\w*', re.UNICODE|re.I|re.M|re.S)
_re_imgs = re.compile('(http[s]?://?[^ \f\n\r\t\v\?]*\w\.(jpg|jpe|jpeg|gif|png))\w*', re.UNICODE|re.I|re.M|re.S)
_re_mentions = re.compile('\B\@([a-z0-9]+)', re.UNICODE|re.I|re.M|re.S)
#http://v.youku.com/v_show/id_XNDQ4NTk5OTQw(.htm|.html)?
_re_youku = re.compile('http://v.youku.com/v_show/id_([a-zA-Z0-9\=]+)(\/|.html?)?', re.UNICODE|re.I|re.M|re.S)
#http://www.tudou.com/listplay/7cb57rueaYI/Op-E8hQrdRw(.htm|.html)?
#http://www.tudou.com/listplay/7cb57rueaYI
#http://www.tudou.com/programs/view/ro1Yt1S75bA/
_re_tudou = re.compile('http://www.tudou.com/(programs/view|listplay)/([a-zA-Z0-9\=\_\-]+)(\/|.html?)?', re.UNICODE|re.I|re.M|re.S)
#qq http://v.qq.com/boke/page/h/1/n/h04021dkn1n.html
_re_qq = re.compile('http://v.qq.com/(.+)/([a-zA-Z0-9]{8,}).(html?)', re.UNICODE|re.I|re.M|re.S)
#_re_urls = re.compile('(\w+:\/\/[^\s]+)', re.UNICODE|re.I|re.M|re.S)
_re_urls = re.compile('(\w+:\/\/[^\s]+)', re.UNICODE|re.I|re.M|re.S)
_re_gist = re.compile('(https?://gist.github.com/[\d]+)', re.UNICODE|re.I|re.M|re.S)
def content_formate(text, is_spider=False):
    #auto img
    if _re_imgs.search(text):
        if not is_spider:
            text = _re_imgs.sub(r'<img src="/static/grey2.gif" data-original="\1" alt="" />', text)
        else:
            text = _re_imgs.sub(r'<img src="\1" alt="" />', text)
    #mentions
    if '@' in text:
        #logging.error([yk for yk in _re_mentions.findall(text)])
        #for yk in _re_mentions.findall(text):
        #    logging.error(yk)
        text = _re_mentions.sub(r'@<a href="/member/\1">\1</a>', text)
    #youku
    if 'v.youku.com' in text:
        text = _re_youku.sub(r'<embed src="http://player.youku.com/player.php/sid/\1/v.swf" quality="high" width="590" height="492" align="middle" allowScriptAccess="sameDomain" type="application/x-shockwave-flash"></embed>', text)
    #tudou
    if 'www.tudou.com' in text:
        text = _re_tudou.sub(r'<embed src="http://www.tudou.com/v/\2/&resourceId=0_05_05_99&iid=152278332&bid=05/v.swf" quality="high" width="590" height="492" align="middle" allowScriptAccess="sameDomain" type="application/x-shockwave-flash"></embed>', text)
    #qq
    if 'v.qq.com' in text:
        text = _re_qq.sub(r'<embed src="http://static.video.qq.com/TPout.swf?vid=\2&auto=0" allowFullScreen="true" quality="high" width="590" height="492" align="middle" allowScriptAccess="always" type="application/x-shockwave-flash"></embed>', text)
    #gist
    if '://gist' in text:
        text = _re_gist.sub(r'<script src="\1.js"></script>',text)
    #url
    if 'http' in text:
        return autolink(text)
        #text = _re_urls.sub(r'<a href="\1" rel="nofollow" target="_blank">\1</a>', text)
    return text

def findall_mentions(text, filter_name=None):
    if '@' in text:
        ns = set([yk for yk in _re_mentions.findall(text.lower())])
        if filter_name:
            ns.discard(filter_name)
        if len(ns)<=NOTIFY_MEMBER_NUM:
            return ns
        else:
            return None
    else:
        return None

def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(int(timestamp))

def date_web(timestamp):
    it = int(timestamp)
    if (int(time())-it)<31536000:#365day
        time1 = datetime.fromtimestamp(it)
        #time_diff = (datetime.utcnow() + timedelta(hours =+ 8)) - time1
        time_diff = datetime.utcnow() - time1
        days = time_diff.days
        if days:
            if days > 60:
                return '%s 月前' % (days / 30)
            if days > 30:
                return '1 月前'
            if days > 14:
                return '%s 周前' % (days / 7)
            if days > 7:
                return '1 周前'
            if days > 1:
                return '%s 天前' % days
            return '1 天前'
            
        seconds = time_diff.seconds
        if seconds > 7200:
            return '%s 小时前' % (seconds / 3600)
        if seconds > 3600:
            return '1 小时前'
        if seconds > 120:
            return '%s 分钟前' % (seconds / 60)
        if seconds > 60:
            return '1 分钟前'
        if seconds > 1:
            return '%s 秒钟前' %seconds
        return '%s 秒钟前' % seconds
        
    else:
        return (datetime.fromtimestamp(it) + timedelta(hours =+ 8)).strftime('%Y-%m-%d %H:%M:%S')

def date_web2(timestamp):
    #2011-12-12 23:26:41
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

def date_item(timestamp):
    #2011-12-12
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')

def obj_runput(obj, keys=None):
    obj.put()
    if obj.is_saved() and keys:
        memcache.delete_multi(keys)
    return obj

def memcached(key, cache_time, key_suffix_calc_func=None, namespace=None):
    def wrap(func):
        def cached_func(*args, **kw):
            key_with_suffix = key

            if key_suffix_calc_func:
                key_suffix = key_suffix_calc_func(*args, **kw)
                if key_suffix:
                    key_with_suffix = '%s:%s' % (key, key_suffix)

            value = memcache.get(key_with_suffix, namespace)
            if not value:
                value = func(*args, **kw)
                memcache.set(key_with_suffix, value, cache_time, namespace)
            return value
        return cached_func
    return wrap
    
###
engine = tenjin.Engine(path=[os.path.join('templates', THEME), 'templates'], cache=tenjin.MemoryCacheStorage(), preprocess=True)

class BaseHandler(yui.HtmlRequestHandler):
   
    def render(self, template, context=None, globals=None, layout=False):
        return engine.render(template, context, globals, layout)
    
    def echo(self, template, context=None, globals=None, layout=False):
        if context is None:
            context = {'request': self.request}
        else:
            context['request'] = self.request
        context['cur_user'] = self.cur_user#()
        if self.request.user and not context['cur_user'] and self.request.path != '/setname':
            self.redirect('/setname')
            return
        self.write(self.render(template, context, globals, layout))
    
    @yui.CachedProperty
    @memcached('cur_user', 300, lambda self: self.request.user.user_id() if self.request.user else '')
    def cur_user(self):
        if self.request.user:
            from model import Member, GoogleUser
            req_user = self.request.user
            gu_obj = GoogleUser.get_or_insert(req_user.user_id())
            if gu_obj.name:
                return Member.get_by_key_name(gu_obj.name)
            return None
        else:
            return None
        
    def handle_exception(self, exception):
        logging.exception('Get an uncaught exception when processing request.')
        self.error(500)
        self.display_exception(exception)
    
    def display_exception(self, exception):
        self.echo('error.html', {
            'page': '500',
            'title': 'An unhandled error occurred',
            'h2': 'The server is temporary error now.',
            'msg': format_exc() if self.request.is_admin else "I don't know what has happened. You can try to refresh this page, if still has error, you can report to the administrator."
        })
    
    
