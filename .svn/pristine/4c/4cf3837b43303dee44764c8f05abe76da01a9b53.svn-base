# -*- coding: utf-8 -*-
'''
@author:    U{keakon<mailto:keakon@gmail.com>}
@license:   the MIT License, see details in LICENSE.txt
@version:   1.1.2
'''

from __future__ import with_statement
from datetime import datetime, timedelta
# You can import sha1 or other hash algorithms instead of md5
# 你可以引入sha1等其他散列算法来代替md5
from hashlib import md5
import logging
import re
from threading import RLock
from time import time
from traceback import format_exc
from urlparse import urljoin, urlunsplit
from zlib import crc32

from google.appengine.api import users
try:
    import webapp2 as webapp
except ImportError:
    from google.appengine.ext import webapp
from webob.multidict import MultiDict


# HTTP status codes
# HTTP状态码
HTTP_STATUS = {
    100: 'Continue',
    101: 'Switching Protocols',
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Large',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    428: 'Precondition Required',
    429: 'Too Many Requests',
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    511: 'Network Authentication Required'
}


class Property(object):
    '''
    Return a property attribute for new-style classes.
    It only implement __get__ method, so you are free to set __dict__ to
    override this property.
    That's the only reason you would like to use it instead of the build-in
    property function.

    将方法封装成一个属性，适用于新风格的类。
    由于只实现了__get__方法，所以你可以自由地设置__dict__，以覆盖对它的访问。
    这也是你采用它，而不使用内建的property函数的唯一原因。
    '''

    def __init__(self, fget):
        '''
        @type fget: function
        @param fget: the function for getting an attribute value

        用于获取属性的函数
        '''
        self.fget = fget
        self.__doc__ = fget.__doc__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError, 'unreadable attribute'
        return self.fget(obj)


class CachedProperty(Property):
    '''
    Return a property attribute for new-style classes.
    It works the same as Property, except caching the calculated property to its __dict__.

    将方法封装成一个属性，适用于新风格的类。
    作用与Property相同，不同之处是会把计算出来的属性缓存到__dict__。
    '''

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        fget = self.fget
        if fget is None:
            raise AttributeError, 'unreadable attribute'
        obj.__dict__[fget.__name__] = prop = fget(obj)
        return prop


class Request(webapp.Request):
    '''
    A simple request class with automatic Google Account authentication.
    It's derived from webapp.Request, so you can use any methods and attributes
    of webapp.Request.

    可自动验证Google账号的请求类。
    继承自webapp.Request，因此你可使用所有webapp.Request的方法和属性。
    '''

    __SPIDER_PATTERN = re.compile('(bot|crawl|spider|slurp|sohu-search|lycos|robozilla)', re.I)

    @CachedProperty
    def user(self):
        '''
        the current user of this request

        发出请求的当前用户
        '''
        return users.get_current_user()
    
    @CachedProperty
    def login_logout_link(self):
        if self.user:
            return u'<a href="%s">退出</a>' % users.create_logout_url("/")
        else:
            return u'<a href="%s">用Google帐户登录</a>' % users.create_login_url(self.uri)
    

    @CachedProperty
    def is_admin(self):
        '''
        whether the current user is admin

        当前用户是否是管理员
        '''
        return users.is_current_user_admin()

    @CachedProperty
    def is_system(self):
        '''
        whether the current request is sent by Google App Engine system,
        such as cron jobs, task queue, email handler and so on.

        当前请求是否由Google App Engine系统发出，
        例如计划任务、任务队列和邮件处理器等。
        '''
        return self.remote_addr[:2] == '0.'

    @CachedProperty
    def ua_details(self):
        '''
        parse browser, platform, os and vendor from user agent.

        从user agent解析浏览器、平台、操作系统和产商信息。

        @rtype: string
        @return: tuple of browser, platform, os, os_version and vendor

        browser, platform, os, os_version, vendor组成的元组
        '''
        user_agent = self.user_agent
        os = ''
        os_version = ''
        browser = ''
        platform = ''
        vendor = ''
        if user_agent:
            if 'iPad' in user_agent:
                os = 'iOS'
                platform = 'iPad'
                vendor = 'Apple'
            elif 'iPod' in user_agent:
                os = 'iOS'
                platform = 'iPod Touch'
                vendor = 'Apple'
            elif 'iPhone' in user_agent:
                os = 'iOS'
                platform = 'iPhone'
                vendor = 'Apple'
            elif 'Android' in user_agent:
                os = platform = 'Android'
            elif 'BlackBerry' in user_agent:
                os = 'BlackBerry OS'
                platform = 'BlackBerry'
                vendor = 'RIM'
            elif 'Palm' in user_agent:
                os = 'webOS'
                platform = 'Palm'
            elif 'Windows Phone' in user_agent:
                os = 'Windows CE'
                platform = 'Windows Phone'
            elif 'PSP' in user_agent:
                platform = 'PSP'
                vendor = 'Sony'
            elif 'Kindle' in user_agent:
                os = 'Linux'
                platform = 'Kindle'
            elif 'Nintendo' in user_agent or 'Nitro' in user_agent:
                platform = 'Wii'
                vendor = 'Nintendo'

            if not os:
                if 'Windows' in user_agent:
                    os = 'Windows'
                    if 'Windows NT 6.1' in user_agent:
                        os_version = 'Windows 7'
                    elif 'Windows NT 5.1' in user_agent:
                        os_version = 'Windows XP'
                    elif 'Windows NT 6.0' in user_agent:
                        os_version = 'Windows Vista'
                    elif 'Windows NT 5.2' in user_agent:
                        os_version = 'Windows Server 2003'
                    elif 'Windows NT 5.0' in user_agent:
                        os_version = 'Windows 2000'
                    elif 'Windows CE' in user_agent:
                        os_version = 'Windows CE'
                elif 'Macintosh' in user_agent or 'Mac OS' in user_agent:
                    os = 'Mac OS'
                    if 'Mac OS X' in user_agent:
                        os_version = 'Mac OS X'
                elif 'Linux' in user_agent:
                    os = 'Linux'
                elif 'FreeBSD' in user_agent:
                    os = 'FreeBSD'
                elif 'OpenBSD' in user_agent:
                    os = 'OpenBSD'
                elif 'Solaris' in user_agent:
                    os = 'Solaris'
                elif 'Symbian' in user_agent or 'SymbOS' in user_agent:
                    os = 'SymbianOS'
                    self.is_mobile = True
                    if 'Series60' in user_agent or 'S60' in user_agent:
                        os_version = 'SymbianOS Series60'
                    elif 'Series40' in user_agent or 'S40' in user_agent:
                        os_version = 'SymbianOS Series40'

            if not browser:
                if 'MSIE' in user_agent:
                    browser = 'Internet Explorer'
                elif 'Firefox' in user_agent:
                    browser = 'Firefox'
                elif 'Chrome' in user_agent:
                    browser = 'Chrome'
                elif 'Safari' in user_agent:
                    if 'Mobile' in user_agent:
                        browser = 'Mobile Safari'
                        self.is_mobile = True
                    else:
                        browser = 'Safari'
                elif 'Opera Mini' in user_agent:
                    browser = 'Opera Mini'
                    self.is_mobile = True
                elif 'Opera Mobi' in user_agent:
                    browser = 'Opera Mobile'
                    self.is_mobile = True
                elif 'Opera' in user_agent:
                    browser = 'Opera'
                elif 'UCWEB' in user_agent:
                    browser = 'UCWEB'
                    self.is_mobile = True
                elif 'IEMobile' in user_agent:
                    browser = 'IEMobile'
                    self.is_mobile = True

            if not vendor:
                if 'Nokia' in user_agent:
                    vendor = 'Nokia'
                elif 'motorola' in user_agent:
                    vendor = 'Motorola'
                elif 'Sony' in user_agent:
                    vendor = 'Sony'
                elif 'samsung' in user_agent.lower():
                    vendor = 'Samsung'
        return browser, platform, os, os_version, vendor

    @CachedProperty
    def is_mobile(self):
        '''
        whether the request is send by a mobile user agent

        发出请求的是否是手机浏览器
        '''
        environ = self.environ
        if 'HTTP_X_WAP_PROFILE' in environ or 'HTTP_PROFILE' in environ or 'X-OperaMini-Features' in environ or\
            self.first_match(('application/vnd.wap.xhtml+xml', 'text/vnd.wap.wml'), ''):
            return True

        user_agent = self.user_agent
        if user_agent:
            user_agent_lower = user_agent.lower()
            if 'phone' in user_agent_lower or 'mobi' in user_agent_lower or 'wap' in user_agent_lower:
                return True

            browser, platform, os, os_version, vendor = self.ua_details
            if platform or vendor:
                return True
            if 'is_mobile' in self.__dict__:
                return self.__dict__['is_mobile']

        return False

    @CachedProperty
    def is_spider(self):
        '''
        whether the current request is sent by a Search Engine spider.

        当前请求是否由搜索引擎的蜘蛛发出。
        '''
        return self.__SPIDER_PATTERN.search(self.user_agent) is not None

    @CachedProperty
    def client_ip(self):
        '''
        the client's IP, return "Unknown" when can't find out

        用户的IP

        @rtype: string
        @return: the client's IP or "Unknown" when can't find out

        用户的IP，若找不到，则返回"unknown"

        @note: The "HTTP_X_FORWARDED_FOR" variable may contain serveral IPs.

        "HTTP_X_FORWARDED_FOR"变量可能包含多个IP。
        '''
        environ = self.environ
        ip = environ.get('HTTP_X_REAL_IP', '') # if using nginx reverse proxy
        if ip:
            return ip
        ip = environ.get('HTTP_CLIENT_IP', '')
        if ip:
            return ip
        ip = environ.get('HTTP_X_FORWARDED_FOR', '')
        if ip:
            return ip
        return environ.get('REMOTE_ADDR', 'unknown')

    def first_match(self, mime_types, fallback='text/html'):
        '''
        Get the first match in the mime_types that is allowed.

        获取mime_types中第一个允许的MIME类型。

        @type mime_types: sequence
        @param mime_types: a sequence for match

        用于匹配的序列

        @type fallback: string
        @param fallback: the default MIME type if nothing is matched

        当找不到匹配的类型时，返回该默认的MIME类型

        @rtype: string
        @return: the first match in the mime_types or
        fallback if not matched

        第一个匹配的MIME类型；若都不匹配，则返回fallback
        '''
        accept = self.accept.best_matches()
        for mime_type in mime_types:
            if mime_type in accept:
                return mime_type
        return fallback


