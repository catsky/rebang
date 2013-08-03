# -*- coding: utf-8 -*-

import logging

import re
from time import time
from datetime import datetime,timedelta
import json

from google.appengine.api import images,memcache
from google.appengine.ext import db, deferred
import yui

from setting import *
from common import BaseHandler, findall_mentions, obj_runput, textilize
from model import Avatar, Comment, Counter, GoogleUser, KeyStrValue, Member, MemberInfo, Node, Photo, Topic

logging.getLogger().setLevel(logging.DEBUG)
##

###############
class HomePage(BaseHandler):
    def get(self):
        self.echo('home.html', {
            'title': "首页",
            'topic_objs': KeyStrValue.get_topic_objs('recent-topic-home'),
            'site_counts': Counter.get_site_counts(),
            'newest_node': Node.get_newest(),
            'recent_node': Node.get_recent_node(),
            'hot_node': Node.get_hot_node(),
            'reply_topic_objs': KeyStrValue.get_topic_key_title('recent-reply-topic'),
        }, layout='_layout.html')

class SetName(BaseHandler):
    def get(self):
        req_user = self.request.user
        gu_obj = GoogleUser.get_or_insert(req_user.user_id())
        if gu_obj.name:
            self.redirect('/')
            return
        else:
            self.echo('setname.html', {
                'title': "设置名字",
                'errors':[],
                'name':'',
                'newest_node': Node.get_newest(),
            }, layout='_layout.html')
    
    def post(self):
        req_user = self.request.user
        gu_obj = GoogleUser.get_or_insert(req_user.user_id())
        if gu_obj.name:
            self.redirect('/')
            return
        
        errors = []
        name = self.POST['name'].strip().lower()
        if name:
            if len(name)<20:
                if re.search('^[a-zA-Z0-9]+$', name):
                    check_obj = Member.get_by_key_name(str(name))
                    if check_obj:
                        errors.append('该用户名已被注册，请换一个吧')
                    else:
                        #get member id
                        mid_obj = Counter.get_or_insert('member_auto_increment',name = 'member_auto_increment', value = 1)
                        nuser_obj = Member(key_name=name, id = mid_obj.value, flag = 1, add = int(time()))
                        nuser_obj.put()
                        if nuser_obj.is_saved():
                            #set google user
                            gu_obj.name = name
                            db.run_in_transaction(obj_runput,gu_obj)
                            #all member num +1
                            mid_obj.value += 1
                            db.run_in_transaction(obj_runput,mid_obj)
                            self.redirect('/setavatar')
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
            'newest_node': Node.get_newest(),
        }, layout='_layout.html')

def avatar_expires():
    #'Tue, 01-May-2012 10:45:21 GMT'
    d = datetime.utcnow() + timedelta(hours =+ 8,days =+ 300)
    return d.strftime('%a, %d-%b-%Y %H:%M:%S GMT')

class AvatarShow(yui.RequestHandler):
    def get(self, name, size=''):
        if size not in ['','%21normal','%21mini']:
            self.error(404)
            return
        a_obj = Avatar.get_by_key_name(name)
        if a_obj and a_obj.content:
            self.header['Content-Type'] = "image/png"
            self.header['Cache-Control'] = "max-age=172800, public, must-revalidate"
            self.header['Expires'] = avatar_expires()
            
            sized = {'%21normal':48,'%21mini':24}
            memkey = "avatar_%s_%d"%(name,sized.get(size,73))
            img = memcache.get(memkey)
            if img is None:
                if size=='':
                    img = a_obj.content
                else:
                    imgobj = images.Image(a_obj.content)
                    imgobj.resize(sized[size], sized[size])
                    imgobj.im_feeling_lucky()
                    img = imgobj.execute_transforms(output_encoding=images.JPEG, quality=95)
                memcache.set(memkey,img,3600)
            self.write(img)
        else:
            self.error(404)
        
