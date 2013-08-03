# -*- coding: utf-8 -*-
import logging
import re
from time import time
from hashlib import md5
from PIL import Image
from StringIO import StringIO
import json
import urllib2

###############
import sae.kvdb
import pylibmc
from sae.taskqueue import Task, TaskQueue

from common import authorized, BaseHandler, call_member, clear_cache_multi, decode_dict, encode_dict, findall_mentions, safe_encode, textilize
from model import Comment, Commomkvdb, Count, Member, Node, Topic
from setting import *

if IMG_STORAGE=='sae':
    import sae.storage
    
    def put_obj2storage(file_name = '', data = '', domain_name = DOMAIN_NAME_UPLOAD, expires='365', type=None, encoding= None):
        s = sae.storage.Client()
        ob = sae.storage.Object(data = data, cache_control='access plus %s day' % expires, content_type= type, content_encoding= encoding)
        return s.put(domain_name, file_name, ob)
    
elif IMG_STORAGE=='upyun':
    from upyun import UpYun

mc = pylibmc.Client()
kv = sae.kvdb.KVClient()

###############
class HomePage(BaseHandler):
    def get(self):
        self.echo('home.html', {
            'title': "首页",
            'topic_objs': Commomkvdb.get_topic_by_keys('recent-topic-home'),
            'site_counts': Count.get_site_counts(),
            'newest_node': Node.get_newest(),
            'recent_node': Node.get_recent_node(),
            'hot_node': Node.get_hot_node(),
            #'recent_topic_objs': Commomkvdb.get_comment_topic_by_keys('recent-topic-home'),
            'comment_topic_objs': Commomkvdb.get_comment_topic_by_keys('recent-comment-topic-home'),
        }, layout='_layout.html')

### qq login
from qqweibo import APIClient as qqAPIClient
qqclient = qqAPIClient(app_key=QQ_APP_ID, app_secret=QQ_APP_KEY)
class QQLoginPage(BaseHandler):
    def get(self):
        if USER_MODEL==2:
            self.redirect('/sigin')
            return
        
        self.clear_all_cookies()
        qq_login_url = qqclient.get_authorize_url()
        self.echo('qqlogin.html', {
            'title': "QQ一键安全登录",
            'qq_login_url': qq_login_url,
        }, layout='_layout.html')

class QQCallback(BaseHandler):
    def get(self):
        if USER_MODEL==2:
            self.redirect('/sigin')
            return
        
        code = self.get_argument('code', '')
        if code:
            access_token = qqclient.request_access_token(code).get('access_token','')
            if access_token:
                #获取当前成功登录的 OpenID
                open_id = qqclient.get_open_id(access_token)
                if open_id:
                    #判断是否已存在
                    k = 'qq_' +str(open_id)
                    self.set_cookie('open_id', str(open_id), path="/", expires_days = 1 )
                    self.set_cookie('access_token', str(access_token), path="/", expires_days = 1 )
                    kv_member = kv.get(k)
                    
                    if kv_member and len(kv_member)<20:
                        #直接登录
                        #get member info
                        name = str(kv_member)
                        m_obj = Member.get_by_name(name)
                        if m_obj:
                            if m_obj['code'] != str(access_token):
                                m_obj['code'] = str(access_token)
                                Commomkvdb.save('m-'+str(kv_member), m_obj)
                                clear_cache_multi(['cur_user:'+name])
                            
                            #set sr_code
                            code_list = [m_obj['code']]
                            u_topic_time = kv.get('u_topic_time:'+name)
                            if u_topic_time:
                                code_list.append(u_topic_time)
                            u_comment_time = kv.get('u_comment_time:'+name)
                            if u_comment_time:
                                code_list.append(u_comment_time)
                            #code_md5 = md5(''.join(code_list)).hexdigest()
                            
                            #
                            self.set_cookie('username', str(kv_member), path="/", expires_days = 365 )
                            self.set_cookie('usercode', str(md5(''.join(code_list)).hexdigest()), path="/", expires_days = 365 )
                            self.set_cookie('userflag', m_obj['flag'], path="/", expires_days = 365 )
                            if m_obj['flag'] == '1':
                                self.redirect('/setavatar')
                            else:
                                self.redirect('/')
                            return
                            
                        else:
                            #设置用户名
                            kv.set('qq_' +str(open_id), str(access_token))
                            self.redirect('/setname')
                            return
                        
                    else:
                        #注册新用户
                        kv.set('qq_' +str(open_id), str(access_token))
                        self.redirect('/setname')
                        return
                else:
                    self.write('获取open_id 失败，请返回再试')
            else:
                self.write('获取access_token 失败，请返回再试')
        else:
            self.write('获取code 失败，请返回再试')

