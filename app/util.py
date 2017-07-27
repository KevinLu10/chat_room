# encoding=utf8
import json
import time
from functools import wraps
from . import exception as ext
from cache import reg_cache
import traceback


def check_response(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        try:
            data = f(*args, **kwargs)
            return json.dumps(dict(code=0, data=data))
        except ext.CusError, e:
            return ext.get_return_str(e)
        except:
            print traceback.format_exc()
            return ext.get_return_str(ext.ServerError)

    return _wrapper


def data_to_json(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        args = list(args)
        param = args[1]
        try:
            param = json.loads(param)
        except:
            raise ext.JsonError
        args[1] = param
        return f(*args, **kwargs)

    return _wrapper


def check_reg(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        #TODO 使用sessionno来验证似乎不是很好，因为一旦连接断开，连接的sessionno是会被重用的，
        sessionno = args[0].transport.sessionno
        if not reg_cache.get(sessionno):
            raise ext.NoRegError
        return f(*args, **kwargs)

    return _wrapper


def args_get(args, key, default=None):
    """从request.args获取参数"""
    if key in args:
        return args[key][0]
    else:
        return default


def get_timestamp():
    """获取当前时间错"""
    return int(time.time())


def check_token(room_id, user_id, timestamp, client_token):
    """验证token是否正确"""
    if time.time() > timestamp + 3600:
        raise ext.RegTimeoutError
    if '%s%s%s' % (user_id, timestamp, room_id) != client_token:
        raise ext.RegTokenError
    return 1