class ResponseHeader(object):
    '''
    A mapping-like object which wraps response headers.
    It's a litter faster than wsgiref.headers.Headers and
    webob.headerdict.HeaderDict, because all the fields is treat as
    single-valued except "Set-Cookie".
    The disadvantage is you can't use it to handle multi-valued fields
    like "Warning", but you almost won't use these fields.

    一个类似于字典的，用于封装响应头的对象。
    它比wsgiref.headers.Headers和webob.headerdict.HeaderDict稍快，
    原因是除了"Set-Cookie"，其他都当成单值来处理了。
    缺点就是你无法用它处理多值字段，例如"Warning"，但你几乎不会用到这些字段。
    '''

    def __init__(self, header=None, cookie=()):
        '''
        Initialize all header fields.

        初始化所有的头字段。

        @type header: dict
        @param header: a dict object contains all header fields

        包含所有头字段的字典对象

        @type cookie: list
        @param cookie: a list object contains all cookie fields

        包含所有cookie的列表对象
        '''
        cookie = [('Set-Cookie', value) for value in cookie]

        _header = {}
        if header:
            for name, value in header.iteritems():
                if value is not None:
                    name = self._valid_name(name)
                    if name != 'Set-Cookie':
                        _header[name] = value
                    else:
                        cookie.append(('Set-Cookie', value))

        self.__header = _header
        self.__cookie = cookie

    def __getitem__(self, name):
        '''
        Get the header field by name.

        根据名称获取头字段。

        @type name: string
        @param name: the name of the header field (case-insensitive)

        字段的名称（大小写不敏感）

        @rtype: string
        @return: the corresponding header field value of the name,
        or None if hasn't been set

        返回对应的头字段，如果未设置的话，则为None

        @note: If you try to get "Set-Cookie" fields, it will return a list of
        cookies' value or None. You'd better use L{get_cookies} method instead.

        如果你使用这个方法来获取"Set-Cookie"字段，它将会返回所有cookie的值或None。
        你最好是用L{get_cookies}方法来代替。
        '''
        name = self._valid_name(name)
        if name != 'Set-Cookie':
            return self.__header.get(name, None)
        else:
            return [cookie[1] for cookie in self.__cookie] or None

    def __setitem__(self, name, value):
        '''
        Set the header field by name.

        设置一个头字段。

        @type name: string
        @param name: the name of the header field (case-insensitive)

        字段的名称（大小写不敏感）

        @type value: string
        @param value: the value of the header field,
        if it's None, the field will be deleted

        字段的名称，若为None，该字段将被删除

        @note: There is a better way to add "Set-Cookie" fields: L{add_cookie}.

        还有个更方便的L{add_cookie}方法可以添加"Set-Cookie"字段。
        '''
        name = self._valid_name(name)
        if name != 'Set-Cookie':
            if value is not None:
                self.__header[name] = value
            else:
                self.__header.pop(name, None)
        else:
            if value is not None:
                self.__cookie = [('Set-Cookie', value)]
            else:
                self.__cookie = []

    def __delitem__(self, name):
        '''
        Delete a header field by name.
        It won't raise a KeyError exception if the field is not exist.

        根据名称来删除头字段。
        如果字段不存在，不会引发KeyError异常。

        @type name: string
        @param name: the name of the header field (case-insensitive)

        字段的名称（大小写不敏感）
        '''
        name = self._valid_name(name)
        if name != 'Set-Cookie':
            self.__header.pop(name, None)
        else:
            self.__cookie = []

    def __contains__(self, name):
        '''
        Test whether a header field is exist.

        @type name: string
        @param name: the name of the header field (case-insensitive)

        字段的名称（大小写不敏感）

        @rtype: bool
        @return: True if exist, otherwise False

        返回对应的头字段，如果未设置的话，则为None
        '''
        name = self._valid_name(name)
        if name != 'Set-Cookie':
            return name in self.__header
        else:
            return self.__cookie != []

    def setdefault(self, name, default_value):
        '''
        Set and return a header field if hasn't been set.

        当头字段未被设置时，设置并返回它。

        @type name: string
        @param name: the name of the header field (case-insensitive)

        字段的名称（大小写不敏感）

        @type default_value: string
        @param default_value: the default value should be returned if the field hasn't
        been set

        如果该字段未设置，则返回该默认值

        @rtype: string or None
        @return: the corresponding header field value of the name,
        or default_value if hasn't been set

        返回对应的头字段，如果未设置的话，则为default_value

        @attention: Do B{not} use this method to set "Set-Cookie" fields,
        you should use L{add_cookie} method instead.

        B{请勿}使用这个方法设置"Set-Cookie"字段，你应该用L{add_cookie}方法来代替。
        '''
        name = self._valid_name(name)
        if name != 'Set-Cookie':
            if default_value is not None:
                return self.__header.setdefault(name, default_value)
            else:
                return self.__header.get(name, None)
        else:
            if self.__cookie != []:
                return [cookie[1] for cookie in self.__cookie]
            elif default_value is not None:
                self.__cookie = [('Set-Cookie', default_value)]
                return [default_value]
            else:
                return None

    def pop(self, name, default_value=None):
        '''
        Remove the header field by name and return it.

        移除一个头字段，并返回它。

        @type name: string
        @param name: the name of the header field (case-insensitive)

        字段的名称（大小写不敏感）

        @type default_value: string
        @param default_value: the default value should be returned if the field hasn't
        been set

        如果该字段未设置，则返回该默认值

        @rtype: string
        @return: the corresponding header field value of the name,
        or default_value if hasn't been set

        返回对应的头字段，如果未设置的话，则为default_value
        '''
        name = self._valid_name(name)
        if name != 'Set-Cookie':
            return self.__header.pop(name, default_value)
        else:
            if self.__cookie != []:
                cookie = [cookie[1] for cookie in self.__cookie]
                self.__cookie = []
                return cookie
            else:
                return None

    def add_cookie(self, name, value, expires=None, path=None, domain=None, secure=False, httponly=False):
        '''
        Add a "Set-Cookie" field.

        添加一个"Set-Cookie"字段。

        @type name: string
        @param name: the name of the cookie

        cookie的名称

        @type value: string
        @param value: the value of the cookie

        cookie的值

        @type expires: string, int or datetime
        @param expires: the time the cookie expires,
        if it's type is int, it will be set to current time plus expires seconds

        cookie的有效期，如果类型为int，将被设为当前时间 + expires秒

        @type domain: string
        @param domain: the domain that the cookie is available

        cookie的有效域

        @type secure: bool
        @param secure: indicates that the cookie should only be transmitted over
        a secure HTTPS connection from the client

        指明这个cookie只应该通过安全的HTTPS链接传送

        @type httponly: bool
        @param httponly: the cookie will be made accessible only through the
        HTTP protocol if True, so the cookie won't be accessible by scripting
        languages, such as JavaScript (not supported by all browsers)

        如果为True，则只能通过HTTP协议来访问这个cookie，而不能通过其他的脚本，
        例如JavaScript（并非所有浏览器都支持这个参数）

        @note: This method is U{Netscape cookie specification
        <http://devedge-temp.mozilla.org/library/manuals/2000/javascript/1.3/reference/cookies.html>}
        compatible only, because IE 6 dosen't support U{RFC 2109
        <http://www.ietf.org/rfc/rfc2109.txt>},
        while Firefox 3.5 dosen't support U{RFC 2965
        <http://www.ietf.org/rfc/rfc2965.txt>} either.

        这个方法只兼容Netscape cookie草案，因为IE 6不支持RFC 2109，
        而Firefox 3.5也不支持RFC 2965。
        '''
        cookie = ['%s=%s' % (name, value)]
        if expires is not None:
            if isinstance(expires, int):
                cookie.append((datetime.utcnow() + timedelta(seconds=expires)).strftime('expires=%a, %d-%b-%Y %H:%M:%S GMT'))
            elif isinstance(expires, datetime):
                cookie.append(expires.strftime('expires=%a, %d-%b-%Y %H:%M:%S GMT'))
            else:
                cookie.append('expires=' + expires)

        if path:
            cookie.append('path=' + path)

        if domain:
            cookie.append('domain=' + domain)

        if secure:
            cookie.append('secure')

        if httponly:
            cookie.append('HttpOnly')

        self.__cookie.append(('Set-Cookie', '; '.join(cookie)))

    def get_cookies(self):
        '''
        Get all "Set-Cookie" fields.

        获取所有的"Set-Cookie"字段。

        @rtype: list
        @return: a list of ('Set-Cookie', cookie content) tuples

        由('Set-Cookie', cookie内容)组成的列表
        '''
        return self.__cookie[:]

    def clear_cookies(self):
        '''
        Clear all "Set-Cookie" fields.

        清除所有的"Set-Cookie"字段。
        '''
        self.__cookie = []

    def items(self):
        '''
        Get all header fields.

        获取所有的头字段。

        @rtype: list
        @return: a list of (field name, field value) tuples

        由(字段名, 字段值)组成的列表
        '''
        return self.__header.items() + self.__cookie

    def clear(self):
        '''
        Clear all the header fields.

        清空所有头字段。
        '''
        self.__header = {}
        self.__cookie = []

    def __len__(self):
        '''
        Get the amount of all the header fields.

        获得所有头字段的总数。

        @rtype: int
        @return: the amount of all the header fields

        所有头字段的总数
        '''
        return len(self.__header) + len(self.__cookie)

    @staticmethod
    def _valid_name(name):
        '''
        Get the valid header field name.

        获得有效的头字段名。

        @type name: string
        @param name: the name of the header field (case-insensitive)

        字段的名称（大小写不敏感）

        @rtype: string
        @return: the valid header field name

        有效的头字段名
        '''
        name = name.title()
        if name == 'Etag':
            return 'ETag'
        if name == 'X-Xss-Protection':
            return 'X-XSS-Protection'
        if name == 'Www-Authenticate':
            return 'WWW-Authenticate'
        if name == 'Content-Md5':
            return 'Content-MD5'
        return name

    def copy(self):
        '''
        @rtype: ResponseHeader
        @return: a copy of this response header.

        该响应的复本。
        '''
        header = ResponseHeader()
        header.__header = self.__header.copy()
        header.__cookie = self.__cookie[:]
        return header