class SetName(BaseHandler):
    def get(self): 
        if USER_MODEL==2:
            self.redirect('/sigin')
            return
        
        open_id = str(self.get_cookie('open_id',''))
        access_token = str(self.get_cookie('access_token',''))
        
        if open_id and access_token:
            access_token_in_kvdb = kv.get('qq_' +str(open_id))
            if access_token_in_kvdb == access_token:
                pass
            else:
                self.redirect('/sigin')
                return
        else:
            self.redirect('/sigin')
            return
        
        self.echo('setname.html', {
            'title': "设置名字",
            'errors':[],
            'name':'',
            'newest_node': Node.get_newest(),
        }, layout='_layout.html')
    
    def post(self):
        if USER_MODEL==2:
            self.redirect('/sigin')
            return
        
        name = str(self.get_argument('name','').lower().encode('utf-8'))
        open_id = str(self.get_cookie('open_id',''))
        access_token = str(self.get_cookie('access_token',''))
        
        errors = []
        if name and open_id and access_token:
            access_token_in_kvdb = kv.get('qq_' +str(open_id))
            if access_token_in_kvdb == access_token:
                pass
            else:
                self.redirect('/sigin')
                return
            
            if len(name)<20:
                if re.search('^[a-zA-Z0-9]+$', name):
                    check_obj = Member.check_user_name(str(name))
                    if check_obj:
                        errors.append('该用户名已被注册，请换一个吧')
                    else:
                        u_flag = Member.add_user(str(name), access_token)
                        if u_flag and kv.set('qq_' +str(open_id), str(name)):
                            #注册成功
                            #set sr_code
                            code_list = [access_token]
                            u_topic_time = kv.get('u_topic_time:'+name)
                            if u_topic_time:
                                code_list.append(u_topic_time)
                            u_comment_time = kv.get('u_comment_time:'+name)
                            if u_comment_time:
                                code_list.append(u_comment_time)
                            #code_md5 = md5(''.join(code_list)).hexdigest()
                            
                            self.set_cookie('username', name, path="/", expires_days = 365 )
                            self.set_cookie('usercode', str(md5(''.join(code_list)).hexdigest()), path="/", expires_days = 365 )
                            self.set_cookie('userflag', str(u_flag), path="/", expires_days = 365 )
                            self.redirect('/setavatar?qq=1')
                            return
                        else:
                            errors.append('服务器出现意外错误，请稍后再试')
                else:
                    errors.append('用户名只能包含字母和数字')
            else:
                errors.append('用户名太长了')
        else:
            errors.append('用户名必填')
            
        self.echo('setname.html', {
            'title': "设置名字",
            'errors':errors,
            'name':name,
        }, layout='_layout.html')        
    
### qq login end

class LoginPage(BaseHandler):
    def get(self):
        if IS_SAE:
            if USER_MODEL==1:
                self.redirect('/qqlogin')
                return
        self.echo('login.html', {
            'title': "登录",
            'errors':[],
            'name':'',
            'newest_node': Node.get_newest(),
        }, layout='_layout.html')
    
    def post(self):
        name = str(self.get_argument('name','').lower().encode('utf-8'))
        pw = self.get_argument('pw','')
        
        errors = []
        if name and pw:
            if len(name)<20 or len(pw)<20:
                if re.search('^[a-zA-Z0-9]+$', name):
                    pwmd5 = md5(pw.encode('utf-8')).hexdigest()
                    u_obj = kv.get('m-' + name)
                    if u_obj:
                        member_dict = decode_dict(u_obj)
                        if pwmd5 == member_dict['code'] and int(member_dict['flag']) >= 1:
                            #set sr_code
                            code_list = [member_dict['code']]
                            u_topic_time = kv.get('u_topic_time:'+name)
                            if u_topic_time:
                                code_list.append(u_topic_time)
                            u_comment_time = kv.get('u_comment_time:'+name)
                            if u_comment_time:
                                code_list.append(u_comment_time)
                            #login
                            self.set_cookie('username', name, path="/", expires_days = 365 )
                            self.set_cookie('usercode', md5(''.join(code_list)).hexdigest(), path="/", expires_days = 365 )
                            self.set_cookie('userflag', member_dict['flag'], path="/", expires_days = 365 )
                            if member_dict['flag'] == '1':
                                self.redirect('/setavatar')
                            else:
                                self.redirect('/')
                            return
                            
                        else:
                            errors.append('用户名或密码不对或已被禁用')
                    else:
                        errors.append('用户名或密码不对')
                else:
                    errors.append('用户名只能包含字母和数字')
            else:
                errors.append('用户名或密码太长了')
        else:
            errors.append('用户名和密码必填')
            
        self.echo('login.html', {
            'title': "登录",
            'errors':errors,
            'name':name,
            'newest_node': Node.get_newest(),
        }, layout='_layout.html')        
    

class SiginPage(BaseHandler):
    def get(self): 
        if IS_SAE:
            if USER_MODEL==1:
                self.redirect('/qqlogin')
                return
        self.echo('sigin.html', {
            'title': "注册",
            'errors':[],
            'name':'',
            'newest_node': Node.get_newest(),
        }, layout='_layout.html')
    
    def post(self):
        name = str(self.get_argument('name','').lower().encode('utf-8'))
        pw = self.get_argument('pw','')
        
        errors = []
        if name and pw:
            if len(name)<20 or len(pw)<20:
                if re.search('^[a-zA-Z0-9]+$', name):
                    check_obj = Member.check_user_name(str(name))
                    if check_obj:
                        errors.append('该用户名已被注册，请换一个吧')
                    else:
                        pwmd5 = md5(pw.encode('utf-8')).hexdigest()
                        u_flag = Member.add_user(str(name), pwmd5)
                        if u_flag:
                            #注册成功
                            self.set_cookie('username', name, path="/", expires_days = 365 )
                            self.set_cookie('usercode', md5(pwmd5).hexdigest(), path="/", expires_days = 365 )
                            self.set_cookie('userflag', str(u_flag), path="/", expires_days = 365 )
                            self.redirect('/setavatar')
                            return
                        else:
                            errors.append('服务器出现意外错误，请稍后再试')
                else:
                    errors.append('用户名只能包含字母和数字')
            else:
                errors.append('用户名或密码太长了')
        else:
            errors.append('用户名和密码必填')
            
        self.echo('sigin.html', {
            'title': "注册",
            'errors':errors,
            'name':name,
            'newest_node': Node.get_newest(),
        }, layout='_layout.html')        

