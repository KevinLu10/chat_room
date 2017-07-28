# coding:utf8
import json
import redis
from firefly.server.globalobject import netserviceHandle, webserviceHandle
from firefly.server.globalobject import GlobalObject
# from datetime import *
import time
from cache import online_cache, room_online_cache, client_data_cache, session_id_cache, reg_cache
from twisted.web import resource
from . import mongo_client
from . import config
from . import util
from . import exception as ext


def lost_client(sessionno, is_push_online_cnt=0):
    """断开客户端连接的处理逻辑"""
    reg_cache.delete(sessionno)
    data = client_data_cache.get(sessionno) or {}
    client_data_cache.delete(sessionno)
    online_cache.remove('online', sessionno)

    if data:
        user_id = data.get('user_id')
        if user_id:
            session_id_cache.delete(user_id)
            room_id = data.get('room_id')
            if room_id:
                room_online_cache.remove(room_id, sessionno)
                if is_push_online_cnt:
                    push_oinline_cnt(room_id, sessionno)
    return data


def doConnectionLost(conn):
    '''当客户端断开连接时，调用该方法'''
    sessionno = conn.transport.sessionno
    lost_client(sessionno, is_push_online_cnt=1)


# 重写客户端连接和断开的方法
# GlobalObject().netfactory.doConnectionMade = doConnectionMade
GlobalObject().netfactory.doConnectionLost = doConnectionLost


def push_oinline_cnt(room_id, exclude_sessionno):
    # 通知房间的所有客户端，房间人数改变
    sessionnos = list(set(room_online_cache.lrange_all(room_id)))
    online_cnt = len(sessionnos)
    if exclude_sessionno in sessionnos:
        sessionnos.remove(exclude_sessionno)
    GlobalObject().netfactory.pushObject(1004, json.dumps(dict(online_cnt=online_cnt)), sessionnos)
    return online_cnt


@netserviceHandle
@util.check_response
@util.data_to_json
def reg_1001(_conn, param):
    '''注册'''
    user_id = param.get('user_id', 0)
    room_id = param.get('room_id', 0)
    timestamp = param.get('timestamp', 0)
    token = param.get('token', '')
    util.check_token(room_id, user_id, timestamp, token)
    sessionno = _conn.transport.sessionno
    if not reg_cache.get(sessionno):
        online_cache.push('online', sessionno)
        room_online_cache.push(room_id, sessionno)
        data = dict(user_id=user_id, room_id=room_id, join_time=util.get_timestamp(), sessionno=sessionno,
                    last_hb=util.get_timestamp())
        client_data_cache.set(sessionno, data)
        session_id_cache.set(user_id, sessionno)
        reg_cache.set(sessionno, '1')
    online_cnt = push_oinline_cnt(room_id, sessionno)
    return dict(online_cnt=online_cnt)


@netserviceHandle
@util.check_response
@util.data_to_json
@util.check_reg
def get_offline_msg_1002(_conn, param):
    '''获取历史消息'''
    timestamp = int(param.get('timestamp', 0))
    sessionno = _conn.transport.sessionno
    data = client_data_cache.get(sessionno)
    room_id = data['room_id']
    if timestamp == 0:
        return dict(msg=[])
    msg = list(mongo_client['msg_%s' % room_id].find({'timestamp': {'$gt': timestamp}}
                                                     ).sort('timestamp').limit(config.MAX_OFFLINE_MSG_CNT))
    msg = [m['msg'] for m in msg]
    return dict(msg=msg)


@netserviceHandle
@util.check_response
@util.data_to_json
@util.check_reg
def hb_1003(_conn, param):
    '''心跳'''
    sessionno = _conn.transport.sessionno
    data = client_data_cache.get(sessionno)
    data['last_hb'] = util.get_timestamp()
    client_data_cache.set(sessionno, data)
    return True


@netserviceHandle
@util.check_response
@util.data_to_json
@util.check_reg
def send_msg_1006(_conn, param):
    '''发送消息'''
    sessionno = _conn.transport.sessionno
    client_data = client_data_cache.get(sessionno)
    room_id = client_data['room_id']
    sessionnos = room_online_cache.lrange_all(room_id)
    if sessionno in sessionnos:
        sessionnos.remove(sessionno)
    GlobalObject().netfactory.pushObject(1006, json.dumps(param), sessionnos)
    return True


@webserviceHandle('dispatch')
class Dispatch(resource.Resource):
    '''分发消息'''

    def get_dispatch_list(self, room_id, user_ids):
        list_ = []
        if user_ids:
            for user_id in user_ids:
                sessionno = session_id_cache.get(user_id)
                data = client_data_cache.get(sessionno)
                if data and data.get('room_id') == room_id:
                    list_.append(sessionno)
        else:
            list_ = room_online_cache.lrange_all(room_id)
        return list(set(list_))

    @util.check_response
    def render(self, request):
        room_id = util.args_get(request.args, 'room_id')
        user_id = util.args_get(request.args, 'user_id')
        msg = util.args_get(request.args, 'msg')
        if room_id is None:
            raise ext.ParamError('invalid room_id')
        if user_id is None:
            raise ext.ParamError('invalid user_id')
        if msg is None:
            raise ext.ParamError('invalid msg')
        user_ids = user_id.split(',')

        list_ = self.get_dispatch_list(room_id, user_ids)
        if list_:
            GlobalObject().netfactory.pushObject(1005, msg, list_)
        mongo_client['msg_%s' % room_id].insert({'timestamp': util.get_timestamp(), 'msg': msg})
        return True


@webserviceHandle('room/close')
class CloseRoom(resource.Resource):
    '''销毁房间'''

    @util.check_response
    def render(self, request):
        room_id = util.args_get(request.args, 'room_id')
        if room_id is None:
            raise ext.ParamError('invalid room_id')

        mongo_client['msg_%s' % room_id].remove()
        sessionnos = room_online_cache.lrange_all(room_id)
        for sessionno in sessionnos:
            GlobalObject().netfactory.loseConnection(sessionno)
            lost_client(sessionno)
        room_online_cache.delete(room_id)
        return True


@webserviceHandle('room/kick')
class KickUser(resource.Resource):
    '''踢人'''

    @util.check_response
    def render(self, request):
        user_id = util.args_get(request.args, 'user_id')
        if user_id is None:
            raise ext.ParamError('invalid user_id')
        sessionno = session_id_cache.get(user_id)
        if sessionno is not None:
            GlobalObject().netfactory.loseConnection(sessionno)
            lost_client(sessionno)
        return True