class Response(object):
    '''
    The response class which used to contain and handle the response content.

    用于存储和处理响应内容的响应类。
    '''

    def __init__(self, start_response, status=200, header=None, body=''):
        '''
        @type start_response: function
        @param start_response: the WSGI-compatible start_response function for
        sending response

        WSGI兼容的start_response函数，用于输出响应

        @type status: int
        @param status: the HTTP status code

        HTTP状态码

        @type header: ResponseHeader
        @param header: the response header

        响应头

        @type body: str
        @param body: the response body

        响应体
        '''
        self._start_response = start_response
        self.status = status
        self.header = ResponseHeader() if header is None else header
        if not body:
            self.body = ''
        elif isinstance(body, str):
            self.body = body
        elif isinstance(body, unicode):
            self.body = body.encode('UTF-8')
        else:
            self.body = str(body)

    def set_content_type(self, mime_type='text/html', charset='UTF-8'):
        '''
        Set the "Content-Type" header field.

        设置"Content-Type"头字段。

        @type mime_type: string
        @param mime_type: the MIME type of output content,
        these abbreviative notations are also available: xhtml, wap, wap2, json,
        atom, rss.

        输出内容的MIME类型，支持如下缩写：xhtml、wap、wap2、json、atom、rss。

        @type charset: string
        @param charset: the charset of output content

        输出内容的字符集
        '''
        if mime_type != 'text/html':
            if mime_type == 'xhtml':
                mime_type = self.handler.request.first_match(('application/xhtml+xml',), 'text/html')
            elif mime_type == 'wap':
                mime_type = 'text/vnd.wap.wml'
            elif mime_type == 'wap2':
                mime_type = self.handler.request.first_match(('application/vnd.wap.xhtml+xml', 'application/xhtml+xml'), 'text/html')
            elif mime_type == 'json':
                mime_type = 'application/json'
            elif mime_type == 'atom':
                mime_type = 'application/atom+xml'
                charset = ''
            elif mime_type == 'rss':
                mime_type = 'application/rss+xml'
                charset = ''

        self.header['Content-Type'] = '%s; charset=%s' % (mime_type, charset) if charset else mime_type

    def set_cache(self, seconds, is_privacy=None):
        '''
        Set the user agent's cache strategy.

        设置用户代理的缓存策略。

        @type seconds: number
        @param seconds: how many seconds should this response be cached

        响应应被缓存多少秒

        @type is_privacy: bool or None
        @param is_privacy: whether the response can be stored in a shared
        cache.
        If it's None, it won't be cached by the edge cache of GAE;
        if False, it won't be cached by shared caches of proxies;
        if True, it can be cached by any cache.

        响应是否能存储在一个共享缓存里.
        若为None，将不会被GAE的边缘缓存所缓存；
        若为False，将不会被代理服务器的共享缓存所缓存；
        若为True，则可以被任何缓存所缓存。
        '''
        if seconds <= 0:
            self.header['Cache-Control'] = self.header['Pragma'] = 'no-cache'
            # fix localhost test for IE 6
            # for performance reason, you can remove next line in production server
            # 在本地开发服务器上用IE 6测试会出现bug
            # 如果是在生产服务器上使用的话，可以去掉下面这行代码，减小header的体积
            # 详情可见：http://www.keakon.cn/bbs/thread-1976-1-1.html
            self.header['Expires'] = 'Fri, 01 Jan 1990 00:00:00 GMT'
        else:
            if is_privacy:
                privacy = 'public, '
            elif is_privacy is None:
                privacy = ''
            else:
                privacy = 'private, '
            self.header['Cache-Control'] = '%smax-age=%s' % (privacy, seconds)

    def set_download_filename(self, filename):
        '''
        Set the file name to save the response content.

        设置用于保存响应内容的文件名。

        @type filename: str
        @param filename: the file name to save.

        用于保存的文件名。
        '''
        self.header['Content-Type'] = 'application/octet-stream'
        self.header['Content-Disposition'] = 'attachment; filename=%s' % filename

    def write(self, obj, encoding='utf-8'):
        '''
        Write an object to the output buffer.

        将对象写入缓存。

        @type obj: object
        @param obj: the object which should be written to the buffer.

        被写入缓存的对象。

        @type encoding: str, unicode, or object
        @param encoding: the unicode encoding.

        unicode对象的编码。

        @note: if the object type is not str or unicode, the str function will
        be called to represent its value.

        若对象类型不为str或unicode，会调用str函数来代表它的值。
        '''
        if isinstance(obj, str):
            self.body += obj
        elif isinstance(obj, unicode):
            self.body += obj.encode(encoding)
        else:
            self.body += str(obj)

    def get_status(self):
        '''
        Get HTTP status message from status code.

        从HTTP状态码中获取状态信息。

        @rtype: string
        @return: the HTTP status message

        HTTP状态信息
        '''
        return '%d %s' % (self.status, HTTP_STATUS[self.status])

    def clear(self):
        '''
        Clear the output buffer.

        清空输出缓存。
        '''
        self.body = ''

    def send(self):
        '''
        Output the response content to the user agent.
        You probably won't call it by yourself.

        将响应内容输出给用户代理。
        基本上你不需要手动去调用它。
        '''
        write = self._start_response(self.get_status(), self.header.items())

        if self.body:
            write(self.body)

    def copy(self, copy_header=True, start_response=None):
        '''
        Return a copy of this response, which is mainly used for caching.

        返回该响应的复本，主要用于缓存。

        @type start_response: function
        @param start_response: the start_response to be assigned to the copy.

        复本的start_response属性。

        @rtype: Response
        @return: a copy of this response.

        该响应的复本。
        '''
        return Response(start_response, self.status, self.header.copy() if copy_header else self.header, self.body)


