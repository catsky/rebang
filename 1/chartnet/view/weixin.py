#!/bin/env python
# -*- coding: utf-8 -*-
#########weibo
__author__ = 'Ken Zheng'

import logging
import hashlib
import time
import xml.etree.ElementTree as ET
from models import operatorDB

FILTER_WORD_LIST=[u"大纪元",]

#接入和消息推送都需要做校验
def verification(request):
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')

    token = 'australian1984' #注意要与微信公众帐号平台上填写一致
    tmplist = [token, timestamp, nonce]
    tmplist.sort()
    tmpstr = ''.join(tmplist)
    hashstr = hashlib.sha1(tmpstr).hexdigest()

    if hashstr == signature:
        return True
    return False

#将消息解析为dict
def parse_msg(rawmsgstr):
    root = ET.fromstring(rawmsgstr)
    msg = {}
    for child in root:
        msg[child.tag] = child.text
    return msg

def is_text_msg(msg):
    return msg['MsgType'] == 'text'

def is_location_msg(msg):
    return msg['MsgType'] == 'location'

def user_subscribe_event(msg):
    return msg['MsgType'] == 'event' and msg['Event'] == 'subscribe'

HELP_INFO = \
u"""
欢迎关注澳洲一刻^_^

我们为您奉上最新鲜的澳洲生活资讯，最前沿的移民信息。
❤回复'n'或者'new' 获取最新澳洲资讯
"""

def help_info(msg):
    return response_text_msg(msg, HELP_INFO)

#访问豆瓣API获取书籍数据
BOOK_URL_BASE = 'http://api.douban.com/v2/book/search'


NEWS_MSG_HEADER_TPL = \
u"""
<xml>
<ToUserName><![CDATA[%s]]></ToUserName>
<FromUserName><![CDATA[%s]]></FromUserName>
<CreateTime>%s</CreateTime>
<MsgType><![CDATA[news]]></MsgType>
<ArticleCount>%d</ArticleCount>
<Articles>
"""
#<Content><![CDATA[]]></Content>

NEWS_MSG_TAIL = \
u"""
</Articles>
</xml>
"""
#<FuncFlag>1</FuncFlag>

#消息回复，采用news图文消息格式
def response_news_msg(recvmsg, posts):
    msgHeader = NEWS_MSG_HEADER_TPL % (recvmsg['FromUserName'], recvmsg['ToUserName'], 
        str(int(time.time())), len(posts))
    msg = ''
    msg += msgHeader
    msg += make_articles(posts)
    msg += NEWS_MSG_TAIL
    return msg

def make_articles(posts):
    msg = ''
    if len(posts) == 1:
        msg += make_single_item(posts[0])
    else:
        for i, post in enumerate(posts):
            if i == 3:
                break
            msg += make_item(post, i+1)
            
    return msg

NEWS_MSG_ITEM_TPL = \
u"""
<item>
    <Title><![CDATA[%s]]></Title>
    <Description><![CDATA[%s]]></Description>
    <PicUrl><![CDATA[%s]]></PicUrl>
    <Url><![CDATA[%s]]></Url>
</item>
 """
 
def make_item(message, itemindex):
    #filter the sensitive words
    title_r = message._title
    description_r = message._shorten_content
    for word in FILTER_WORD_LIST:
        title_r = title_r.replace(word, '*')
        description_r =description_r.replace(word, '*')
        
        
    title =  u'%s' % title_r
    description = u'%s' % description_r
    picUrl = message._imgthumbnail
    url = 'http://australian.sinaapp.com/detailpost/%s?weixin=1' % message._id
    item = NEWS_MSG_ITEM_TPL % (title, description, picUrl, url)
    #item = NEWS_MSG_ITEM_TPL
    return item

#图文格式消息只有单独一条时，可以显示更多的description信息，所以单独处理
def make_single_item(message):
    #filter the sensitive words
    title_r = message._title
    description_r = message._shorten_content
    for word in FILTER_WORD_LIST:
        title_r = title_r.replace(word, '*')
        description_r = description_r.replace(word, '*')
        
    title =  u'%s' % title_r
    if len(description_r) > 75:
        msg_discription = description_r[:70] + "..."
    description ='%s' % msg_discription
    picUrl = message._imgthumbnail
    url = 'http://australian.sinaapp.com/detailpost/%s?weixin=1' % message._id
    item = NEWS_MSG_ITEM_TPL % (title, description, picUrl, url)
    #item = NEWS_MSG_ITEM_TPL
    return item

TEXT_MSG_TPL = \
u"""
<xml>
<ToUserName><![CDATA[%s]]></ToUserName>
<FromUserName><![CDATA[%s]]></FromUserName>
<CreateTime>%s</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[%s]]></Content>
<FuncFlag>0</FuncFlag>
</xml>
"""

def response_text_msg(msg, content):
    s = TEXT_MSG_TPL % (msg['FromUserName'], msg['ToUserName'], 
        str(int(time.time())), content)
    return s
