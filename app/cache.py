# -*- coding: utf-8 -*-
from . import redis_client

try:
    import ujson as json
except:
    from flask import json


class ListCache(object):
    def __init__(self, name, redis_cli=redis_client):
        self.name = name
        self.redis_cli = redis_cli

    def push(self, key, obj):
        self.redis_cli.lpush("%s:%s" % (self.name, key), json.dumps(obj))

    def pop(self, key):
        v = self.redis_cli.rpop("%s:%s" % (self.name, key))
        if v:
            v = json.loads(v)
        return v

    def expire(self, key, delta):
        self.redis_cli.expire("%s:%s" % (self.name, key), delta)

    def delete(self, key):
        real_key = "%s:%s" % (self.name, key)
        self.redis_cli.delete(real_key)

    def remove(self, key, obj):
        self.redis_cli.lrem("%s:%s" % (self.name, key), json.dumps(obj))

    def index(self, key, idx):
        return self.redis_cli.lindex("%s:%s" % (self.name, key), idx)

    def lrange(self, key, _min=0, _max=1):
        ret = self.redis_cli.lrange("%s:%s" % (self.name, key), _min, _max)
        _ret = map(lambda x: json.loads(x), ret)
        return _ret

    def lrange_all(self, key):
        ret = self.redis_cli.lrange("%s:%s" % (self.name, key), 0, -1)
        _ret = map(lambda x: json.loads(x), ret)
        return _ret

    def count(self, key):
        return self.redis_cli.llen("%s:%s" % (self.name, key))


class ObjCache(object):
    def __init__(self, prefix, redis_cli=redis_client):
        self.redis_cli = redis_cli
        self.prefix = prefix

    def get(self, key=''):
        raw_data = self.redis_cli.get('%s:%s' % (self.prefix, key))
        if raw_data is None:
            return None
        data = json.loads(raw_data)
        return data

    def set(self, key, obj):
        self.redis_cli.set('%s:%s' % (self.prefix, key), json.dumps(obj))

    def setex(self, key, obj, seconds):
        self.redis_cli.setex('%s:%s' % (self.prefix, key), json.dumps(obj), seconds)

    def delete(self, key):
        self.redis_cli.delete('%s:%s' % (self.prefix, key))

    def expire(self, key, seconds):
        self.redis_cli.expire('%s:%s' % (self.prefix, key), seconds)

    def expire_at(self, key, dt):
        self.redis_cli.expireat("%s:%s" % (self.prefix, key), dt)

    def incr(self, key):
        return self.redis_cli.incr('%s:%s' % (self.prefix, key))

    def decr(self, key):
        return self.redis_cli.decr('%s:%s' % (self.prefix, key))


online_cache = ListCache('online')  # 在线列表
room_online_cache = ListCache('room_online')  # 房间的在线列表
client_data_cache = ObjCache('client_data')  # 客户端数据
session_id_cache = ObjCache('session_id')  # session_no与user_id的映射
reg_cache = ObjCache('reg_cache')  # 标志sessionno是否已经注册