class EtagResponse(Response):
    '''
    This EtagResponse class can automaticlly handle "If-None-Match" header field,
    send Etag header and decide whether set 304 HTTP status code.
    It can save transport bytes and time, but takes more CPU time.

    这个EtagResponse类可以自动处理"If-None-Match"头字段，发出ETag头，并决定是否设置
    304 HTTP状态码。
    这可以节省传输的字节数和时间，但会使用更多的CPU时间。

    @warning: Do B{not} manually set 304 status code by yourself, otherwise you should
    use L{Response} class instead.

    请B{不要}自行手动设置304状态码，否则请用L{Response}类来代替。
    '''

    def __init__(self, start_response, status=200, header=None, body='', _mime='', _status=200, _last_modified=None):
        '''
        @type _mime: string
        @param _mime: a backup of the MIME type

        MIME类型的备份

        @type _status: int
        @param _status: a backup of the HTTP status code

        HTTP状态码的备份

        @type _last_modified: datetime
        @param _last_modified: the last modified time

        最后被修改的时间
        '''
        super(EtagResponse, self).__init__(start_response, status, header, body)
        self._mime = _mime
        self._status = _status
        self._last_modified = _last_modified

    def set_last_modified(self, last_modified):
        '''
        Set the "Last-Modified" header field.
        设置"Last-Modified"头字段。

        @type last_modified: datetime, basestring, or int
        @param last_modified: the last modified time.
        If its type is basestring, it will be be convert to datetime object using
        '%a, %d %b %Y %H:%M:%S GMT' format.
        If its type is int, it will be be convert to current datetime plus
        last_modified seconds (can be negative).

        最后被修改的时间。
        若类型为basestring，将使用'%a, %d %b %Y %H:%M:%S GMT'格式来转换成datetime对象。
        若类型为int，将转换成当前datetime加last_modified秒(可为负数)。

        @note: In most cases, you needn't set the "Last-Modified" header field,
        EtagResponse will generate an "ETag" header field for the same use.

        绝大多数情况下，你无需自行设置"Last-Modified"，EtagResponse会自动生成一个
        "Etag"头字段作为相同用途。

        @attention: Whenever "Etag" matches "If-None-Match" or "Last-Modified"
        is no latter than "If-Modified-Since", EtagResponse will set status to 304.
        It's not meet the standard, but more efficient. If you insist on meeting
        it, don't set "Last-Modified" and use "ETag" only.

        无论是"Etag"与"If-None-Match"匹配，或"Last-Modified"不晚于"If-Modified-Since"，
        EtagResponse都会输出304状态码。这不符合规范，但更为高效。
        若你坚持要符合标准，请不要设置"Last-Modified"，仅使用"ETag"即可。
        '''
        if last_modified:
            if isinstance(last_modified, datetime):
                self._last_modified = last_modified
            elif isinstance(last_modified, basestring):
                self._last_modified = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S GMT')
            elif isinstance(last_modified, int):
                self._last_modified = (datetime.utcnow() + timedelta(seconds=last_modified))
        else:
            self._last_modified = None

    def send(self):
        status = self.status
        request = self.handler.request
        header = self.header
        body = ''
        # Do not check 1xx, 204 and 3xx status codes since Content-Length is 0.
        # 不检查1xx、204和3xx状态码，因为输出长度为0，没必要缓存。
        if 200 <= status < 300 and status != 204 or status >= 400:
            body = self.body
            # do not cache if no message body
            # 没有内容就不缓存
            if body:
                _cmp = -1
                last_modified = self._last_modified
                if last_modified:
                    header['Last-Modified'] = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
                    if request.if_modified_since:
                        if last_modified.tzinfo:
                            _cmp = cmp(request.if_modified_since, last_modified)
                        else:
                            _cmp = cmp(request.if_modified_since.replace(tzinfo=None), last_modified)
                if _cmp < 0: # don't calculate ETag if "Last-Modified" no latter than "If-Modified-Since"
                    etag = hex(crc32(body))[2:]
                    # You can also use md5 or other hash algorithms instead of crc32.
                    # 你可以使用md5或其他散列算法来取代crc32。
                    # etag = md5(body).digest().encode('base64').replace('\n', '').strip('=')
                    header['Etag'] = '"%s"' % etag
                    if str(request.if_none_match) == etag:
                        _cmp = 1
                if _cmp >= 0:
                    # set backup
                    # 备份状态码和Content-Type
                    self._status = status
                    self.status = 304
                    # 304 response do not need Content-Type field
                    # 304响应不需要Content-Type字段
                    self._mime = header.pop('Content-Type', self._mime)
                    body = ''
                else:
                    # set Content-Type header from backup
                    # 如果没有Content-Type头，可能是被删除了，因此需要恢复它
                    header.setdefault('Content-Type', self._mime)

        write = self._start_response(self.get_status(), header.items())
        if body:
            write(body)

    def copy(self, copy_header=True, start_response=None):
        return EtagResponse(start_response, self.status, self.header.copy() if copy_header else self.header, self.body, self._mime, self._status, self._last_modified)


