# coding:utf8

from firefly.server.globalobject import netserviceHandle
from firefly.server.globalobject import GlobalObject
from datetime import *


def doConnectionMade(conn):
    '''当有客户端连接时，调用该方法'''
    str1 = 'welcome\r\n'
    GlobalObject().netfactory.pushObject(10001, str1, [conn.transport.sessionno])  # 向登录的客户端发送欢迎信息
    str2 = '%d is login\r\n' % conn.transport.sessionno
    lis = GlobalObject().netfactory.connmanager._connections.keys()  # 获取所有连接的客户端的session_no
    lis.remove(conn.transport.sessionno)  # 移除当前登录的客户端的session_no
    GlobalObject().netfactory.pushObject(10001, str2, lis)  # 向其他客户端发送上线消息


def doConnectionLost(conn):
    '''当客户端断开连接时，调用该方法'''
    str2 = '%d is logout\r\n' % conn.transport.sessionno
    lis = GlobalObject().netfactory.connmanager._connections.keys()  # 获取所有在线的客户端的session_no
    lis.remove(conn.transport.sessionno)  # 移除当前登录的客户端的session_no
    GlobalObject().netfactory.pushObject(10001, str2, lis)  # 向其他客户端发送下线消息

#重写客户端连接和断开的方法
GlobalObject().netfactory.doConnectionMade = doConnectionMade
GlobalObject().netfactory.doConnectionLost = doConnectionLost


@netserviceHandle
def speak_10001(_conn, data):
    '''发消息接口，定义客户端访接口，命令码是10001'''
    date = datetime.now()
    str1 = date.strftime("%Y-%m-%d %H:%M:%S") + ' (' + str(_conn.transport.sessionno) + '):\r\n' + data  # 拼装字符串
    lis = GlobalObject().netfactory.connmanager._connections.keys()  # 获取所有在线的客户端的session_no
    lis.remove(_conn.transport.sessionno)  # 移除当前登录的客户端的session_no
    GlobalObject().netfactory.pushObject(10001, str1, lis)  # 向其他客户端发送发言消息
