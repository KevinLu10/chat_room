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


def doConnectionMade(conn):
    pass
    # '''当有客户端连接时，调用该方法'''
    # str1 = 'welcome\r\n'
    # GlobalObject().netfactory.pushObject(10001, str1, [conn.transport.sessionno])  # 向登录的客户端发送欢迎信息
    # str2 = '%d is login\r\n' % conn.transport.sessionno
    # lis = GlobalObject().netfactory.connmanager._connections.keys()  # 获取所有连接的客户端的session_no
    # lis.remove(conn.transport.sessionno)  # 移除当前登录的客户端的session_no
    # GlobalObject().netfactory.pushObject(10001, str2, lis)  # 向其他客户端发送上线消息


def lost_client(sessionno):
    """断开客户端连接的处理逻辑"""
    reg_cache.delete(sessionno)
    data = client_data_cache.get(sessionno)
    client_data_cache.delete(sessionno)
    online_cache.remove('online', sessionno)

    if data:
        user_id = data.get('user_id')
        if user_id:
            session_id_cache.delete(user_id)
            room_id = data.get('room_id')
            if room_id:
                room_online_cache.remove(room_id, sessionno)


def doConnectionLost(conn):
    '''当客户端断开连接时，调用该方法'''
    sessionno = conn.transport.sessionno
    lost_client(sessionno)
    #群发房间人数


# 重写客户端连接和断开的方法
GlobalObject().netfactory.doConnectionMade = doConnectionMade
GlobalObject().netfactory.doConnectionLost = doConnectionLost


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
    # 通知房间的所有客户端，房间人数改变
    sessionnos = list(set(room_online_cache.lrange_all(room_id)))
    if sessionno in sessionnos:
        sessionnos.remove(sessionno)
    online_cnt = len(sessionnos)
    GlobalObject().netfactory.pushObject(1004, json.dumps(dict(online_cnt=online_cnt)), sessionnos)
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
def hb_1003(_conn, data):
    '''心跳'''
    sessionno = _conn.transport.sessionno
    data = client_data_cache.get(sessionno)
    data['last_hb'] = util.get_timestamp()
    client_data_cache.set(sessionno, data)
    return True


@webserviceHandle('dispatch')
class dispatch(resource.Resource):
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
        room_id = util.args_get(request.args, 'room_id', 0)
        user_ids = util.args_get(request.args, 'user_id', '').split(',')
        msg = util.args_get(request.args, 'msg', '')
        if not msg:
            return True
        list_ = self.get_dispatch_list(room_id, user_ids)
        print list_
        if list_:
            GlobalObject().netfactory.pushObject(1005, msg, list_)
        mongo_client['msg_%s' % room_id].insert({'timestamp': util.get_timestamp(), 'msg': msg})
        return True


@webserviceHandle('room/close')
class close_room(resource.Resource):
    '''销毁房间'''

    @util.check_response
    def render(self, request):
        room_id = util.args_get(request.args, 'room_id', 0)
        mongo_client['msg_%s' % room_id].remove()
        sessionnos = room_online_cache.lrange_all(room_id)
        for sessionno in sessionnos:
            GlobalObject().netfactory.loseConnection(sessionno)
            lost_client(sessionno)
        room_online_cache.delete(room_id)
        return True