class PhotoShow(yui.RequestHandler):
    def get(self, name):
        a_obj = Photo.get_by_key_name(name)
        if a_obj and a_obj.content:
            self.header['Content-Type'] = "image/png"
            self.header['Cache-Control'] = "max-age=172800, public, must-revalidate"
            self.header['Expires'] = avatar_expires()
            
            self.write(a_obj.content)
        else:
            self.error(404)

class SetAvatar(BaseHandler):
    def get(self):
        if self.cur_user:
            self.echo('setavatar.html', {
                'title': "设置头像",
                'errors':[],
                'newest_node': Node.get_newest(),
            }, layout='_layout.html')
        else:
            self.redirect('/')
    
    def post(self):
        if self.cur_user:
            file_content = self.request.get('myfile','')
            errors = []
            if file_content:
                imgobj = images.Image(file_content)
                if imgobj.width <= 73 and imgobj.height <= 73:
                    img_large = file_content
                else:
                    imgobj.resize(73, 73)
                    imgobj.im_feeling_lucky()
                    img_large = imgobj.execute_transforms(output_encoding=images.JPEG, quality=95)
                    
                av_obj = Avatar.get_or_insert(self.cur_user.name)
                av_obj.content = img_large
                av_obj.put()
                if av_obj.is_saved():
                    m_obj = Member.get_by_key_name(self.cur_user.name)
                    if m_obj:
                        if m_obj.flag ==1:
                            if m_obj.id == 1:
                                m_obj.flag = 99
                            else:
                                m_obj.flag = 2
                            db.run_in_transaction(obj_runput,m_obj, ['cur_user:'+self.request.user.user_id()])
                    memcache.delete_multi(["avatar_%s_%d"%(self.cur_user.name,x) for x in [73,48,24]])
                    self.redirect('/setavatar')
                    return
                else:
                    errors.append('服务器出现意外错误，请稍后再试')
            else:
                self.echo('setavatar.html', {
                    'title': "设置头像",
                    'errors':errors,
                    'newest_node': Node.get_newest(),
                }, layout='_layout.html')
                
        else:
            self.redirect('/')