class RequestHandler(object):
    '''
    It's a base request handler class, you should inherit it and implement
    the method you need.

    这是请求处理基类，你应该继承它，并实现所需的方法。
    '''

    def __init__(self, request, response, default_status=405):
        '''
        @type request: Request
        @param request: the incoming request object

        接收到的请求对象

        @type response: Response
        @param response: the response object for handling the response content

        处理响应内容的响应对象

        @type default_status: int
        @param default_status: the status code should be returned if method not
        implemented

        当方法未实现时，应该返回的状态码
        '''
        self.request = request
        self.response = response
        self.__default_status = default_status
        self.update_shortcut()

    def update_shortcut(self):
        '''
        Bind shortcuts for referencing to request and response object.

        为引用请求和响应对象绑定快捷方式。
        '''
        request = self.request
        response = self.response

        response.handler = self

        self.header = response.header
        self.write = response.write
        self.clear = response.clear
        self.set_content_type = response.set_content_type
        self.set_cache = response.set_cache

        self.GET = request.GET
        self.POST = request.POST
        self.HEADER = request.headers

    # Please override below methods to handle HTTP requests.
    # 请覆盖下列方法，以处理HTTP请求。
    def get(self, *args, **kw):
        self.not_allowed()

    def head(self, *args, **kw):
        # It should do the same thing like get(), without returning message body.
        # 这个方法应该和get()做同样的事，但不返回消息体。
        self.get(*args, **kw)

    post = options = put = delete = trace = get

    def before(self, *args, **kw):
        '''
        The processing before calling the handler method.
        You can put some common operations in this method,
        such as set Content-Type or do some hooking.

        在调用处理方法之前要进行的操作。
        你可以在这里面进行一些共同的操作，例如设置Content-Type或做些hook。
        '''

    def after(self, *args, **kw):
        '''
        The processing after calling the handler method.
        You can do some logging or counting in this method.

        在调用处理方法之后要进行的操作。
        你可以在这做些记录、计数的操作。
        '''

    def set_status(self, code):
        '''
        Set the response status code.

        设置响应状态码。

        @type code: int
        @param code: the status code should be returned for responsing

        需要返回的状态码
        '''
        self.response.status = code

    def error(self, code):
        '''
        Set an error status code, and also clear the output buffer.

        设置一个错误状态码，并清空输出缓存。
        '''
        self.set_status(code)
        self.clear()

    def redirect(self, url, status=302):
        '''
        Redirect the user agent to another URL.

        将用户代理重定向到另一个URL。

        @type url: string
        @param url: the URL should the user agent be redirected to

        用户代理将要重定向到的URL

        @type status: int
        @param status: the status code should be set, you will almost only use
        301, 302, 303 and 307.
        See U{RFC 2616<http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.3>}
        for more details.

        应被设置的状态码，你几乎只会用到301、302、303和307，详细内容可查看RFC 2616。
        '''
        # if status not in (301, 302, 303, 307) or (status in (303, 307) and self.request.environ['SERVER_PROTOCOL'] == 'HTTP/1.0'):
            # status = 302
        self.set_status(status)
        self.header['Location'] = urljoin(self.request.url, url)
        self.clear()

    def not_allowed(self):
        '''
        If the handler method hasn't been implemented, it will be called to
        tell user agent that this method is not available.

        若处理方法未被实现，这个方法将会被调用，以告诉用户代理该方法不可用。
        '''
        status = self.__default_status
        self.error(status)
        if status == 405:
            allow = [method.upper() for method in ('get', 'post', 'head', 'options', 'put', 'delete', 'trace')
                 # has been overriden, so must has been implemented
                 # 已被覆盖，所以必然已被实现
                if getattr(self.__class__, method) != getattr(RequestHandler, method)]
            self.header['Allow'] = ', '.join(allow)

    def handle_exception(self, exception):
        '''
        Handle the exceptions during execution.
        You'd better override it to display a user-friendly page.

        处理执行过程中出现的异常。
        你最好覆盖它来显示一个对用户友好的页面。
        '''
        logging.exception('Get an uncaught exception when processing request.')
        self.error(500)
        raise


