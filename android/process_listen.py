from instance import mongo_instance  # weixindb
import redis
import datetime
import re
from bson.objectid import ObjectId
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def listen_task_entry():
    suber = r.pubsub()
    suber.subscribe('__keyevent@0__:expired')
    for item in suber.listen():
        if item['type'] == 'message':
            # running_task_
            endfix = re.split('__running_taskid_', item['data'])[1]

            taskid = endfix.split('_bizenname_', endfix)[0]
            # biz_enname = endfix.split('_bizenname_', endfix)[1]

            t = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
            print(' {} 时间到了任务过期: {} '.format(t, taskid))
            # ANCHOR 设置task状态为过时
            set_task_in_mongodb(ObjectId(taskid))


def set_task_in_mongodb(task_obj_id):
    t = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
    mongo_instance.tasks.find_and_modify(
        query={'_id': task_obj_id}, update={'$set': {'task_status': 'end_timeout', 'task_updatetime': t}})


