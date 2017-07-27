# encoding=utf8
import json

def get_return_str(ext):
    """获取返回给客户端的字符串"""
    return json.dumps(dict(code=ext.code, message=ext.message))
class CusError(Exception):
    code = 0
    message = ''




class ServerError(CusError):
    """服务端内部错误"""
    code = 1000
    message = u'服务端内部错误'


class RegTimeoutError(CusError):
    """注册时间戳超时"""
    code = 10000
    message = u'注册时间戳超时'


class RegTokenError(CusError):
    """注册token错误"""
    code = 10001
    message = u'注册token错误'


class JsonError(CusError):
    """请求的数据不是json格式"""
    code = 10002
    message = u'请求的数据不是json格式'


class NoRegError(CusError):
    """连接没有注册"""
    code = 10003
    message = u'连接没有注册'


if __name__ == '__main__':
    pass