class LogoutPage(BaseHandler):
    def get(self): 
        username = self.get_cookie('username','')
        if username:
            clear_cache_multi(['cur_user:'+str(username)])
        self.clear_all_cookies()
        
        self.redirect('/')        

class MemberPage(BaseHandler):
    def get(self, name): 
        name = name.lower()
        m_obj = Member.get_by_name(str(name))
        if m_obj:
            self.echo('member.html', {
                'title': m_obj['name'],
                'm_obj': m_obj,
                'topic_objs': Commomkvdb.get_topic_by_keys('topic-'+str(m_obj['name'])),
                'member_comment_topic_objs': Commomkvdb.get_topic_by_keys('comment-topic-'+str(m_obj['name'])),
                'newest_node': Node.get_newest(),
                'recent_node': Node.get_recent_node(),
                'hot_node': Node.get_hot_node(),
                'recent_topic_objs': Commomkvdb.get_comment_topic_by_keys('recent-topic-home'),
                'comment_topic_objs': Commomkvdb.get_comment_topic_by_keys('recent-comment-topic-home'),                
            }, layout='_layout.html')
        else:
            self.set_status(404)
            self.echo('error.html', {
                'page': '404',
                'title': "Can't find out this URL",
                'h2': 'Oh, my god!',
                'msg': 'Something seems to be lost...'
            })

class SetAvatar(BaseHandler):
    @authorized(flag=1)
    def get(self):
        #尝试读取QQ空间头像
        wb_avatar_large = ''
        qq = self.get_argument('qq', '')
        if qq=='1':
            username = str(self.get_cookie('username',''))
            open_id = str(self.get_cookie('open_id',''))
            access_token = str(self.get_cookie('access_token',''))
            userflag = str(self.get_cookie('userflag',''))
            if username and open_id and access_token and userflag:
                qq_user = qqclient.get_user_info(access_token, open_id)
                #qq_user { "ret":0, "msg":"", "nickname":"qq nicke name", "figureurl_2":"http://qzapp.qlogo.cn/qzapp/100254539/5BDCA5E6321B273E44720E532B1379ED/100" }
                #保存有用的信息
                #id = str(open_id)
                #name = en_code(qq_user['nickname'])
                wb_avatar_large = str(qq_user.get('figureurl_2',''))
                
                headers = {
                    'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6',
                    'Referer':wb_avatar_large,
                }
                req = urllib2.Request(
                    url = wb_avatar_large,
                    headers = headers
                )
                data = urllib2.urlopen(req).read()
                if data:
                    im = Image.open(StringIO(data))
                    if im.size[0] > 73 or im.size[1] > 73:
                        ss = max(float(im.size[0])/73, float(im.size[1])/73)
                        box = (int(im.size[0]/ss), int(im.size[1]/ss))
                        im = im.resize(box, Image.ANTIALIAS)
                        output = StringIO()
                        im.convert('RGB').save(output, 'JPEG', quality = 95)#95
                        img_data = output.getvalue()
                        output.close()
                        
                    else:
                        img_data = data
                    
                    if IMG_STORAGE=='sae':
                        file_path_name = '%s.jpg'% username
                        avatar = put_obj2storage(file_name = file_path_name, data = img_data, domain_name = DOMAIN_NAME_AVATAR)
                    elif IMG_STORAGE=='upyun':
                        u = UpYun(DOMAIN_NAME_AVATAR, UPYUN_USER, UPYUN_PW)
                        file_path_name = '/avatar/%s.jpg'% username
                        avatar = u.writeFile( file_path_name, img_data, True)
                    
                    if avatar:
                        if userflag == '1':
                            if Member.set_flag(username, '2'):
                                self.set_cookie('userflag', '2', path="/", expires_days = 365 )
                                clear_cache_multi(['cur_user:' + username])
                                #self.redirect('/')
                                #return
        
        self.echo('setavatar.html', {
            'title': "设置头像",
            'errors':[],
            'newest_node': Node.get_newest(),
            'wb_avatar_large': wb_avatar_large,
        }, layout='_layout.html')
    
    @authorized(flag=1)
    def post(self):
        errors = []
        username = str(self.get_cookie('username',''))
        userflag = str(self.get_cookie('userflag',''))
        if not username or not userflag:
            self.write('403')
            return
        myfile = self.request.files.get('myfile',[0])[0]
        if myfile:
            im = Image.open(StringIO(myfile['body']))
            max_w = 73
            max_h = 73
            if im.size[0] > max_w or im.size[1] > max_w:
                ss = max(float(im.size[0])/max_w, float(im.size[1])/max_h)
                im = im.resize((int(im.size[0]/ss), int(im.size[1]/ss)), Image.ANTIALIAS)
            
            output = StringIO()
            im.convert('RGB').save(output, 'JPEG', quality = 95)#95
            img_data = output.getvalue()
            output.close()
            
            #self.set_header('Content-Type','image/jpeg')
            #self.write(img_data)
            #return
            
            if IMG_STORAGE=='sae':
                file_path_name = '%s.jpg'% username
                avatar = put_obj2storage(file_name = file_path_name, data = img_data, domain_name = DOMAIN_NAME_AVATAR)
            elif IMG_STORAGE=='upyun':
                u = UpYun(DOMAIN_NAME_AVATAR, UPYUN_USER, UPYUN_PW)
                file_path_name = '/avatar/%s.jpg'% username
                avatar = u.writeFile( file_path_name, img_data, True)
            
            if avatar:
                if username == 'admin':
                    Member.set_flag(username, '99')
                if userflag == '1':
                    if Member.set_flag(username, '2'):
                        self.set_cookie('userflag', '2', path="/", expires_days = 365 )
                        clear_cache_multi(['cur_user:' + username])
                        self.redirect('/setavatar')
                        return
                    else:
                        errors.append('服务器暂时出错，请稍后再试')
                else:
                    self.redirect('/setavatar')
                    return
            else:
                errors.append('保存图片出错，请稍后再试')
        else:
            errors.append('图片没有正确上传')
            
        self.echo('setavatar.html', {
            'title': "设置头像",
            'errors':errors,
            'wb_avatar_large': '',
        }, layout='_layout.html')