class TopicPage(BaseHandler):
    def get(self, nodeid, topicid):
        topic_key = '%s-%s' % (nodeid, topicid)
        t_obj = Topic.get_by_key_name(topic_key)
        if not t_obj:
            self.error(404)
            self.echo('error.html', {
                'page': '404',
                'title': "Can't find out this URL",
                'h2': 'Oh, my god!',
                'msg': 'Something seems to be lost...'
            })
            return
        
        if t_obj.cnum:
            from_id = int(self.request.get('id', '1'))
            if from_id>1 and from_id%EACH_PAGE_COMMENT_NUM!=1:
                self.redirect('/t-'+topic_key)
                return
            to_id = from_id + EACH_PAGE_COMMENT_NUM - 1
            if to_id > t_obj.cnum:
                to_id = t_obj.cnum
            c_objs = Comment.get_comments(topic_key, from_id, to_id)
        else:
            c_objs = None
            from_id = to_id = cnum = 0
        
        self.echo('topicdetail.html', {
            'title': t_obj.title + ' - ' + t_obj.node.name,
            'description':'description',
            't_obj': t_obj,
            'c_objs': c_objs,
            'from_id': from_id,
            'to_id': to_id,
            'newest_node': Node.get_newest(),
            'recent_node': Node.get_recent_node(),
            'hot_node': Node.get_hot_node(),
            'recent_topic_objs': KeyStrValue.get_topic_key_title('recent-topic-home'),
            'reply_topic_objs': KeyStrValue.get_topic_key_title('recent-reply-topic'),
        }, layout='_layout.html')
        
    def post(self, nodeid, topicid):
        if self.cur_user and self.cur_user.flag>1:
            author = self.cur_user.name
            content = self.POST['content']
            
            if content and len(content)<=COMMENT_MAX_S:
                int_time = int(time())
                
                #check spam
                mi_obj = MemberInfo.get_or_insert(author)
                if mi_obj.replyt:
                    t_list = mi_obj.replyt.split(',')
                    if len(t_list) == MEMBER_RECENT_REPLY and (int_time-int(t_list[-1])) < 3600:
                        self.write(u'403:不要回复太频繁了 <a href="/t-%s-%s">请返回</a>' % (nodeid, topicid))
                        return
                
                #check repeat
                content = textilize(content)
                #content = safe_encode(content)
                con_md5 = md5(content.encode('utf-8')).hexdigest()
                if memcache.get('c_'+con_md5):
                    self.write(u'403:请勿灌水 <a href="/t-%s-%s">请返回</a>' % (nodeid, topicid))
                    return
                else:
                    memcache.set('c_'+con_md5, '1', 36000)
                
                topic_key = '%s-%s' % (nodeid, topicid)
                t_obj = Topic.get_by_key_name(topic_key)
                if not t_obj:
                    self.error(404)
                    self.write('404: not found')
                    return
                
                if t_obj.cnum:
                    id_num = t_obj.cnum + 1
                else:
                    id_num = 1
                
                c_key = '%s-%d' % (topic_key, id_num)
                c_obj = Comment(key_name=c_key)
                c_obj.author = author
                c_obj.add = int_time
                c_obj.con = content
                c_obj.put()
                if c_obj.is_saved():
                    #topic commont count +1
                    t_obj.cnum = id_num
                    t_obj.reply = author
                    t_obj.edit = int_time
                    db.run_in_transaction(obj_runput,t_obj)
                    #memberinfo
                    mi_obj.replyn += 1
                    if mi_obj.replyk:
                        t_list = mi_obj.replyk.split(',')
                        if topic_key in t_list:
                            t_list.remove(topic_key)
                        t_list.insert(0, topic_key)
                        mi_obj.replyk = ','.join(t_list[:MEMBER_RECENT_REPLY])
                    else:
                        mi_obj.replyk = topic_key
                        
                    if mi_obj.replyt:
                        t_list = mi_obj.replyt.split(',')
                        t_list.insert(0, str(int_time))
                        mi_obj.replyt = ','.join(t_list[:MEMBER_RECENT_REPLY])
                    else:
                        mi_obj.replyt = str(int_time)
                    db.run_in_transaction(obj_runput,mi_obj,['reply_objs:'+author])
                    #recent reply +key
                    hi_obj = KeyStrValue.get_or_insert('recent-reply-topic')
                    if hi_obj.value:
                        t_list = hi_obj.value.split(',')
                        if topic_key in t_list:
                            t_list.remove(topic_key)
                        t_list.insert(0, topic_key)
                        hi_obj.value = ','.join(t_list[:RECENT_COMMENT_NUM])
                        db.run_in_transaction(obj_runput,hi_obj,['get_topic_key_title:recent-reply-topic'])
                    else:
                        hi_obj.value = topic_key
                        db.run_in_transaction(obj_runput,hi_obj,['get_topic_key_title:recent-reply-topic'])
                    #all reply counter +1
                    at_obj = Counter.get_or_insert('all-reply-num', name = 'all-reply-num')
                    at_obj.value += 1
                    db.run_in_transaction(obj_runput,at_obj)
                    #notifications
                    if t_obj.author != author:
                        mentions = findall_mentions(c_obj.con+' @%s '%t_obj.author, author)
                    else:
                        mentions = findall_mentions(c_obj.con, author)
                    
                    if mentions:
                        deferred.defer(set_mentions, topic_key, ','.join(mentions), _countdown=8, _queue="default")
                    
                    #del cache
                    cache_keys = []
                    hi_obj = KeyStrValue.get_or_insert('recent-topic-home')
                    if hi_obj.value:
                        if topic_key in hi_obj.value.split(','):
                            cache_keys.append('get_topic_objs:recent-topic-home')
                    
                    if id_num<EACH_PAGE_COMMENT_NUM:
                        cache_keys.append('get_comments:%s:1' % topic_key)
                    else:
                        cache_keys.append('get_comments:%s:%d' % (topic_key, [i for i in range(1,id_num,EACH_PAGE_COMMENT_NUM)][-1]))
                    
                    if cache_keys:
                        memcache.delete_multi(cache_keys)
                    
                    
                    self.redirect('/t-%s#reply%d'%(topic_key,id_num))
                    return
            else:
                self.write('错误: 没有内容 或 内容太长了，请后退返回修改！')
        else:
            self.error(403)
            self.write('403:forbidden')
        
