import redis
from classes.pymongo_utils import PyMongoUtils

class redisMani:
    def insertIntoRedisAndMongo(word, data, uri):
        pymongo_utils = PyMongoUtils(uri)
        
        r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_key = f"word:{word}"
        r.hmset(redis_key, data)
        
        print(f"\nStored word '{word}' in Redis.")
        
        pymongo_utils.insertIntoMongoDB(data)

    def updateIntoRedisAndMongo(word, data, uri):
        pymongo_utils = PyMongoUtils(uri)
        
        r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_key = f"word:{word}"
        r.hmset(redis_key, data)
        
        print(f"\nStored word '{word}' in Redis.")
        
        pymongo_utils.updateIntoMongoDB(data)

    
    def flushRedis(self):
        r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        r.flushdb()
        print("Redis database has been flushed.")     

    
    def getCountRedis(word):
        r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_key = f"word:{word}"
        data = r.hgetall(redis_key)
        
        count = data.get('count', 0)
        return count

    def redisGetAllData(self):
        r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        keys = r.keys('word:*')  
        data = []
    
        for key in keys:
            value = r.hgetall(key)
            row = {"key": key}
            row.update(value)
            data.append(row)

        return data