class NodePage(BaseHandler):
    def get(self, nodeid):
        n_obj = Node.get_by_key('n-'+str(nodeid))
        if not n_obj:
            self.set_status(404)
            self.write('404')
            return
        
        from_id = int(self.get_argument('id', '0'))
        if from_id<=0 and n_obj['count']:
            from_id = int(n_obj['count'])
        
        to_id = from_id - EACH_PAGE_POST_NUM
        if to_id<0:
            to_id = 0
        
        self.echo('nodedetail.html', {
            'title': n_obj['name'],
            'n_obj': n_obj,
            'from_id': from_id,
            'to_id': to_id,
            'topic_objs': Node.get_page_topic(str(nodeid), from_id, to_id),
            'newest_node': Node.get_newest(),
            'recent_node': Node.get_recent_node(),
            'hot_node': Node.get_hot_node(),
            'recent_topic_objs': Commomkvdb.get_comment_topic_by_keys('recent-topic-home'),
            'comment_topic_objs': Commomkvdb.get_comment_topic_by_keys('recent-comment-topic-home'),            
        }, layout='_layout.html')
        Node.add_node_key('n-'+str(nodeid))
        
class TopicPage(BaseHandler):
    def get(self, nodeid, topicid):
        t_key = 't-%s-%s' % (str(nodeid), str(topicid))
        t_obj = Topic.get_by_key(t_key)
        if not t_obj or t_obj.has_key('hide'):
            self.set_status(404)
            self.echo('error.html', {
                'page': '404',
                'title': "Can't find out this URL",
                'h2': 'Oh, my god!',
                'msg': 'Something seems to be lost...'
            })
            
            return
        if t_obj['cnum']:
            cnum = int(t_obj['cnum'])
            from_id = int(self.get_argument('id', '1'))
            if from_id>1 and from_id%EACH_PAGE_COMMENT_NUM!=1:
                self.redirect('/'+t_key)
                return
            to_id = from_id + EACH_PAGE_COMMENT_NUM - 1
            if to_id > cnum:
                to_id = cnum
            c_objs = Comment.get_comments(t_key, from_id, to_id)
        else:
            c_objs = None
            from_id = to_id = cnum = 0
            
        self.echo('topicdetail.html', {
            'title': t_obj['title'] + ' - ' + t_obj['nodename'],
            'description':'description',
            't_obj': t_obj,
            'c_objs': c_objs,
            'from_id': from_id,
            'to_id': to_id,
            'cnum': cnum,
            'newest_node': Node.get_newest(),
            'recent_node': Node.get_recent_node(),
            'hot_node': Node.get_hot_node(),
            'recent_topic_objs': Commomkvdb.get_comment_topic_by_keys('recent-topic-home'),
            'comment_topic_objs': Commomkvdb.get_comment_topic_by_keys('recent-comment-topic-home'),            
        }, layout='_layout.html')
    
    @authorized(flag=2)
    def post(self, nodeid, topicid):
        author = str(self.get_cookie('username',''))
        content = self.get_argument('content','')
        
        if author and content and len(content)<=COMMENT_MAX_S:
            int_time = int(time())
            #check spam
            u_comment_time = kv.get('u_comment_time:'+author)
            if u_comment_time:
                tlist = u_comment_time.split(',')
                if len(tlist)== MEMBER_RECENT_TOPIC and (int_time-int(tlist[-1])) < 3600:
                    self.write(u'403:不要回复太频繁了 <a href="/t-%s-%s">请返回</a>' % (nodeid, topicid))
                    return
            
            #check repeat
            content = textilize(content)
            #content = safe_encode(content)
            con_md5 = md5(content.encode('utf-8')).hexdigest()
            if mc.get('c_'+con_md5):
                self.write(u'403:请勿灌水 <a href="/t-%s-%s">请返回</a>' % (nodeid, topicid))
                return
            else:
                mc.set('c_'+con_md5, '1', 36000)
            
            ##
            t_key = 't-%s-%s' % (str(nodeid), str(topicid))
            t_obj = Topic.get_by_key(t_key)
            
            if t_obj['cnum']:
                id_num = int(t_obj['cnum']) + 1
            else:
                id_num = 1
            
            c_key = 't-%s-%s-%d' % (str(nodeid), str(topicid), id_num)
            c_obj = COMMENT_DICT.copy()
            c_obj['author'] = author
            c_obj['add'] = int_time
            c_obj['content'] = content
            
            if Commomkvdb.save(c_key, c_obj):
                #topic commont count +1
                t_obj['cnum'] = id_num
                t_obj['reply'] = author
                t_obj['edit'] = int_time
                Commomkvdb.save(t_key, t_obj)
                
                #member recent +key
                #Member.add_key_rencent_comment_topic(author, t_key)
                rt_obj = kv.get('comment-topic-'+author)
                if rt_obj:
                    olist = rt_obj.split(',')
                    if t_key in olist:
                        olist.remove(t_key)
                    olist.insert(0, t_key)
                    kv.set('comment-topic-'+author, ','.join(olist[:MEMBER_RECENT_TOPIC]))
                else:
                    kv.set('comment-topic-'+author, t_key)
                
                #recent comment in home +key
                Commomkvdb.add_key_rencent_topic('recent-comment-topic-home', t_key)
                #all comment counter +1
                Count.key_incr('all-comment-num')
                #notifications
                if t_obj['author'] != author:
                    mentions = findall_mentions(c_obj['content']+' @%s '%t_obj['author'], author)
                else:
                    mentions = findall_mentions(c_obj['content'], author)
                if mentions:
                    tqueue = TaskQueue('default')
                    tqueue.add(Task('/task/mentions/'+t_key, 'member='+','.join(mentions), delay=5))
                
                #set for check spam
                #u_comment_time = kv.get('u_comment_time:'+author)
                if u_comment_time:
                    tlist = u_comment_time.split(',')
                    if str(int_time) not in tlist:
                        tlist.insert(0, str(int_time))
                        u_comment_time = ','.join(tlist[:MEMBER_RECENT_TOPIC])
                        kv.set('u_comment_time:'+author, u_comment_time)
                else:
                    u_comment_time = str(int_time)
                    kv.set('u_comment_time:'+author, u_comment_time)
                
                ##set new sr_code
                cur_user = self.cur_user()
                code_list = [cur_user['code']]
                u_topic_time = kv.get('u_topic_time:'+author)
                if u_topic_time:
                    code_list.append(u_topic_time)
                if u_comment_time:
                    code_list.append(u_comment_time)
                self.set_cookie('usercode', md5(''.join(code_list)).hexdigest(), path="/", expires_days = 365 )
                
                    
                #del cache
                cachekeys = ['get_topic_by_keys:recent-comment-topic-home', 'get_topic_by_keys:comment-topic-'+author, 'get_comment_topic_by_keys:recent-topic-home', 'get_comment_topic_by_keys:recent-comment-topic-home','cur_user:' + author]
                tks = kv.get('recent-topic-home')
                if tks and t_key in tks.split(','):
                    cachekeys.append('get_topic_by_keys:recent-topic-home')
                if id_num<EACH_PAGE_COMMENT_NUM:
                    cachekeys.append('get_comments:%s:1' % t_key)
                else:
                    cachekeys.append('get_comments:%s:%d' % (t_key, [i for i in range(1,id_num,EACH_PAGE_COMMENT_NUM)][-1]))
                clear_cache_multi(cachekeys)
                
                self.redirect('/'+t_key)
                return
        else:
            self.set_status(403)
            self.write('错误: 403 (请返回填写内容 或 内容太长了)')

