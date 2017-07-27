# coding:utf8

import socket
import struct
from thread import start_new
import time
import json

COMMAND_ID_REG = 1001
COMMAND_ID_GET_OFFLINE_MSG = 1002
COMMAND_ID_HB = 1003


def send_data(sendstr, commandId):
    '''定义协议头
    '''
    HEAD_0 = chr(0)
    HEAD_1 = chr(0)
    HEAD_2 = chr(0)
    HEAD_3 = chr(0)
    ProtoVersion = chr(0)
    ServerVersion = 0
    sendstr = sendstr
    data = struct.pack('!sssss3I', HEAD_0, HEAD_1, HEAD_2, \
                       HEAD_3, ProtoVersion, ServerVersion, \
                       len(sendstr) + 4, commandId)
    senddata = data + sendstr
    return senddata


def rec_one_pk(conn):
    """接收一个数据包"""
    data = conn.recv(17)
    head = struct.unpack('!sssss3I', data)
    lenght = head[6]
    cmd_id = head[7]
    pk = conn.recv(lenght)
    return cmd_id, pk


def send_hb(conn):
    '''发送消息
    '''
    while 1:
        data = '{}'
        conn.sendall(send_data(data, COMMAND_ID_HB))  # 向服务器发送消息
        time.sleep(10)
        print 'HB'


def rec_msg(conn):
    '''接收消息
    '''
    while 1:
        cmd_id, pk = rec_one_pk(conn)
        print 'REC PK', cmd_id, pk


def send_rec_pk(conn, data, cmd_id):
    """发送一个数据包，并接收一个"""
    conn.sendall(send_data(json.dumps(data), cmd_id))
    cmd_id, pk = rec_one_pk(conn)
    pk = json.loads(pk)
    return cmd_id, pk


def reg(conn, room_id, user_id):
    """注册"""
    timestamp = time.time()
    token = '%s%s%s' % (user_id, timestamp, room_id)
    data = dict(timestamp=timestamp, room_id=room_id, user_id=user_id, token=token)
    cmd_id, pk = send_rec_pk(conn, data, COMMAND_ID_REG)
    if pk['code'] != 0:
        print "REG FAIL %s" % pk
        return 0
    print 'REG SUC'
    return 1


def get_offline_msg(conn, timestamp):
    '''获取离线消息'''
    print 1
    data = dict(timestamp=timestamp)
    cmd_id, pk = send_rec_pk(conn, data, COMMAND_ID_GET_OFFLINE_MSG)
    print pk
    print 'OFFLINE MSG :'
    for msg in pk['data']['msg']:
        print msg
    print 'OFFLINE MSG -'


class ChatServer:
    def __init__(self, port, room_id, user_id, offline_timestamp):
        self.port = port
        self.room_id = room_id
        self.user_id = user_id
        self.offline_timestamp = offline_timestamp
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(('127.0.0.1', port))

    def run(self):
        if reg(self.conn, room_id, user_id):
            get_offline_msg(self.conn, offline_timestamp)
            start_new(send_hb, (self.conn,))
            start_new(rec_msg, (self.conn,))


if __name__ == '__main__':
    import sys

    room_id = sys.argv[1]
    user_id = sys.argv[2]
    offline_timestamp = sys.argv[3]
    print 'room_id:%s user_id:%s offline_timestamp:%s' % (room_id, user_id, offline_timestamp)
    myServer = ChatServer(1001, room_id, user_id, offline_timestamp).run()
    while 1:
        pass
