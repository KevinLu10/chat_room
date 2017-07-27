# 聊天室服务器
本项目是基于firefly和twisted实现的一个聊天服务器。具有功能：
* 群发消息
* 对指定N个用户发送消息
* 离线消息
* 在线人数更新
* 主动关闭房间

## 一、项目的使用

本项目适合用于产品中大多数业务都是HTTP请求，只有少部分业务需要用到TCP连接的产品。

聊天室中发言，送礼等请求，一般会涉及很多额外的业务，例如扣费，是否有发言权限等。所以建议这些请求，可以先发HTTP请求到产品原有的WEB服务器，服务器处理完业务逻辑后，通过本项目的HTTP API来发消息到聊天室。

这个也是本项目没有实现客户端直接发socket消息到聊天室服务器的接口的原因。


## 二、部署
### 1. 安装firefly
    pip install firefly
### 2. 安装Redis
### 3. 安装Mongodb
### 4. 修改app/config.py里面的Redis配置和Mongodb配置
### 5. 运行服务器
    python startmaster.py

## 三、运行
### 1. 客户端
运行客户端：

    python tool/client.py 1000 20000 1501147683
其中：  
1000是客户端进入的房间的ID  

20000是客户端的用户的ID  

1501147683是需要获取的离线消息的最小时间戳  

### 2. 群发消息
发送消息给房间里面的所有用户
发送消息`hello`到房间1000

    curl 'http://127.0.0.1:1002/dispatch?room_id=1000&msg=hello'

### 3. 对多用户发送消息
发送消息`hello`到房间10000里面的用户20000和用户20001

    curl 'http://127.0.0.1:1002/dispatch?room_id=10000&msg=hello&user_id=20000,20001'

### 4. 关闭房间
关闭房间后，会清除历史消息，并断开房间里面的客户端的连接

    curl 'http://127.0.0.1:1002/room/close?room_id=10000'


## 四、TODO
1. 踢人的HTTP接口
2. 压测
