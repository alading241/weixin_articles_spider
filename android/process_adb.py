# -*- coding:utf-8 -*-
from bson.objectid import ObjectId
import redis
import datetime
import time
import sys
sys.path.append("../")  # 为了引入instance
from instance import mongo_instance  # weixindb
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def adb_entry(android_queue):
    # 每隔一分钟去队列检查下是否有任务在running 没有的话就搞一个变成runnning

    while True:
        t = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
        # TODO 这里貌似有点问题 但又不是逻辑问题 tasks
        tasks = android_queue.pickAll()
        if not tasks:
            print('- {} 没有任何任务，安卓adb啥事也不用干'.format(t))
        else:
            runnning_tasks = pick_running(tasks)
            if not runnning_tasks:
                print('- {} 即将添加任务至安卓运行队列'.format(t))
                # 如果没有任何进行中的任务
                # 1. 将第一个任务设为进行中 存入数据库
                # 2. 通知代理，你有活要干啦！ 并且删除他
                try:
                    print('- {} 即将开始安卓任务'.format(t))
                    set_task_running(tasks[0])
                    print('- {} 即将开始插入mongodb'.format(t))
                    set_task_in_mongo(str(tasks[0]['_id']))
                    print('- {} 即将开始插入redis'.format(t))
                    set_task_in_redis(
                        str(tasks[0]['_id']), str(tasks[0]['task_biz_enname']))
                    print('- {} 即将通知anyproxy'.format(t))
                    notify_http_proxy(str(tasks[0]['_id']))
                    print('- {} 即将开始做adb操作'.format(t))

                    # TODO adb操作

                except Exception as e:
                    print(' - 31行 这里出错了')
                    print(e)
            else:
                print('- {} 已经有运行中的任务了哦 _id是 {}'.format(t, str(runnning_tasks[0]['_id'])))

        time.sleep(20)


def pick_running(tasks):
    runnning_tasks = []
    for task in tasks:
        # 同一时间只能有一个running的
        if task['task_status'] == 'running':
            runnning_tasks.append(task)
            break
    return runnning_tasks


def set_task_running(task):
    task['task_status'] = 'running'

def set_task_in_mongo(taskid):
    task_obj_id = ObjectId(taskid)
    t = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
    mongo_instance.tasks.find_and_modify(
        query={'_id': task_obj_id}, update={'$set': {'task_status': 'runnning', 'task_updatetime': t}})

def set_task_in_redis(taskid, enname):
    # redis的key过期事件在获返回结果时是 key的值，所以在做相关任务时，可以把key名写成需要执行的函数名等等
    # 先清空
    for key in r.scan_iter("__running_taskid*"):
        r.delete(key)

    r.set('__running_taskid_{}_bizenname_{}'.format(
        taskid, enname), taskid, ex=60*10)

def notify_http_proxy(taskid):
    r.publish('there_is_a_adb', '__taskid_' + str(taskid))