class GotoTopic(BaseHandler):
    @authorized(flag=2)
    def get(self, t_key):
        t_key = str(t_key)
        m_obj = self.cur_user()
        if m_obj.get('notic', ''):
            klist = m_obj['notic'].split(',')
            if t_key in klist:
                klist.remove(t_key)
                m_obj['notic'] = ','.join(klist)
                if Commomkvdb.save('m-'+str(m_obj['name']), m_obj):
                    clear_cache_multi(['cur_user:'+str(m_obj['name'])])
        self.redirect('/'+t_key)
    
class TaskMentions(BaseHandler):
    def post(self, t_key):
        t_key = str(t_key)
        member = self.get_argument('member','')
        if member:
            clearkeys = []
            for m in member.split(','):
                logging.error(m)
                m_obj = Member.get_by_name(str(m))
                if m_obj:
                    if m_obj.get('notic', ''):
                        klist = m_obj['notic'].split(',')
                    else:
                        klist = []
                    if t_key not in klist:
                        klist.insert(0, t_key)
                        m_obj['notic'] = ','.join(klist[:NOTIFY_NUM])
                        try:
                            if Commomkvdb.save('m-'+str(m), m_obj):
                                clearkeys.append('cur_user:'+str(m))
                        except:
                            pass
            if clearkeys:
                clear_cache_multi(clearkeys)
        self.write('test task')
    
    get = post

class TaskHotNode(BaseHandler):
    def get(self, nodekey, topicnum):
        nodekey = str(nodekey)
        topicnum = str(topicnum)
        h_obj = Commomkvdb.get_by_key('nodekey-topicnum')
        if h_obj:
            h_obj[nodekey] = topicnum
            Commomkvdb.save('nodekey-topicnum', h_obj)
            clear_cache_multi(['get_hot_node'])
        else:
            Commomkvdb.save('nodekey-topicnum', {nodekey:topicnum})
            
    post = get 
    
class Robots(BaseHandler):
    def get(self):
        max_nid = Node.get_max_node_id()
        
        self.echo('robots.txt',{'ids':[x for x in range(1,max_nid)]})