class NodePage(BaseHandler):
    def get(self, nodeid):
        n_obj = Node.get_by_id(int(nodeid))
        if not n_obj:
            self.error(404)
            self.echo('error.html', {
                'page': '404',
                'title': "Can't find out this URL",
                'h2': 'Oh, my god!',
                'msg': 'Something seems to be lost...'
            })
            return
        
        from_id = int(self.request.get('id', '0'))
        if from_id<=0 and n_obj.count:
            from_id = n_obj.count
        
        to_id = from_id - EACH_PAGE_POST_NUM
        if to_id<0:
            to_id = 0
        
        newest_node = Node.get_newest()
        self.echo('nodedetail.html', {
            'title': n_obj.name,
            'n_obj': n_obj,
            'from_id': from_id,
            'to_id': to_id,
            'topic_objs': Node.get_page_topic(nodeid, from_id, to_id),
            'newest_node': newest_node,
            'recent_node': Node.get_recent_node(),
            'hot_node': Node.get_hot_node(),
            'recent_topic_objs': KeyStrValue.get_topic_key_title('recent-topic-home'),
            'reply_topic_objs': KeyStrValue.get_topic_key_title('recent-reply-topic'),            
        }, layout='_layout.html')
        if len(newest_node)==10:
            KeyStrValue.add_node_key(nodeid)
        
class MemberPage(BaseHandler):
    def get(self, name):
        name = name.lower()
        m_obj = Member.get_by_key_name(name)
        if m_obj:
            self.echo('member.html', {
                'title': m_obj.name,
                'm_obj': m_obj,
                'mi_obj': MemberInfo.get_by_key_name(name),
                'newest_node': Node.get_newest(),
                'recent_node': Node.get_recent_node(),
                'hot_node': Node.get_hot_node(),
                'recent_topic_objs': KeyStrValue.get_topic_key_title('recent-topic-home'),
                'reply_topic_objs': KeyStrValue.get_topic_key_title('recent-reply-topic'),            
            }, layout='_layout.html')
        else:
            self.error(404)
            self.echo('error.html', {
                'page': '404',
                'title': "Can't find out this URL",
                'h2': 'Oh, my god!',
                'msg': 'Something seems to be lost...'
            })
            return
            
class Robots(BaseHandler):
    def get(self):
        max_nid_obj = Counter.get_or_insert('node_auto_increment', name='node_auto_increment', value = 1)
        self.echo('robots.txt',{'ids':[x for x in range(1,max_nid_obj.value)]})

class FeedPage(BaseHandler):
    def get(self):
        self.header['Content-Type'] = "application/atom+xml"
        self.echo('index.xml', {
                    'posts':KeyStrValue.get_topic_objs('recent-topic-home')[:FEED_NUM],
                    'site_updated':int(time()),
        })

class Sitemap(yui.RequestHandler):
    def get(self, node_id):
        n_obj = Node.get_by_id(int(node_id))
        if n_obj:
            
            urlstr = """<url><loc>%s</loc><changefreq>%s</changefreq><priority>%s</priority></url>\n """
            urllist = []
            urllist.append('<?xml version="1.0" encoding="UTF-8"?>\n')
            urllist.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            
            urllist.append(urlstr%("%s/n-%s" % (BASE_URL, str(node_id)), 'weekly', '0.6'))
            
            max_id = n_obj.count
            to_id = max_id - 40000
            if to_id<0:
                to_id = 0
            for i in xrange(max_id, to_id,-1):
                urllist.append(urlstr%("%s/t-%s-%d" % (BASE_URL, str(node_id), i), 'weekly', '0.5'))
            
            urllist.append('</urlset>')
            
            self.header['Content-Type'] = "text/xml"
            self.write(''.join(urllist))
        else:
            self.write('')