class HtmlRequestHandler(RequestHandler):
    '''
    A request handler class for outputting HTML content.

    一个用于输出HTML的请求处理类。
    '''
    def before(self, *args, **kw):
        self.response.set_content_type()


class XhtmlRequestHandler(RequestHandler):
    '''
    A request handler class used for outputting XHTML content.

    一个用于输出XHTML的请求处理类。

    @warning: If your output content cannot be parsed as XHTML, Firefox will
    display an error page.

    如果你的输出内容不能被解析为XHTML，Firefox将会显示一个错误页面。
    '''
    def before(self, *args, **kw):
        self.response.set_content_type('xhtml')


class WsgiApplication(object):
    '''
    A WSGI application class.
    It can map the request URL pathes to your request handlers.

    一个WSGI应用程序类。
    它可以将请求的URL路径映射到响应请求处理类。

    @attention: Do B{not} use wsgiref.handlers.CGIHandler().run(application)
    to run an application, it may cause environ variables leak problem.
    Using google.appengine.ext.webapp.util.run_wsgi_app(application) is recommended.

    请勿使用wsgiref.handlers.CGIHandler().run(application)来运行一个应用程序，
    它可能会导致一些环境变量泄露的问题。
    请使用google.appengine.ext.webapp.util.run_wsgi_app(application)来代替。

    @see: U{Don't use CGIHandler on Google App Engine
    <http://dirtsimple.org/2010/02/don-use-cgihandler-on-google-app-engine.html>}

    U{慎用wsgiref.handlers.CGIHandler<http://www.keakon.cn/bbs/thread-1985-1-1.html>}
    '''

    def __init__(self, url_mapping, default_response_class=EtagResponse, quote_path=True):
        '''
        @type url_mapping: list
        @param url_mapping: a list of (url_path, handler_class, [response_class]) tuple

        一个(url_path, handler_class[, response_class])元组的列表
            - url_path：a regular expression that can match a URL path,
              it should start with "/" or "^/"

              一个可匹配URL路径的正则表达式，应以"/"或"^/"开始

            - handler_class: a RequestHandler instance for handler the path,
              a string of "module_name.class_name" is also available

              一个用于处理该路径的RequestHandler实例，
              "模块名.类名"这种风格的字符串也是可行的

            - response_class: the response class which should be used,
              default to default_response_class

              应使用的响应类，默认值为default_response_class

        @type default_response_class: response class (eg: Response, EtagResponse)
        @param default_response_class: the default response class

        默认的响应类

        @type quote_path: bool
        @param quote_path: whether percent-encoding the URL path

        是否用百分号编码URL路径

        @note: If percent-encode the URL path, some special characters will
        be encoded, e.g., ' ' => '%20', '囧'('\xe5\x9b\xa7') = > '%E5%9B%A7'.
        You need call urllib.unquote() to get the real path.
        See U{RFC 3986<http://www.ietf.org/rfc/rfc3986.txt>} for more details.

        如果百分号编码URL路径，一些特殊字符将会被编码，例如：
        ' ' => '%20', '囧'('\xe5\x9b\xa7') = > '%E5%9B%A7'。
        你需要调用urllib.unquote()来获得真实路径。
        详细内容可查看RFC 3986。
        '''
        self.quote_path = quote_path
        url_mapping_keys = []
        url_mappings = {}

        for handler_tuple in url_mapping:
            regexp = handler_tuple[0]
            handler = handler_tuple[1]
            if not regexp or not handler:
                continue

            response_class = handler_tuple[2] if len(handler_tuple) > 2 else default_response_class

            if regexp[0] != '^':
                regexp = '^' + regexp
            if regexp[-1] != '$':
                regexp += '$'
            compiled = re.compile(regexp)

            url_mappings[compiled] = (handler, response_class)
            url_mapping_keys.append(compiled)

        self.__url_mapping_keys = url_mapping_keys
        self.__url_mappings = url_mappings

    def __call__(self, environ, start_response):
        '''
        @type environ: dict
        @param environ: the environ variables dictionary

        环境变量字典

        @type start_response: function
        @param start_response: the WSGI-compatible start_response function for
        sending response

        WSGI兼容的start_response函数，用于输出响应
        '''
        request = Request(environ)
        request_path = request.path if self.quote_path else request.path_info
        groups = ()
        groupdict = {}

        for regexp in self.__url_mapping_keys:
            handler, response_class = self.__url_mappings[regexp]
            match = regexp.match(request_path)
            if match:
                response = response_class(start_response)

                if not callable(handler):
                    # delay binding for url_path and handler_class string
                    # 推迟绑定URL路径和处理类字符串
                    try:
                        mod_name, class_name = handler.rsplit('.', 1)
                        mod = __import__(mod_name)
                        handler = getattr(mod, class_name)
                        self.__url_mappings[regexp] = handler, response_class
                    except Exception, e:
                        logging.error('Please check your URL mapping, you probably point this path "%s" to an undefined handler "%s". \n%s',
                        request_path, handler, format_exc())

                        response, handler = self.handle_not_found(request, start_response)
                        # make future requests not to match other handler
                        # 不删除它，以免后续的访问可能匹配其他的handler
                        self.__url_mappings[regexp] = handler, response.__class__
                        break
                handler = handler(request, response)
                groupdict = match.groupdict()
                if not groupdict:
                    groups = match.groups()
                break
        else:
            response, handler = self.handle_not_found(request, start_response)

        try:
            handler.before(*groups, **groupdict)
            method = request.method
            if method == 'GET':
                handler.get(*groups, **groupdict)
            elif method == 'POST':
                handler.post(*groups, **groupdict)
            else:
                # only speed up for GET & POST
                # 只为GET和POST方法提速绑定，因为getattr比较慢
                getattr(handler, method.lower())(*groups, **groupdict)
            handler.after(*groups, **groupdict)
        except Exception, e:
            handler.handle_exception(e)

        handler.response.send()
        return []

    def handle_not_found(self, request, start_response):
        '''
        Handle the URL pathes if no handler class matches.
        You'd better override it to display a user-friendly page.

        处理不匹配任何处理类的URL路径。
        你最好覆盖它来显示一个对用户友好的页面。
        '''
        response = Response(start_response)
        return response, RequestHandler(request, response, 404)


