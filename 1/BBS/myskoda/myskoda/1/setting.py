# -*- coding: utf-8 -*-

from os import environ

IS_SAE = 'SERVER_SOFTWARE' in environ

SITE_TITLE = "yourSite" #网站标题

THEME = 'default' #主题

#代码安装前请先到SAE后台开通以下功能：
#Memcache 大小1M（可根据数据量和访问量自行调整）;
#TaskQueue 队列名default，类型 顺序队列，Level 1
#启用KVDB
#上面三个是必须的，如果你使用SAE storage来存储头像和用户的图片，
#则还需建立两个storage domain name: avatar、upload

#用户模式 
#1:只允许qq登录，需要在下面设置 QQ登录接口信息
#2：只用注册模式，
#3：可同时用两种方式
#注意，1和2这两种用户模式不能随意切换，否则已有用户将不可登录
#允许的模式切换:1>3、2>3
USER_MODEL = 2 #1/2/3

##当 USER_MODEL 为1或3时，需要设置QQ登录接口信息
QQ_APP_ID = '' # app id 如 100305xxx
QQ_APP_KEY = '' # app key 如 c47f8a77ac51a0e4dd615xxxxxxxxxx

#链接列表
LINK_BROLL = [
    {'text': 'SAEPy blog', 'url': 'http://saepy.sinaapp.com/', 'title': u'基于SAE/python 上的blog程序'},
    {'text': 'SAEspot社区', 'url': 'http://www.saespot.com/', 'title': u'SAEspot官方社区'},
]

###设置容易调用的jquery 文件
if IS_SAE:
    APP_NAME = environ["APP_NAME"]
    MAJOR_DOMAIN = APP_NAME + '.sinaapp.com'
    BASE_URL = 'http://' + MAJOR_DOMAIN
    JQUERY = "http://lib.sinaapp.com/js/jquery/1.6.2/jquery.min.js"
    #JQUERY = "http://code.jquery.com/jquery-1.6.2.min.js"
else:
    APP_NAME = ''
    MAJOR_DOMAIN = '127.0.0.1:8080'
    BASE_URL = 'http://127.0.0.1:8080'
    JQUERY = "/static/js/jquery-1.6.4.js"

#下面的设置比较合理，建议不要修改
TITLE_MAX_S = 60 #帖子标题最多字数
CONTENT_MAX_S = 2000 #帖子内容最多字数
COMMENT_MAX_S = 1200 #回复内容最多字数
RECENT_POST_NUM = 20 #首页显示的文章数
EACH_PAGE_POST_NUM = 20 #每页显示文章数
EACH_PAGE_COMMENT_NUM = 32 #每页评论数
DESCRIPTION_CUT_WORDS = 100 #meta description 显示的字符数
RECENT_COMMENT_NUM = 10 #边栏显示最近被评论的帖子数
FEED_NUM = 10 #订阅显示的文章数，要小于RECENT_POST_NUM
MEMBER_RECENT_TOPIC = 10 #记录个人最近的发帖数
MEMBER_RECENT_REPLY = 10 #记录个人最近的回帖数
NOTIFY_NUM = 16 #最多提醒条数
NOTIFY_MEMBER_NUM = 10 #一个帖子或回复可允许最多 @username 的人数
DEFAULT_CACHE_TIME = 600 #默认的缓存时间 n秒


#图片存储方式，只有两项sae/upyun，并作下面对应设置，
#如果用SAE storage 来保存图像，就保留下面默认设置，
#只需到后台建立两个storage domain name: avatar、upload
IMG_STORAGE = 'sae' #sae/upyun
if IMG_STORAGE=='sae':
    DOMAIN_NAME_AVATAR = 'avatar' #存放头像
    DOMAIN_NAME_UPLOAD = 'upload' #存放用户上传的图像
    #头像后缀，留空不填
    AVATAR_NORMAL = ''
    AVATAR_MINI = ''
    #头像图片网址前缀
    if IS_SAE:
        #http://appid-domainname.stor.sinaapp.com/objname.jpg
        AVATAR_URL = 'http://%s-%s.stor.sinaapp.com/'%(APP_NAME, DOMAIN_NAME_AVATAR)
    else:
        #'http://%s/stor-stub/%s/%s' % (os.environ['HTTP_HOST'], domain, urllib.quote(key_name))
        AVATAR_URL = 'http://%s/stor-stub/%s/'%(MAJOR_DOMAIN, DOMAIN_NAME_AVATAR)
elif IMG_STORAGE=='upyun':
    DOMAIN_NAME_AVATAR = '' #存放头像
    DOMAIN_NAME_UPLOAD = '' #存放用户上传的图像
    AVATAR_NORMAL = '!normal' #48px 需要在upyun 上建立对应的缩略图
    AVATAR_MINI = '!mini' #24px 需要在upyun 上建立对应的缩略图
    
    UPYUN_USER = '' #操作用户
    UPYUN_PW = '' #操作用户密码
    
    #头像图片网址前缀
    AVATAR_URL = 'http://%s.b0.upaiyun.com/avatar/'%DOMAIN_NAME_AVATAR
    #用户上传图片网址前缀
    UPLOAD_BASE_URL = 'http://%s.b0.upaiyun.com'%DOMAIN_NAME_UPLOAD

## dict in kvdb 以下不要修改
#用户key: m-username flag 注册后默认1，上传头像后2，被禁用0，管理员99
MEMBER_DICT = {'id':'', 'name':'', 'code':'', 'add':'', 'flag':'1', 'notic':''}
#key: n-id
NODE_DICT = {'id':'', 'name':'', 'count':'', 'imgurl':'', 'about':''}
#key: t-nodeid-id
TOPIC_DICT = {'title':'', 'nodeid':'', 'nodename':'', 'author':'', 'add':'', 'cnum':'', 'content':'','reply':'', 'edit':''}
#key: t-nodeid-id-cnumi
COMMENT_DICT = {'author':'', 'add':'', 'content':''}


#有建议或问题可到SAEspot官方社区交流 http://www.saespot.com/ 
