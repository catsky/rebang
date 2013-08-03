# -*- coding: utf-8 -*-
import logging

from time import time
from hashlib import md5

import sae.kvdb

###
from common import BaseHandler, clear_cache_multi, decode_dict, encode_dict, memcached
from setting import *

###############
kv = sae.kvdb.KVClient()

###
class Count:
    
    @staticmethod
    def get_by_key(key):
        return kv.get(key)
    
    @staticmethod
    def key_incr(key):
        obj = kv.get(key)
        if obj:
            kv.set(key, str(int(obj)+1))
        else:
            kv.set(key, '1')
            
    @staticmethod
    @memcached('get_site_counts', 300)
    def get_site_counts():
        site_info = []
        
        member_num = kv.get('member_auto_increment')
        if member_num:
            if int(member_num)>1:
                site_info.append(('会员',int(member_num)-1))
        
        node_num = kv.get('node_auto_increment')
        if node_num:
            if int(node_num)>1:
                site_info.append(('主题',int(node_num)-1))
            
        topic_num = kv.get('all-topic-num')
        if topic_num:
            site_info.append(('帖子',topic_num))
        
        comment_num = kv.get('all-comment-num')
        if comment_num:
            site_info.append(('回复',comment_num))
        return site_info

class Member:
    @staticmethod
    def get_by_name(name):
        u_obj = kv.get('m-' + name)
        if u_obj:
            return decode_dict(u_obj)
        else:
            return None
    
    @staticmethod
    @memcached('cur_user', 600, lambda name, sr_code, flag=1: name)
    def check_loged_user(name, sr_code, flag=1):
        u_obj = kv.get('m-' + name)
        if u_obj:
            member_dict = decode_dict(u_obj)
            if int(member_dict['flag']) >= flag:
                code_list = [member_dict['code']]
                u_topic_time = kv.get('u_topic_time:'+name)
                if u_topic_time:
                    code_list.append(u_topic_time)
                u_comment_time = kv.get('u_comment_time:'+name)
                if u_comment_time:
                    code_list.append(u_comment_time)
                #code_md5 = md5(''.join(code_list)).hexdigest()
                if md5(''.join(code_list)).hexdigest() == sr_code:
                    return member_dict
                else:
                    return None
            else:
                return None
        else:
            return None
    
    @staticmethod
    def check_user_name(name):
        return kv.get('m-' + name)
    
    @staticmethod
    def add_user(name, pwmd5):
        udict = MEMBER_DICT.copy()
        #get use id
        cur_num = kv.get('member_auto_increment')
        if cur_num:
            member_id = cur_num
            udict['flag'] = 1
        else:
            member_id = 1
            udict['flag'] = 99
        
        udict['id'] = member_id
        udict['name'] = name
        udict['code'] = pwmd5
        udict['add'] = int(time())
        if kv.set('m-' + name, encode_dict(udict)):
            if kv.set('member_auto_increment', member_id+1):
                return udict['flag']
        return None
    
    @staticmethod
    def get_by_name_for_edit(name):
        if name:
            m_obj_str = kv.get('m-' + name)
            return  decode_dict(m_obj_str)
        else:
            return MEMBER_DICT.copy()
    
    @staticmethod
    def set_flag(name, flag):
        u_obj_str = kv.get('m-' + name)
        if u_obj_str:
            u_obj = decode_dict(u_obj_str)
            if u_obj['flag'] != flag:
                u_obj['flag'] = flag
                return kv.set('m-' + name, encode_dict(u_obj))
        return False
    
    @staticmethod
    def add_key_rencent_topic(name, topickey):
        rt_obj = kv.get('topic-'+name)
        if rt_obj:
            olist = rt_obj.split(',')
            if topickey not in olist:
                olist.insert(0, topickey)
                kv.set('topic-'+name, ','.join(olist[:MEMBER_RECENT_TOPIC]))
        else:
            kv.set('topic-'+name, topickey)
    
    @staticmethod
    def add_key_rencent_comment_topic(name, topickey):
        rt_obj = kv.get('comment-topic-'+name)
        if rt_obj:
            olist = rt_obj.split(',')
            if topickey not in olist:
                olist.insert(0, topickey)
                kv.set('comment-topic-'+name, ','.join(olist[:MEMBER_RECENT_TOPIC]))
        else:
            kv.set('comment-topic-'+name, topickey)
    