def set_mentions(topic_key,allmember):
    for m in allmember.split(','):
        m_obj = Member.get_by_key_name(m)
        if m_obj:
            if m_obj.notic:
                t_list = m_obj.notic.split(',')
                if topic_key not in t_list:
                    t_list.insert(0, topic_key)
                    m_obj.notic = ','.join(t_list[:NOTIFY_NUM])
                    m_obj.put()
            else:
                m_obj.notic = topic_key
                m_obj.put()
    
### member
class NewPostPage(BaseHandler):
    def get(self, nodeid='1'):
        if self.cur_user and self.cur_user.flag>1:
            n_obj = Node.get_by_id(int(nodeid))
            if not n_obj:
                self.error(404)
                self.echo('error.html', {
                    'page': '404',
                    'title': "Can't find out this URL",
                    'h2': 'Oh, my god!',
                    'msg': 'Something seems to be lost...'
                })
                return
            self.echo('newpost.html', {
                'title': "发新帖子",
                'errors':[],
                'n_obj': n_obj,
                't_obj': Topic(),
                'newest_node': Node.get_newest(),
            }, layout='_layout.html')
        else:
            self.error(403)
            self.write('403:forbidden')
    
    def post(self, nodeid='1'):
        if self.cur_user and self.cur_user.flag>1:
            n_obj = Node.get_by_id(int(nodeid))
            if not n_obj:
                self.error(404)
                self.write('404: not found')
                return
            
            errors = []
            author = self.cur_user.name
            title = self.POST['title']
            content = self.POST['content']
            
            if title and content:
                if len(title)<=TITLE_MAX_S and len(content)<=CONTENT_MAX_S:
                    int_time = int(time())
                    #check spam
                    mi_obj = MemberInfo.get_or_insert(author)
                    if mi_obj.topict:
                        t_list = mi_obj.topict.split(',')
                        if len(t_list) == MEMBER_RECENT_TOPIC and (int_time-int(t_list[-1])) < 3600:
                            self.write(u'403:不要发帖太频繁了 <a href="/newpost/%s">请返回</a>' % nodeid)
                            return
                    
                    #check repeat
                    content = textilize(content)
                    #content = safe_encode(content)
                    con_md5 = md5(content.encode('utf-8')).hexdigest()
                    if memcache.get('c_'+con_md5):
                        self.write(u'403:请勿灌水 <a href="/newpost/%s">请返回</a>' % nodeid)
                        return
                    else:
                        memcache.set('c_'+con_md5, '1', 36000)                    
                    
                    if n_obj.count:
                        topic_id = n_obj.count + 1
                    else:
                        topic_id = 1
                    
                    topic_key = '%s-%s' % (nodeid, str(topic_id))
                    
                    t_obj = Topic(key_name=topic_key)
                    t_obj.title = title
                    t_obj.author = author
                    t_obj.add = int_time
                    t_obj.con = textilize(content)
                    #t_obj.con = safe_encode(content)
                    t_obj.put()
                    if t_obj.is_saved():
                        #node count +1
                        n_obj.count += 1
                        db.run_in_transaction(obj_runput,n_obj)
                        #memberinfo
                        mi_obj.topicn += 1
                        if mi_obj.topick:
                            t_list = mi_obj.topick.split(',')
                            t_list.insert(0, topic_key)
                            mi_obj.topick = ','.join(t_list[:MEMBER_RECENT_TOPIC])
                        else:
                            mi_obj.topick = topic_key
                            
                        if mi_obj.topict:
                            t_list = mi_obj.topict.split(',')
                            t_list.insert(0, str(int_time))
                            mi_obj.topict = ','.join(t_list[:MEMBER_RECENT_TOPIC])
                        else:
                            mi_obj.topict = str(int_time)
                        db.run_in_transaction(obj_runput,mi_obj,['topic_objs:'+author])
                        #recent in home +key
                        hi_obj = KeyStrValue.get_or_insert('recent-topic-home')
                        if hi_obj.value:
                            t_list = hi_obj.value.split(',')
                            t_list.insert(0, topic_key)
                            hi_obj.value = ','.join(t_list[:RECENT_POST_NUM])
                        else:
                            hi_obj.value = topic_key
                        db.run_in_transaction(obj_runput,hi_obj,['get_topic_objs:recent-topic-home', 'get_topic_key_title:recent-topic-home'])
                        #all topic counter +1
                        at_obj = Counter.get_or_insert('all-topic-num', name = 'all-topic-num')
                        at_obj.value += 1
                        db.run_in_transaction(obj_runput,at_obj)
                        #notifications
                        mentions = findall_mentions(t_obj.con, author)
                        if mentions:
                            deferred.defer(set_mentions, topic_key, ','.join(mentions), _countdown=8, _queue="default")
                        
                        self.redirect('/t-'+topic_key)
                        return
                else:
                    t_obj = Topic(title = title, con = content)
                    errors.append(u"注意标题和内容的最大字数限制，当前字数:%s %d" % (len(title), len(content)))
            else:
                t_obj = Topic(title = title, con = content)
                errors.append("标题和内容必填")
            
            self.echo('newpost.html', {
                'title': "发新帖子",
                'errors':errors,
                'n_obj': n_obj,
                't_obj': t_obj,
                'newest_node': Node.get_newest(),
            }, layout='_layout.html')
            
        else:
            self.error(403)
            self.write('403:forbidden')

