# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.api import memcache

from common import memcached, obj_runput

from yui import CachedProperty

from setting import *

##
class Counter(db.Model):
    #key_name
    name = db.StringProperty(default='')
    value = db.IntegerProperty(default=0)
    
    @staticmethod
    @memcached('get_site_counts', 300)
    def get_site_counts():
        site_info = []
        
        member_num = Counter.get_by_key_name('member_auto_increment')
        if member_num:
            if member_num.value>1:
                site_info.append(('会员',member_num.value-1))
        
        node_num = Counter.get_by_key_name('node_auto_increment')
        if node_num:
            if node_num.value>1:
                site_info.append(('主题',node_num.value-1))
            
        topic_num = Counter.get_by_key_name('all-topic-num')
        if topic_num:
            site_info.append(('帖子',topic_num.value))
        
        comment_num = Counter.get_by_key_name('all-reply-num')
        if comment_num:
            site_info.append(('回复',comment_num.value))
        return site_info
    

class Member(db.Model):
    #key name: username
    id = db.IntegerProperty(indexed=False,default=0)
    flag = db.IntegerProperty(indexed=False,default=0)
    add = db.IntegerProperty(indexed=False,default=0)
    notic = db.StringProperty(indexed=False,default='')#max 16 '999-100000'
    
    @property
    def name(self):
        return self.key().name()
    
    @property
    def notic_objs(self):
        return Topic.get_by_key_name(self.notic.split(','))

class MemberInfo(db.Model):
    #key name: username
    topicn = db.IntegerProperty(indexed=False,default=0) #counter
    replyn = db.IntegerProperty(indexed=False,default=0) #counter
    topick = db.StringProperty(indexed=False,default='') #key
    replyk = db.StringProperty(indexed=False,default='') #key
    topict = db.StringProperty(indexed=False,default='') #time
    replyt = db.StringProperty(indexed=False,default='') #time
    
    @property
    @memcached('topic_objs', 300, lambda self: self.key().name())
    def topic_objs(self):
        if self.topick:
            return Topic.get_by_key_name(self.topick.split(','))
        else:
            return None
    
    @property
    @memcached('reply_objs', 300, lambda self: self.key().name())
    def reply_objs(self):
        if self.replyk:
            return Topic.get_by_key_name(self.replyk.split(','))
        else:
            return None

class GoogleUser(db.Model):
    #key name:id
    name = db.StringProperty(indexed=False,default='')

class Node(db.Model):
    #sorted id
    name = db.StringProperty(indexed=False,default='')
    count = db.IntegerProperty(default=0)
    imgurl = db.StringProperty(indexed=False,default='')
    about = db.StringProperty(indexed=False,default='')
    
    @property
    def id(self):
        return self.key().id()
    
    @staticmethod
    @memcached('newest_add_node', 600)
    def get_newest():
        nid_obj = Counter.get_or_insert('node_auto_increment', name='node_auto_increment', value = 1)
        from_id = nid_obj.value - 1
        to_id = from_id - 10
        if to_id<0:
            to_id = 0
        objs = []
        n_objs = Node.get_by_id([id for id in range(from_id, to_id, -1)])
        for n_obj in n_objs:
            if n_obj:
                objs.append(('n-'+str(n_obj.key().id()), n_obj.name))
        return objs
    
    @staticmethod
    #@memcached('get_hot_node', 600)
    def get_hot_node():
        objs = []
        for obj in Node.all().order('-count').fetch(10):
            objs.append(('n-'+str(obj.key().id()), obj.name))
        return objs
    
    @staticmethod
    @memcached('get_recent_node', 300)
    def get_recent_node():
        k_obj = KeyStrValue.get_or_insert('rencent-view-node')
        if k_obj.value:
            objs = []
            n_objs = Node.get_by_id([int(id) for id in k_obj.value.split(',')])
            for n_obj in n_objs:
                if n_obj:
                    objs.append(('n-'+str(n_obj.key().id()), n_obj.name))
            return objs
        return None
    
    @staticmethod
    @memcached('get_page_topic', 300, lambda nodeid, from_id, to_id: "%s:%s"%(nodeid, str(from_id)))
    def get_page_topic(nodeid, from_id, to_id):
        return Topic.get_by_key_name(['%s-%d'%(nodeid, i) for i in range(from_id, to_id, -1)])

class Topic(db.Model):
    #keyname: 1-2
    title = db.StringProperty(indexed=False,default='')
    author = db.StringProperty(indexed=False,default='')
    add = db.IntegerProperty(indexed=False,default=0)
    edit = db.IntegerProperty(indexed=False,default=0)
    cnum = db.IntegerProperty(indexed=False,default=0)
    reply = db.StringProperty(indexed=False,default='')
    con = db.TextProperty(default='') #conten
    
    @CachedProperty
    def node(self):
        return Node.get_by_id(int(self.key().name().split('-')[0]))
    
class Comment(db.Model):
    #keyname: 1-2-3
    author = db.StringProperty(indexed=False,default='')
    add = db.IntegerProperty(indexed=False,default=0)
    con = db.TextProperty(default='') #conten
    
    @staticmethod
    @memcached('get_comments', 300, lambda t_key, from_id, to_id: "%s:%s"%(str(t_key), str(from_id)))
    def get_comments(t_key, from_id, to_id):
        return Comment.get_by_key_name(["%s-%d"%(t_key,i) for i in range(from_id, to_id+1)])
    
class KeyStrValue(db.Model):
    value = db.StringProperty(indexed=False,default='')
    
    @staticmethod
    def add_node_key(nodeid):
        k_obj = KeyStrValue.get_or_insert('rencent-view-node')
        if k_obj.value:
            t_list = k_obj.value.split(',')
            if nodeid not in t_list:
                t_list.insert(0, nodeid)
                k_obj.value = ','.join(t_list[:10])
                db.run_in_transaction(obj_runput,k_obj)
        else:
            k_obj.value = nodeid
            db.run_in_transaction(obj_runput,k_obj)
    
    @staticmethod
    @memcached('get_topic_objs', 300, lambda key: key)
    def get_topic_objs(key):
        k_obj = KeyStrValue.get_by_key_name(key)
        if k_obj and k_obj.value:
            objs = []
            t_objs = Topic.get_by_key_name(k_obj.value.split(',')[:RECENT_POST_NUM])
            for obj in t_objs:
                if obj:
                    objs.append(obj)
            return objs
        else:
            return []
    
    @staticmethod
    @memcached('get_topic_key_title', 300, lambda key: key)
    def get_topic_key_title(key):
        k_obj = KeyStrValue.get_by_key_name(key)
        if k_obj and k_obj.value:
            objs = []
            t_objs = Topic.get_by_key_name(k_obj.value.split(',')[:RECENT_COMMENT_NUM])
            for obj in t_objs:
                if obj:
                    objs.append(('t-'+obj.key().name(), obj.title))
            return objs
        else:
            return None

class Avatar(db.Model):
    #keyname:usernamem
    content = db.BlobProperty()

class Photo(db.Model):
    #keyname: filename
    content = db.BlobProperty()
