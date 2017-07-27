import redis
import config
import pymongo
redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD)

mongo_client = pymongo.MongoClient(host=config.MONGO_HOST, port=config.MONGO_PORT)[config.MONGO_DB]