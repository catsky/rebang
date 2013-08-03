# -*- coding: utf-8 -*-
import logging
import os.path
import re
import tornado.web

from time import mktime, time
from datetime import datetime, timedelta

import tenjin
from tenjin.helpers import *
from tenjin.html import nl2br

from setting import *

import pylibmc
mc = pylibmc.Client()

###
def cur_time():
    return int(time())

def encode_dict(my_dict):
    newdict = {}
    for k in my_dict:
        #newdict[str(k)] = str(my_dict[k]).encode('utf-8')
        newdict[str(k)] = my_dict[k].encode('utf-8') if isinstance(my_dict[k], unicode) else str(my_dict[k])
    return "\x1e".join("%s\x1f%s" % x for x in newdict.iteritems())

def decode_dict(my_string):
    return dict(x.split("\x1f") for x in my_string.split("\x1e"))

def dict2utf8(my_dict):
    newdict = {}
    for k in my_dict:
        newdict[str(k)] = str(my_dict[k]).encode('utf-8')
        #newdict[str(k)] = my_dict[k].encode('utf-8') if isinstance(my_dict[k], unicode) else str(my_dict[k])
    return newdict

_re_html=re.compile('<.*?>|\&.*?\;', re.UNICODE|re.I|re.M|re.S)
def textilize(s):
    return _re_html.sub("", s).strip()

#_re_call = re.compile(r'@([a-z0-9]+)', re.UNICODE|re.I|re.M|re.S)
#_re_call = re.compile(r'(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9]+)', re.UNICODE|re.I|re.M|re.S)
_re_call = re.compile(r'\B\@([a-z0-9]+)', re.UNICODE|re.I|re.M|re.S)#同上
def call_member(text):
    members = _re_call.findall(text)
    if len(members) > 0:
        #for member in members:
        #    logging.error(member)
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
    """
    Converts any URLs in text into clickable links. Works on http://, https:// and
    www. links. Links can have trailing punctuation (periods, commas, close-parens)
    and leading punctuation (opening parens) and it'll still do the right thing.

    If trim_url_limit is not None, the URLs in link text will be limited to
    trim_url_limit characters.

    If nofollow is True, the URLs in link text will get a rel="nofollow" attribute.
    """
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
    
def safe_encode(con):
    return con.replace("<","&lt;").replace(">","&gt;")

def safe_decode(con):
    return con.replace("&lt;","<").replace("&gt;",">")

def clear_cache_multi(pathlist = None):
    if pathlist:
        mc.delete_multi([str(p) for p in pathlist])

def clear_all_cache():
    mc.flush_all()

def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(int(timestamp))

def date_web(timestamp):
    it = int(timestamp)
    if (int(time())-it)<31536000:#365day
        time1 = datetime.fromtimestamp(it)
        time_diff = (datetime.utcnow() + timedelta(hours =+ 8)) - time1
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
        return datetime.fromtimestamp(it).strftime('%Y-%m-%d %H:%M:%S')

def date_web2(timestamp):
    #2011-12-12 23:26:41
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

def date_item(timestamp):
    #2011-12-12
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')

#
def memcached(key, cache_time=DEFAULT_CACHE_TIME, key_suffix_calc_func=None):
    def wrap(func):
        def cached_func(*args, **kw):
            
            key_with_suffix = key
            if key_suffix_calc_func:
                key_suffix = key_suffix_calc_func(*args, **kw)
                if key_suffix is not None:
                    key_with_suffix = '%s:%s' % (key, key_suffix)
            
            key_with_suffix = str(key_with_suffix)
            
            mc = pylibmc.Client()
            value = mc.get(key_with_suffix)
            if value is None:
                value = func(*args, **kw)
                mc.set(key_with_suffix, value, cache_time)
            return value
        return cached_func
    return wrap

###
engine = tenjin.Engine(path=[os.path.join('templates', THEME), 'templates'], cache=tenjin.MemoryCacheStorage(), preprocess=True)
class BaseHandler(tornado.web.RequestHandler):
    
    __SPIDER_PATTERN = re.compile('(bot|crawl|spider|slurp|sohu-search|lycos|robozilla|google)', re.I)
    
    def render(self, template, context=None, globals=None, layout=False):
        if context is None:
            context = {}
        context.update({
            'cur_user':self.cur_user(),
            'is_spider': self.is_spider(),
            'request': self.request,
        })
        
        context['qq_login_url'] = ''
        if USER_MODEL in [1,3]:
            if not context['cur_user']:
                from qqweibo import APIClient as qqAPIClient
                qqclient = qqAPIClient(app_key=QQ_APP_ID, app_secret=QQ_APP_KEY)
                context['qq_login_url'] = qqclient.get_authorize_url()
                #建议把qq_login_url 值设为静态（如下示例），并把上面三行屏蔽掉
                #context['qq_login_url'] = 'https://graph.qq.com/oauth2.0/authorize?scope=get_user_info&redirect_uri=http%3A//myskoda.sinaapp.com/qqcallback&response_type=code&client_id=100305902'
        
        return engine.render(template, context, globals, layout)
    
    def echo(self, template, context=None, globals=None, layout=False):
        self.write(self.render(template, context, globals, layout))
        
    @memcached('cur_user', 600, lambda self: self.get_cookie('username', ''))
    def cur_user(self):
        user_name_cookie = self.get_cookie('username','')
        user_code_cookie = self.get_cookie('usercode','')
        if user_name_cookie and user_code_cookie:
            from model import Member
            return Member.check_loged_user(user_name_cookie, user_code_cookie)
        else:
            return None
    
    def is_spider(self):
        user_agent = self.request.headers.get('user-agent','')
        return self.__SPIDER_PATTERN.search(user_agent) is not None    

def authorized(url='/login', flag = 2):
    def wrap(handler):
        def authorized_handler(self, *args, **kw):
            request = self.request
            user_name_cookie = self.get_cookie('username','')
            user_code_cookie = self.get_cookie('usercode','')
            if user_name_cookie and user_code_cookie:
                from model import Member
                user = Member.check_loged_user(user_name_cookie, user_code_cookie, flag)
            else:
                user = False
            if request.method == 'GET':
                if not user:
                    self.redirect(url)
                    return False
                else:
                    handler(self, *args, **kw)
            else:
                if not user:
                    self.set_status(403)
                    #self.error(403)
                else:
                    handler(self, *args, **kw)
        return authorized_handler
    return wrap