class Feed(BaseHandler):
    def get(self):
        posts = Commomkvdb.get_topic_by_keys('recent-topic-home')[:10]
        output = self.render('index.xml', {
                    'posts':posts,
                    'site_updated':int(time()),
                })
        self.set_header('Content-Type','application/atom+xml')
        self.write(output)

class Sitemap(BaseHandler):
    def get(self, node_id):
        
        urlstr = """<url><loc>%s</loc><changefreq>%s</changefreq><priority>%s</priority></url>\n """
        urllist = []
        urllist.append('<?xml version="1.0" encoding="UTF-8"?>\n')
        urllist.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        
        n_obj = Node.get_by_key('n-'+str(node_id))
        if n_obj:
            max_id = int(n_obj['count'])
            to_id = max_id - 40000
            if to_id<0:
                to_id = 0
            for i in xrange(max_id, to_id,-1):
                urllist.append(urlstr%("%s/t-%s-%d" % (BASE_URL, str(node_id), i), 'weekly', '0.5'))
            
            urllist.append('</urlset>')
            
            self.set_header('Content-Type','text/xml')
            self.write(''.join(urllist))
        else:
            self.write('')

#flag ==2
class NewPostPage(BaseHandler):
    @authorized(flag=2)
    def get(self, nodeid='1'):
        n_obj = Node.get_by_key('n-'+str(nodeid))
        if not n_obj:
            self.set_status(404)
            self.write('404')
            return
        self.echo('newpost.html', {
            'title': "发新帖子",
            'errors':[],
            'n_obj': n_obj,
            't_obj': TOPIC_DICT.copy(),
            'newest_node': Node.get_newest(),
        }, layout='_layout.html')
    
    @authorized(flag=2)
    def post(self, nodeid='1'):
        n_obj = Node.get_by_key('n-'+str(nodeid))
        if not n_obj:
            self.set_status(404)
            self.write('404')
            return
        
        errors = []
        author = str(self.get_cookie('username',''))
        title = self.get_argument('title','')
        content = self.get_argument('content','')
        
        t_obj = TOPIC_DICT.copy()
        if title and content:
            if len(title)<=TITLE_MAX_S and len(content)<=CONTENT_MAX_S:
                int_time = int(time())
                #check spam
                u_topic_time = kv.get('u_topic_time:'+author)
                if u_topic_time:
                    tlist = u_topic_time.split(',')
                    if len(tlist)== MEMBER_RECENT_TOPIC and (int_time-int(tlist[-1])) < 3600:
                        self.write(u'403:不要发帖太频繁了 <a href="/newpost/%s">请返回</a>' % nodeid)
                        return
                
                #check repeat
                content = textilize(content)
                #content = safe_encode(content)
                con_md5 = md5(content.encode('utf-8')).hexdigest()
                if mc.get('c_'+con_md5):
                    self.write(u'403:请勿灌水 <a href="/newpost/%s">请返回</a>' % nodeid)
                    return
                else:
                    mc.set('c_'+con_md5, '1', 36000)
                
                t_obj['title'] = title
                t_obj['nodeid'] = str(nodeid)
                t_obj['nodename'] = n_obj['name']
                t_obj['author'] = author
                t_obj['add'] = int_time
                t_obj['content'] = content
                
                if n_obj['count']:
                    topic_id = int(n_obj['count']) + 1
                else:
                    topic_id = 1
                if Topic.add(topic_id, t_obj):
                    topic_key = 't-%s-%s' % (str(nodeid), str(topic_id))
                    #node count +1
                    n_obj['count'] = str(topic_id)
                    Commomkvdb.save('n-'+str(nodeid), n_obj)
                    
                    #member recent +key
                    #Member.add_key_rencent_topic(author, topic_key)
                    rt_obj = kv.get('topic-'+author)
                    if rt_obj:
                        olist = rt_obj.split(',')
                        if topic_key not in olist:
                            olist.insert(0, topic_key)
                            rt_obj = ','.join(olist[:MEMBER_RECENT_TOPIC])
                            kv.set('topic-'+author, rt_obj)
                    else:
                        rt_obj = topic_key
                        kv.set('topic-'+author, topic_key)
                    
                    #recent in home +key
                    Commomkvdb.add_key_rencent_topic('recent-topic-home', topic_key)
                    #all topic counter +1
                    Count.key_incr('all-topic-num')
                    #hot node
                    tqueue = TaskQueue('default')
                    tqueue.add(Task('/task/hotnode/%s/%s' % ('n-'+str(nodeid), str(topic_id)), delay=5))
                    #notifications
                    mentions = findall_mentions(t_obj['content'], author)
                    if mentions:
                        tqueue.add(Task('/task/mentions/'+topic_key, 'member='+','.join(mentions), delay=8))
                    
                    #set for check spam
                    #u_topic_time = kv.get('u_topic_time:'+author)
                    if u_topic_time:
                        tlist = u_topic_time.split(',')
                        if str(int_time) not in tlist:
                            tlist.insert(0, str(int_time))
                            u_topic_time = ','.join(tlist[:MEMBER_RECENT_TOPIC])
                            kv.set('u_topic_time:'+author, u_topic_time)
                    else:
                        u_topic_time = str(int_time)
                        kv.set('u_topic_time:'+author, u_topic_time)
                    
                    
                    ##set new sr_code
                    cur_user = self.cur_user()
                    code_list = [cur_user['code'],u_topic_time]
                    u_comment_time = kv.get('u_comment_time:'+author)
                    if u_comment_time:
                        code_list.append(u_comment_time)
                    self.set_cookie('usercode', md5(''.join(code_list)).hexdigest(), path="/", expires_days = 365 )
                    
                    
                    #del cache
                    clear_cache_multi(['get_topic_by_keys:recent-topic-home','get_topic_by_keys:topic-' + author, 'get_comment_topic_by_keys:recent-topic-home', 'get_comment_topic_by_keys:recent-comment-topic-home','cur_user:' + author])
                    
                    self.redirect('/'+topic_key)
                    return
                else:
                    errors.append("服务器出现错误，请稍后再试")
            else:
                t_obj['title'] = title
                t_obj['content'] = content
                errors.append(u"注意标题和内容的最大字数:%s %d" % (len(title), len(content)))
        else:
            errors.append("标题和内容必填")
        self.echo('newpost.html', {
            'title': "发新帖子",
            'errors':errors,
            'n_obj': n_obj,
            't_obj': t_obj,
        }, layout='_layout.html')
        
