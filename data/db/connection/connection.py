# import aiomysql
# import redis.asyncio as redis

# _redis = None
# _pool = None


# async def init_redis():
#     global _redis
#     if _redis is None:
#         _redis = await redis.Redis.from_url(
            
#             "host": os.getenv("REDIS_HOST"),
#             "user": os.getenv("REDIS_USER"),
#             "password": os.getenv("REDIS_PASSWORD"),
#             "port": int(os.getenv("REDIS_PORT", 3306))
#             encoding="utf-8",
#             decode_responses=True,
#             max_connections=32
#         )
#         pong = await _redis.ping()
#         if pong:
#             print("✅ Redis ishlamoqda!")
#         else:
#             print("❌ Redis javob bermadi!")

# # Pooldan get qilish misoli
# async def get_redis():
#     global _redis
#     if _redis is None:
#         await init_redis()
#     return _redis


# async def init_db_pool():
#     global _pool
#     if _pool is None:
#         _pool = await aiomysql.create_pool(

#             "host": os.getenv("MYSQL_HOST"),
#             "user": os.getenv("MYSQL_USER"),
#             "password": os.getenv("MYSQL_PASSWORD"),
#             "database": os.getenv("MYSQL_DATABASE"),
#             "port": int(os.getenv("MYSQL_PORT", 3306))


#             # host="localhost",
#             # user="root",
#             # password="Aa20050309@",
#             # db="avto_message",
#             # port=3306,
#             # minsize=1,
#             # maxsize=32,
#             # autocommit=True
#         )


# async def get_pool():
#     if not _pool is None:
#         return _pool
    

import os
import redis.asyncio as redis
import aiomysql

_redis = None
_pool = None


async def init_redis():
    global _redis
    if _redis is None:
        redis_url = f"redis://{os.getenv('REDIS_USER')}:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT', 6379)}/0"

        _redis = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=32
        )
        pong = await _redis.ping()
        if pong:
            print("✅ Redis ishlamoqda!")
        else:
            print("❌ Redis javob bermadi!")


async def get_redis():
    global _redis
    if _redis is None:
        await init_redis()
    return _redis


async def init_db_pool():
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            db=os.getenv("MYSQL_DATABASE"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            minsize=1,
            maxsize=32,
            autocommit=True
        )


async def get_pool():
    global _pool
    if _pool is None:
        await init_db_pool()
    return _pool