class UploadPhoto(BaseHandler):
    def post(self, username, img_max_size):
        if self.cur_user and self.cur_user.flag>1:
            self.header['Content-Type'] = "text/html"
            rspd = {'status': 201, 'msg':'ok'}
            
            file_content = self.request.get('filetoupload','')
            if file_content:
                imgobj = images.Image(file_content)
                max_w = int(img_max_size)
                if imgobj.width <= max_w:
                    #img_data = file_content
                    pass
                else:
                    imgobj.resize(width=max_w)
                imgobj.im_feeling_lucky()
                
                img_data = imgobj.execute_transforms(output_encoding=images.JPEG, quality=90)
                
                ni_obj = Photo(key_name = '%s-%s'%(username, str(int(time()))), content = img_data)
                ni_obj.put()
                if ni_obj.is_saved():
                    rspd['status'] = 200
                    rspd['msg'] = u'图片已成功上传'
                    rspd['url'] = '%s/photo/%s.jpg' % (BASE_URL, ni_obj.key().name())
                else:
                    rspd['status'] = 500
                    rspd['msg'] = u'图片上传失败，可能是网络问题或图片太大，请刷新本页再上传'
            else:
                rspd['msg'] = u'没有上传图片'
            self.write(json.dumps(rspd))
        else:
            self.error(403)
            self.write('403:forbidden')

class Notifications(BaseHandler):
    def get(self):
        if self.cur_user:
            self.echo('notifications.html', {
                'title': "站内提醒",
                'newest_node': Node.get_newest(),
                'recent_node': Node.get_recent_node(),
                'hot_node': Node.get_hot_node(),
                'recent_topic_objs': KeyStrValue.get_topic_key_title('recent-topic-home'),
                'reply_topic_objs': KeyStrValue.get_topic_key_title('recent-reply-topic'),            
            }, layout='_layout.html')
            
        else:
            self.redirect('/')

class GotoTopic(BaseHandler):
    def get(self, t_key):
        t_key = str(t_key)
        cur_user = self.cur_user
        if cur_user.notic:
            klist = cur_user.notic.split(',')
            if t_key in klist:
                klist.remove(t_key)
                cur_user.notic = ','.join(klist)
                #cur_user.put()
                db.run_in_transaction(obj_runput,cur_user,['cur_user:'+self.request.user.user_id()])
        self.redirect('/t-'+t_key)

