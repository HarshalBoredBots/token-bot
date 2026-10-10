from pymongo import MongoClient
from var import *

client = MongoClient(DB_URL)
db = client[DB_NAME]
col = db['users']

# FIX 9: Load users lazily at first access instead of blocking at import time.
# The original code ran a synchronous MongoDB query during module import,
# before the async event loop was running, blocking startup on slow connections.
_users_loaded = False
users_list = []

def _ensure_users_loaded():
    global _users_loaded
    if not _users_loaded:
        users_list.clear()
        for doc in col.find():
            users_list.append(doc['_id'])
        _users_loaded = True

async def add_user(ids):
    _ensure_users_loaded()
    if ids not in users_list:
        try:
            col.insert_one({'_id': ids})
        except Exception:
            pass
        users_list.append(ids)

async def del_user(ids):
    _ensure_users_loaded()
    if ids in users_list:
        try:
            col.delete_one({'_id': ids})
        except Exception:
            pass
        users_list.remove(ids)

def get_users_snapshot():
    """Return a stable copy of the user list safe for iteration."""
    _ensure_users_loaded()
    return list(users_list)


# TOKEN SYSTEM
tcol = db['token']

cf = tcol.find_one({'_id': 'token'})
if not cf:
    cf = {'_id': 'token'}
    tcol.insert_one(cf)

async def sync():
    tcol.replace_one({'_id': 'token'}, cf)


# PREMIUM USERS
prem = db['premium']

prem_dict = prem.find_one({'_id': 'premium'})
if not prem_dict:
    prem_dict = {'_id': 'premium'}
    prem.insert_one(prem_dict)

if 'PREMIUM' not in prem_dict:
    prem_dict['PREMIUM'] = {}

for key, value in prem_dict['PREMIUM'].items():
    value.update({'END': value['END'].astimezone(TIME_ZONE)})

async def prem_sync():
    prem.replace_one({'_id': 'premium'}, prem_dict)