class UploadPhoto(BaseHandler):
    @authorized(flag=2)
    def post(self, username, img_max_size):
        self.set_header('Content-Type','text/html')
        rspd = {'status': 201, 'msg':'ok'}
        
        filetoupload = self.request.files.get('filetoupload','')
        
        if filetoupload:
            myfile = filetoupload[0]
            ##
            im = Image.open(StringIO(myfile['body']))
            max_w = int(img_max_size)
            if im.size[0] > max_w:
                th = float(im.size[0])/max_w
                box = (int(im.size[0]/th), int(im.size[1]/th))
                im = im.resize(box, Image.ANTIALIAS)
            else:
                pass
            
            #normal
            output = StringIO()
            im.convert('RGB').save(output, 'JPEG', quality = 90)#95
            img_data = output.getvalue()
            output.close()
            
            if IMG_STORAGE=='sae':
                file_path_name = '%s-%s.jpg'% ( str(username), str(int(time())))
                uimg = put_obj2storage(file_name = file_path_name, data = img_data, domain_name = DOMAIN_NAME_UPLOAD)
                rspd['url'] = uimg
            elif IMG_STORAGE=='upyun':
                file_path_name = '/%s/%s.jpg'% ( str(username), str(int(time())))
                u = UpYun(DOMAIN_NAME_UPLOAD, UPYUN_USER, UPYUN_PW)
                uimg = u.writeFile( file_path_name, img_data, True)
                rspd['url'] = UPLOAD_BASE_URL + file_path_name
            
            if uimg:
                rspd['status'] = 200
                rspd['msg'] = u'图片已成功上传'
            else:
                rspd['status'] = 500
                rspd['msg'] = u'图片上传失败，可能是网络问题或图片太大，请刷新本页上传'
            
        else:
            rspd['msg'] = u'没有上传图片'
        self.write(json.dumps(rspd))
        return

class Notifications(BaseHandler):
    @authorized(flag=2)
    def get(self):
        cur_user = self.cur_user()
        
        self.echo('notifications.html', {
            'title': "站内提醒",
            'topic_objs': Commomkvdb.get_notifications(cur_user['name'], cur_user.get('notic', '')),
            'newest_node': Node.get_newest(),
            'recent_node': Node.get_recent_node(),
            'recent_topic_objs': Commomkvdb.get_comment_topic_by_keys('recent-topic-home'),
            'comment_topic_objs': Commomkvdb.get_comment_topic_by_keys('recent-comment-topic-home'),                
        }, layout='_layout.html')        
        
#### admin
class AddNodePage(BaseHandler):
    @authorized(flag=99)
    def get(self):
        n_id = str(self.get_argument('id',''))
        self.echo('addnode.html', {
            'title': "添加分类",
            'n_obj':Node.get_by_id_for_edit(n_id),
            'newest_node': Node.get_newest(),
        }, layout='_layout.html')
        
    @authorized(flag=99)
    def post(self):
        n_id = str(self.get_argument('id',''))
        name = self.get_argument('name','')
        imgurl = self.get_argument('imgurl','')
        about = self.get_argument('about','')
        
        if name:
            n_n_id = Node.set_node(n_id, name, imgurl, about)
            if n_n_id:
                self.redirect('/add-node?id=%s'%n_n_id)
                return
        
        self.redirect('/add-node?id=%s'%n_id)
        
class UploadPhotoNode(BaseHandler):
    @authorized(flag=99)
    def post(self):
        self.set_header('Content-Type','text/html')
        rspd = {'status': 201, 'msg':'ok'}
        
        n_id = str(self.get_argument('id',''))
        if n_id:
            filetoupload = self.request.files.get('filetoupload','')
            
            if filetoupload:
                myfile = filetoupload[0]
                ##
                im = Image.open(StringIO(myfile['body']))
                if im.size[0] > 73 or im.size[1] > 73:
                    th = max(float(im.size[0])/73,float(im.size[1])/73)
                    box = (int(im.size[0]/th), int(im.size[1]/th))
                    im = im.resize(box, Image.ANTIALIAS)
                else:
                    pass
                
                #normal
                output = StringIO()
                im.convert('RGB').save(output, 'JPEG', quality = 90)#95
                img_data = output.getvalue()
                output.close()
                
                if IMG_STORAGE=='sae':
                    file_path_name = 'node-img-%s.jpg'%n_id
                    uimg = put_obj2storage(file_name = file_path_name, data = img_data, domain_name = DOMAIN_NAME_UPLOAD)
                    rspd['url'] = uimg
                elif IMG_STORAGE=='upyun':
                    file_path_name = '/nodeimg/%s.jpg'%n_id
                    u = UpYun(DOMAIN_NAME_UPLOAD, UPYUN_USER, UPYUN_PW)
                    uimg = u.writeFile( file_path_name, img_data, True)
                    rspd['url'] = UPLOAD_BASE_URL + file_path_name
                
                if uimg:
                    rspd['status'] = 200
                    rspd['msg'] = u'图片已成功上传'
                else:
                    rspd['status'] = 500
                    rspd['msg'] = u'图片上传失败，可能是网络问题或图片太大，请刷新本页上传'
                
            else:
                rspd['msg'] = u'没有上传图片'
        else:
            rspd['msg'] = u'id 传入错误'
        self.write(json.dumps(rspd))
        return