### admin
class AddNode(BaseHandler):
    def get(self):
        if self.cur_user and self.cur_user.flag==99:
            n_id = self.request.get('id')
            if n_id:
                n_obj = Node.get_by_id(int(n_id))
            else:
                n_obj = Node()
                
            if n_obj:
                title = "修改分类"
            else:
                n_obj = Node()
                title = "添加分类"
                
            self.echo('addnode.html', {
                'title': title,
                'n_obj': n_obj,
                'newest_node': Node.get_newest(),
            }, layout='_layout.html')
        else:
            self.error(403)
            self.write('403:forbidden')
        
    def post(self):
        if self.cur_user and self.cur_user.flag==99:
            n_id = self.request.get('id')
            name = self.POST['name']
            imgurl = self.POST['imgurl']
            about = self.POST['about']
            
            if name:
                if n_id:
                    n_obj = Node.get_by_id(int(n_id))
                else:
                    n_obj = None
                    
                if n_obj:
                    n_obj.name = name
                    n_obj.imgurl = imgurl
                    n_obj.about = about
                    n_obj.put()
                else:
                    #get node id
                    nid_obj = Counter.get_or_insert('node_auto_increment', name='node_auto_increment', value = 1)
                    
                    n_obj = Node(key=db.Key.from_path('Node', nid_obj.value))
                    n_obj.name = name
                    n_obj.imgurl = imgurl
                    n_obj.about = about
                    n_obj.put()
                    
                    if n_obj.is_saved():
                        n_id = nid_obj.value
                        nid_obj.value += 1
                        db.run_in_transaction(obj_runput,nid_obj,['newest_add_node'])
            
            self.redirect('/add-node?id=%s'%str(n_id))
        else:
            self.error(403)
            self.write('403:forbidden')

class UploadPhotoNode(BaseHandler):
    def post(self):
        if self.cur_user and self.cur_user.flag==99:
            self.header['Content-Type'] = "text/html"
            rspd = {'status': 201, 'msg':'ok'}
            
            n_id = self.request.get('id')
            if n_id:
                file_content = self.request.get('filetoupload','')
                if file_content:
                    imgobj = images.Image(file_content)
                    if imgobj.width <= 73 and imgobj.height <= 73:
                        img_large = file_content
                    else:
                        imgobj.resize(73, 73)
                        imgobj.im_feeling_lucky()
                        img_large = imgobj.execute_transforms(output_encoding=images.JPEG, quality=95)
                        
                    ni_obj = Photo.get_or_insert('node-'+n_id)
                    ni_obj.content = img_large
                    ni_obj.put()
                    if ni_obj.is_saved():
                        rspd['status'] = 200
                        rspd['msg'] = u'图片已成功上传'
                        rspd['url'] = '/photo/node-%s.jpg'%n_id
                    else:
                        rspd['status'] = 500
                        rspd['msg'] = u'图片上传失败，可能是网络问题或图片太大，请刷新本页再上传'
                else:
                    rspd['msg'] = u'没有上传图片'
            else:
                rspd['msg'] = u'id 传入错误'
                
            self.write(json.dumps(rspd))
        else:
            self.error(403)
            self.write('403:forbidden')

class SetUserFlagPage(BaseHandler):
    def get(self):
        if self.cur_user and self.cur_user.flag==99:
            m_name = self.request.get('name')
            m_obj = None
            if m_name:
                m_obj = Member.get_by_key_name(m_name)
            
            self.echo('setuserflag.html', {
                'title': "设置用户权限",
                'm_name': m_name,
                'm_obj':m_obj,
            }, layout='_layout.html')
            
        else:
            self.error(403)
            self.write('403:forbidden')
            
    def post(self):
        if self.cur_user and self.cur_user.flag==99:
            m_name = self.request.get('name')
            flag = self.request.get('flag')
            m_obj = None
            if m_name and flag:
                m_obj = Member.get_by_key_name(m_name)
                if m_obj:
                    m_obj.flag = int(flag)
                    m_obj.put()
                else:
                    self.redirect('/set-user-flag')
                    return
            
            self.redirect('/set-user-flag?name=%s'%str(m_name))
        else:
            self.error(403)
            self.write('403:forbidden')