def multi_domain_mapping(*domains_with_url_mappings):
    '''
    A middleware for multi-domain support.

    一个用于支持多域名的中间件。

    @type domains_with_url_mappings: one or more tuples of (domain, wsgi_app)
    @param domains_with_url_mappings: each domain and its URL mappings,
    you can use '*' to match any domain.

    每个域名及其URL映射，可以用'*'来匹配任何域名。
    '''
    def find_domain(env, start_response):
        host = env['HTTP_HOST']
        for (domain, wsgi_app) in domains_with_url_mappings:
            if domain == '*' or domain == host:
                return wsgi_app(env, start_response)
        start_response('404 Not Found', [])
        return []
    return find_domain

def redirect_to_major_domain(wsgi_app, major_domain, ignore_scheme=False):
    '''
    A middleware for redirecting request to major domain.

    用于将请求重定向到主要域名的中间件。

    @type major_domain: string
    @param major_domain: the domain of redirect destination

    重定向的目的地域名。

    @type ignore_scheme: bool
    @param ignore_scheme: whether ignore scheme, if it's False, only HTTP
    requests will be redirect.

    是否忽略协议，若为False，则只有HTTP请求会被重定向。

    @note: The fragment part of the URL, which followed by '#', will be ignore
    since it won't be sent to server.

    URL中'#'后的部分会被忽略，因为它不会被发送到服务器。
    '''
    def redirect_if_needed(env, start_response):
        if env['HTTP_HOST'] != major_domain and env['REMOTE_ADDR'][:2] != '0.' and (ignore_scheme or env['wsgi.url_scheme'] == 'http'):
            url = urlunsplit(['http', major_domain, env['PATH_INFO'], env['QUERY_STRING'], ''])
            start_response('301 Moved Permanently', [('Location', url)])
            return []
        else:
            return wsgi_app(env, start_response)
    return redirect_if_needed

def client_cache(seconds, privacy=None):
    '''
    A decorator for decorating a handler method to make user agent cache this
    response.

    一个修饰处理方法来让用户代理缓存这次响应的装饰器。

    @see: L{Response.set_cache}
    '''
    def wrap(handler):
        def cache_handler(self, *args, **kw):
            self.set_cache(seconds, privacy)
            return handler(self, *args, **kw)
        return cache_handler
    return wrap

# server cache dictionary
# 服务器端的缓存字典
__app_cache = {}

# global lock for thread safe mode
# 用于线程安全的全局锁
__lock = RLock()

# whether use thread safe mode
# 是否使用线程安全模式
__thread_safe = False

def __set_server_cache(key, value, seconds):
    '''
    @type key: object
    @param key: the key of the cache

    缓存的键

    @type value: object
    @param value: the value of the cache

    缓存的值

    @type seconds: int or float
    @param seconds: the cache expiry time from now in seconds.
    If it's not bigger than than 0, the cache will never expired.

    从现在起，缓存保存的秒数；若小于等于0，则永不过期。
    '''
    global __app_cache

    if seconds < 0:
        seconds = 0

    __app_cache[key] = (value, time() + seconds if seconds else 0)

def __get_server_cache(key):
    '''
    @type key: object
    @param key: the key of the cache

    缓存的键

    @rtype: object
    @return: the value of the cache, or None if expired or never been set

    缓存的值，若已过期或从未设置则为None
    '''
    global __app_cache

    value = __app_cache.get(key, None)
    if value:
        expiry = value[1]
        if expiry and time() > expiry:
            del __app_cache[key]
            return None
        else:
            return value[0]
    return None

def clear_expired_server_cache():
    '''
    Remove all the server caches which has expired.
    You can use cron jobs to call it periodically for saving memory.

    清除所有已过期的服务器端缓存。
    你可以在计划任务里调用它，以节省内存。

    @note: An app may use several instances, this function only remove caches
    of current instance.

    一个应用可能使用多个实例，这个函数只会清除当前实例的缓存。
    '''
    global __app_cache

    for key, value in __app_cache.items():
        expiry = value[1]
        if expiry and time() > expiry:
            del __app_cache[key]

def flush_all_server_cache():
    '''
    Remove all the server caches.

    清除所有服务器端缓存。

    @note: An app may use several instances, this function only remove caches
    of current instance.

    一个应用可能使用多个实例，这个函数只会清除当前实例的缓存。
    '''
    global __app_cache

    __app_cache = {}