class SetUserFlagPage(BaseHandler):
    @authorized(flag=99)
    def get(self):
        m_name = str(self.get_argument('name',''))
        self.echo('setuserflag.html', {
            'title': "设置用户权限",
            'm_name': m_name,
            'm_obj':Member.get_by_name_for_edit(m_name),
        }, layout='_layout.html')
    
    @authorized(flag=99)
    def post(self):
        m_name = str(self.get_argument('name',''))
        flag = self.get_argument('flag','')
        
        if m_name and flag:
            if Member.set_flag(m_name, flag):
                clear_cache_multi(['cur_user:' + m_name])
                self.redirect('/set-user-flag?name=%s'%m_name)
                return
        
        self.redirect('/set-user-flag?name=%s'%m_name)
        
class EditPostPage(BaseHandler):
    @authorized(flag=99)
    def get(self):
        t_key = str(self.get_argument('key',''))
        if t_key:
            t_obj = Topic.get_by_key(t_key)
        else:
            t_obj = TOPIC_DICT.copy()
        self.echo('editpost.html', {
            'title': "修改帖子",
            't_key': t_key,
            't_obj': t_obj,
        }, layout='_layout.html')
    
    @authorized(flag=99)
    def post(self):
        t_key = str(self.get_argument('key',''))
        title = self.get_argument('title','')
        content = self.get_argument('content','')
        hide = self.get_argument('hide','')
        
        if t_key and title and content:
            t_obj = Topic.get_by_key(t_key)
            if t_obj:
                t_obj['title'] = title
                t_obj['content'] = textilize(content)
                if hide:
                    t_obj['hide'] = hide
                else:
                    if t_obj.has_key('hide'):
                        del t_obj['hide']
                if Commomkvdb.save(t_key, t_obj):
                    self.redirect('/edit-post?key=%s'%t_key)
                    return
        
        self.redirect('/edit-post?key=%s'%t_key)
    
class EditCommentPage(BaseHandler):
    @authorized(flag=99)
    def get(self):
        t_key = str(self.get_argument('key',''))
        if t_key:
            t_obj = Comment.get_by_key(t_key)
        else:
            t_obj = TOPIC_DICT.copy()
        self.echo('editcomment.html', {
            'title': "修改评论",
            't_key': t_key,
            't_obj': t_obj,
        }, layout='_layout.html')
    
    @authorized(flag=99)
    def post(self):
        t_key = str(self.get_argument('key',''))
        content = self.get_argument('content','')
        
        if t_key and content:
            t_obj = Comment.get_by_key(t_key)
            if t_obj:
                t_obj['content'] = textilize(content)
                if Commomkvdb.save(t_key, t_obj):
                    self.redirect('/edit-comment?key=%s'%t_key)
                    return
        
        self.redirect('/edit-comment?key=%s'%t_key)

####
class NotFoundPage(BaseHandler):
    def get(self):
        self.set_status(404)
        self.echo('error.html', {
            'page': '404',
            'title': "Can't find out this URL",
            'h2': 'Oh, my god!',
            'msg': 'Something seems to be lost...'
        })

########
urls = [
    (r"/", HomePage),
    (r"/qqlogin", QQLoginPage),
    (r"/qqcallback", QQCallback),
    (r"/setname", SetName),
    (r"/login", LoginPage),
    (r"/sigin", SiginPage),
    (r"/logout", LogoutPage),
    (r"/member/([a-zA-Z0-9]+)", MemberPage),
    (r"/t-(\d+)-(\d+)", TopicPage),
    (r"/n-(\d+)", NodePage),
    (r"/edit-post", EditPostPage),
    (r"/edit-comment", EditCommentPage),
    (r"/newpost/(\d*)", NewPostPage),
    (r"/setavatar", SetAvatar),
    (r"/add-node", AddNodePage),
    (r"/set-user-flag", SetUserFlagPage),
    (r"/goto/([t\-0-9]+)", GotoTopic),
    (r"/notifications", Notifications),
    (r"/set-user-flag", SetUserFlagPage),
    (r"/uploadphoto/([a-zA-Z0-9]+)/(650|590)", UploadPhoto),
    (r"/uploadphotonode", UploadPhotoNode),
    (r"/task/mentions/([t\-0-9]+)", TaskMentions),
    (r"/task/hotnode/([n\-0-9]+)/(\d+)", TaskHotNode),
    (r"/feed", Feed),
    (r"/sitemap-(\d+)", Sitemap),
    (r"/robots.txt", Robots),
    (r".*", NotFoundPage)
]