class EditPostPage(BaseHandler):
    def get(self):
        if self.cur_user and self.cur_user.flag==99:
            t_key = self.request.get('key')
            if t_key:
                t_obj = Topic.get_by_key_name(t_key)
            else:
                t_obj = None
            self.echo('editpost.html', {
                'title': "修改帖子",
                't_obj': t_obj,
            }, layout='_layout.html')
        else:
            self.error(403)
            self.write('403:forbidden')
    
    def post(self):
        if self.cur_user and self.cur_user.flag==99:
            t_key = self.request.get('key')
            title = self.POST['title']
            content = self.POST['content']
            
            if t_key and title and content:
                t_obj = Topic.get_by_key_name(t_key)
                if t_obj:
                    t_obj.title = title
                    t_obj.con = textilize(content)
                    db.run_in_transaction(obj_runput, t_obj)
                
            self.redirect('/edit-post?key=%s'%str(t_key))
        else:
            self.error(403)
            self.write('403:forbidden')

class EditCommentPage(BaseHandler):
    def get(self):
        if self.cur_user and self.cur_user.flag==99:
            t_key = self.request.get('key')
            if t_key:
                t_obj = Comment.get_by_key_name(t_key)
            else:
                t_obj = None
            self.echo('editcomment.html', {
                'title': "修改评论",
                't_obj': t_obj,
            }, layout='_layout.html')
            
        else:
            self.error(403)
            self.write('403:forbidden')
    
    def post(self):
        if self.cur_user and self.cur_user.flag==99:
            t_key = self.request.get('key')
            content = self.POST['content']
            if t_key and content:
                t_obj = Comment.get_by_key_name(t_key)
                if t_obj:
                    t_obj.con = textilize(content)
                    db.run_in_transaction(obj_runput, t_obj)
            
            self.redirect('/edit-comment?key=%s'%str(t_key))
            
        else:
            self.error(403)
            self.write('403:forbidden')        

###
class NotFoundPage(BaseHandler):
    def get(self):
        self.error(404)
        self.echo('error.html', {
            'page': '404',
            'title': "Can't find out this URL",
            'h2': 'Oh, my god!',
            'msg': 'Something seems to be lost...'
        })

    post = get

#################
application = yui.WsgiApplication([
    ('/', HomePage),
    ('/setname', SetName),
    ('/setavatar', SetAvatar),
    ('/avatar/([a-zA-Z0-9]+).jpg(.*)', AvatarShow),
    ('/photo/(.+).jpg', PhotoShow),
    ('/t-(\d+)-(\d+)', TopicPage),
    ('/n-(\d+)', NodePage),
    ('/member/([a-zA-Z0-9]+)', MemberPage),
    ('/feed', FeedPage),
    ('/sitemap-(\d+)', Sitemap),
    ('/robots.txt', Robots),
    #member
    ('/newpost/(\d*)', NewPostPage),
    ('/uploadphoto/([a-zA-Z0-9]+)/(650|590)', UploadPhoto),
    ('/notifications', Notifications),
    ('/goto/([\-\d]+)', GotoTopic),
    #admin
    ('/add-node', AddNode),
    ('/edit-post', EditPostPage),
    ('/edit-comment', EditCommentPage),
    ('/uploadphotonode', UploadPhotoNode),
    ('/set-user-flag', SetUserFlagPage),
    ('.*', NotFoundPage)
    ])

if not is_debug:
    if ONLY_USE_MAJOR_DOMAIN:
        application = yui.redirect_to_major_domain(application, MAJOR_DOMAIN)