def server_cache(seconds, is_private=True, only_check_login=False, check_ajax=False):
    '''
    A decorator for decorating a handler method to cache the response in memory,
    so that the subsequent requests can reuse the response without
    getting result from datastore and memcache, rendering template or something else.

    一个修饰处理方法来将响应缓存在内存的装饰器，这样就能让后续的请求直接重用响应，
    而无需从datastore和memcache中获取结果、渲染模板等。

    @type seconds: int or float
    @param seconds: the cache expiry time from now in seconds.
    If it's not bigger than than 0, the cache will never expired

    从现在起，缓存保存的秒数；若小于等于0，则永不过期

    @type is_private: bool
    @param is_private: whether the cache is public or private

    缓存是公用的还是私有的

    @type only_check_login: bool
    @param only_check_login: whether only differentiate among visitors, logged users
    and admins, it will be ignore if is_private is False

    是否只区分访客、已登录用户和管理员，当is_private为False时忽略此参数

    @type check_ajax: bool
    @param check_ajax: whether differentiate AJAX requests and non-AJAX requests

    是否区分AJAX请求和非AJAX请求

    @note: You can check the "X-Server-Cached" response headers to verify
    whether it's retrieved from server cache.

    你可通过检查"X-Server-Cached"响应头字段，来确认这次响应是否是由缓存中取出的。

    @warning: B{Never} cache a response which contains "Set-Cookie" headers or
    its request method is not GET & HEAD.
    Make sure you has set "is_private" to True, and forced user logged in
    for private content.

    B{永远不要}缓存一个输出"Set-Cookie"头的响应，或其请求不为GET和HEAD。
    并且保证私有的内容已将is_private设为True，并强制用户登录了。
    '''
    def wrap(handler):
        def cache_handler(self, *args, **kw):
            key = id(handler)
            # if you want implement your own cache mechanism using memcache,
            # you may set:
            # key = '%s.%s' % (self.__class__, handler.__name__)
            # 若你想自行实现使用memcache的缓存机制，那你可以如上设置key
            request = self.request
            if is_private:
                if only_check_login:
                    key = (key, request.is_admin * 2 or bool(request.user))
                else:
                    user = request.user
                    if user:
                        key = (key, user.user_id())
            key = (key, request.scheme, args, tuple(kw.items()), md5(request.query_string).digest(), request.is_xhr if check_ajax else None)

            response = __get_server_cache(key)
            if response:
                if response.status == 304 and isinstance(response, EtagResponse):
                    response.status = response._status
                response.header['X-Server-Cached'] = '1' # for debug
                response._start_response = self.response._start_response
                self.response = response
                self.update_shortcut()
            else:
                handler(self, *args, **kw)
                __set_server_cache(key, self.response, seconds)
        return cache_handler
    return wrap

def server_cache_safe(seconds, is_private=True, only_check_login=False, check_ajax=False):
    '''
    Thread safe version of server_cache_safe.

    server_cache_safe的线程安全版本。
    '''
    def wrap(handler):
        def cache_handler(self, *args, **kw):
            key = id(handler)
            request = self.request
            if is_private:
                if only_check_login:
                    key = (key, request.is_admin * 2 or bool(request.user))
                else:
                    user = request.user
                    if user:
                        key = (key, user.user_id())
            key = (key, request.scheme, args, tuple(kw.items()), md5(request.query_string).digest(), request.is_xhr if check_ajax else None)

            __lock.acquire()
            response = __get_server_cache(key)
            if response:
                response = response.copy(False, self.response._start_response)
                __lock.release()
                self.response = response
                self.update_shortcut()
            else:
                __lock.release()
                handler(self, *args, **kw)
                response = self.response.copy()
                if response.status == 304 and isinstance(response, EtagResponse):
                    response.status = response._status
                response.header['X-Server-Cached'] = '1' # for debug
                __set_server_cache(key, response, seconds)
        return cache_handler
    return wrap

def thread_safe(func):
    '''
    A decorator for making a function call thread safe.

    一个用来让函数调用变得线程安全的装饰器。

    @type func: function
    @param func: the function to be set thread safe

    要设为线程安全的函数
    '''
    def safe_func(*args, **kw):
        with __lock:
            return func(*args, **kw)
    return safe_func

def use_thread_safe_mode():
    '''
    Make all functions thread safe.
    You'd better call it immediately after import yui.

    使所有函数线程安全。
    最好在引入YUI后立刻调用。
    '''
    with __lock:
        global __thread_safe
        if not __thread_safe:
            __thread_safe = True
            global __set_server_cache, __get_server_cache, clear_expired_server_cache, flush_all_server_cache, server_cache
            __set_server_cache = thread_safe(__set_server_cache)
            __get_server_cache = thread_safe(__get_server_cache)
            clear_expired_server_cache = thread_safe(clear_expired_server_cache)
            flush_all_server_cache = thread_safe(flush_all_server_cache)
            server_cache = server_cache_safe

def authorized(is_admin=False, url=None):
    '''
    A decorator for decorating a handler method to make sure user has been
    logged in.

    一个修饰处理方法来确保用户已登录的装饰器。

    @type is_admin: bool
    @param is_admin: whether the requested content should only be accessed by
    administrator

    被请求的内容是否只能被管理员访问

    @type url: string
    @param url: the URL that the non-admin users should be redirected to
    when he requested a administrator only page.
    If not given, he will get a 403 Forbidden error.

    当非管理员用户访问只能被管理员访问的页面时，他应该被重定向到的地址。
    若未给出，则会收到一个403 Forbidden错误。

    @warning: If you also use server_cache decorator, please set is_private to
    True, otherwise all the following visitors will see the cached page.
    Please also put authorized decorator before server_cache, otherwise you may
    cache a redirect header, so the users will always be redirected to the
    login page.

    若你同时使用server_cache装饰器，请将is_private设为True，否则接下来的访问者
    都会看到被缓存的页面。
    并请将authorized装饰器置于server_cache之前，否则你会缓存一个重定向头，
    导致用户一直被重定向到登录页面。
    '''
    def wrap(handler):
        def authorized_handler(self, *args, **kw):
            request = self.request
            if request.method == 'GET':
                if not request.user:
                    self.redirect(users.create_login_url(request.url), 303)
                elif is_admin and not request.is_admin:
                    if url:
                        self.redirect(url, 303)
                    else:
                        self.error(403)
                else:
                    handler(self, *args, **kw)
            else:
                if not request.user or (is_admin and not request.is_admin):
                    self.error(403)
                else:
                    handler(self, *args, **kw)
        return authorized_handler
    return wrap

def get_without_exception(method):
    def get(self, key):
        try:
            return method(self, key)
        except:
            return None
    return get

# return None instead of raising KeyError exception when trying to get an item
# not in request.GET or request.POST
# 当request.GET或request.POST中没有相应key时，返回None而不是引发KeyError异常
MultiDict.__getitem__ = get_without_exception(MultiDict.__getitem__)