class Node:
    @staticmethod
    def add_node_key(node_key):
        keys = kv.get('recent_view_node')
        if keys:
            keys_list = keys.split(',')
            if node_key not in keys_list:
                keys_list.insert(0, node_key)
                kv.set('recent_view_node', ','.join(keys_list[:10]))
                clear_cache_multi(['recent_view_node'])
        else:
            kv.set('recent_view_node', node_key)
            clear_cache_multi(['recent_view_node'])
    
    @staticmethod
    @memcached('recent_view_node', 300)
    def get_recent_node():
        keys = kv.get('recent_view_node')
        if keys:
            objs = []
            for key in keys.split(','):
                value = kv.get(key)
                if value:
                    n_obj = decode_dict(value)
                    objs.append((key, n_obj['name']))
            return objs
        else:
            return None
    
    @staticmethod
    def get_max_node_id():
        cur_num = kv.get('node_auto_increment')
        if cur_num:
            id = str(cur_num)
        else:
            id = '1'
        return int(id)-1
    
    @staticmethod
    @memcached('newest_add_node', 600)
    def get_newest():
        cur_num = kv.get('node_auto_increment')
        if cur_num:
            id = str(cur_num)
        else:
            id = '1'
        from_id = int(id)-1
        to_id = from_id - 10
        if to_id <0:
            to_id = 0
        objs = []
        for x in range(from_id, to_id, -1):
            value = kv.get('n-'+str(x))
            if value:
                n_obj = decode_dict(value)
                objs.append(('n-'+str(x), n_obj['name']))
        return objs
    
    @staticmethod
    @memcached('get_hot_node', 3600)
    def get_hot_node():
        h_obj = kv.get('nodekey-topicnum')
        if h_obj:
            d = dict([x.split("\x1f")[0],int(x.split("\x1f")[1])] for x in h_obj.split("\x1e"))
            sorted_keys = sorted(d, key=d.__getitem__, reverse=True)[:10]
            objs = []
            for key in sorted_keys:
                value = kv.get(key)
                if value:
                    n_obj = decode_dict(value)
                    objs.append((key, n_obj['name']))
            return objs
        else:
            return None
    
    @staticmethod
    def get_by_key(key):
        n_obj_str = kv.get(key)
        if n_obj_str:
            return decode_dict(n_obj_str)
        else:
            return None
    
    @staticmethod
    def get_by_id_for_edit(id):
        if id:
            n_obj_str = kv.get('n-' + id)
            return  decode_dict(n_obj_str)
        else:
            return NODE_DICT.copy()
    
    @staticmethod
    def set_node(id, name, imgurl, about):
        if id:
            n_obj_str = kv.get('n-' + id)
            ndict = decode_dict(n_obj_str)
            
            ndict['id'] = id
            ndict['name'] = name
            ndict['imgurl'] = imgurl
            ndict['about'] = about
                
            if kv.set('n-' + id, encode_dict(ndict)):
                clear_cache_multi(['newest_add_node'])
                return id #True
            else:
                return False
        else:
            ndict = NODE_DICT.copy()
            #get node id
            cur_num = kv.get('node_auto_increment')
            if cur_num:
                id = str(cur_num)
            else:
                id = '1'
            ndict['id'] = id
            ndict['name'] = name
            ndict['imgurl'] = imgurl
            ndict['about'] = about
            
            if kv.set('n-' + id, encode_dict(ndict)):
                if kv.set('node_auto_increment', int(id)+1):
                    clear_cache_multi(['newest_add_node'])
                    return id #True
            return False
    
    @staticmethod
    @memcached('get_page_topic', 300, lambda node_id, from_id, to_id: "%s:%s"%(str(node_id), str(from_id)))
    def get_page_topic(node_id, from_id, to_id):
        objs = []
        for i in range(from_id, to_id, -1):
            t_key = 't-%s-%d' % (node_id, i)
            #logging.error(t_key)
            value = kv.get(t_key)
            if value:
                objs.append((t_key, decode_dict(value)))
        return objs

class Topic:
    @staticmethod
    def get_by_key(key):
        t_obj_str = kv.get(key)
        if t_obj_str:
            return decode_dict(t_obj_str)
        else:
            return None    
    
    @staticmethod
    def add(topic_id, topic_dict):
        topic_key = 't-%s-%s' % (topic_dict['nodeid'], str(topic_id))
        if kv.set(topic_key, encode_dict(topic_dict)):
            return True
        else:
            return False
    
class Comment:
    
    @staticmethod
    def get_by_key(key):
        t_obj_str = kv.get(key)
        if t_obj_str:
            return decode_dict(t_obj_str)
        else:
            return None
    
    @staticmethod
    @memcached('get_comments', 300, lambda t_key, from_id, to_id: "%s:%s"%(str(t_key), str(from_id)))
    def get_comments(t_key, from_id, to_id):
        objs = []
        for i in range(from_id, to_id+1):
            value = kv.get('%s-%d'%(t_key, i))
            if value:
                objs.append(decode_dict(value))
        return objs
        
class Commomkvdb:
    @staticmethod
    def get_by_key(key):
        t_obj_str = kv.get(key)
        if t_obj_str:
            return decode_dict(t_obj_str)
        else:
            return None
    
    @staticmethod
    def save(key, my_dict):
        return kv.set(key, encode_dict(my_dict))
    
    @staticmethod
    def add_key_rencent_topic(key, topickey):
        rt_obj = kv.get(key)
        if rt_obj:
            olist = rt_obj.split(',')
            if topickey in olist:
                olist.remove(topickey)
            olist.insert(0, topickey)
            kv.set(key, ','.join(olist[:RECENT_POST_NUM]))
        else:
            kv.set(key, topickey)
    
    @staticmethod
    @memcached('get_topic_by_keys', 300, lambda keys_list_key: keys_list_key)
    def get_topic_by_keys(keys_list_key):
        obj = kv.get(keys_list_key)
        if obj:
            objs = []
            for key in obj.split(','):
                value = kv.get(key)
                if value:
                    objs.append((key, decode_dict(value)))
            return objs
        else:
            return []
    
    @staticmethod
    def get_notifications(username, keys_list_str):
        if keys_list_str:
            objs = []
            for key in keys_list_str.split(','):
                value = kv.get(key)
                if value:
                    objs.append((key, decode_dict(value)))
            return objs
        else:
            return []
    
    @staticmethod
    @memcached('get_comment_topic_by_keys', 300, lambda keys_list_key: keys_list_key)
    def get_comment_topic_by_keys(keys_list_key):
        obj = kv.get(keys_list_key)
        if obj:
            objs = []
            for key in obj.split(',')[:10]:
                value = kv.get(key)
                if value:
                    objs.append((key, decode_dict(value)['title']))
            return objs
        else:
            return []
    