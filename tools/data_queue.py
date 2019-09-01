import redis
import json
from bson.json_util import object_hook
# 任务的队列
class Normal_queue():
    """
    创建一个队列 FIFO 先进先出
    """

    def __init__(self, q_name):
        """
        :param q_name:创建一个队列
        """
        self.q_name = q_name
        self.queue = list()

    def isEmpty(self):
        """
        判断队列是否为空
        :return:
        """
        return len(self.queue) == 0

    def pickAll(self):
        return self.queue

    def addItem(self, obj):
        """
        将指定元素加入队列的尾部
        :param obj:
        :return: self.queue
        """
        self.queue.append(obj)
        return self.queue

    def pickItem(self):
        """
        查看队首的对象，但不移除
        :return:
        """
        if not self.isEmpty():
            return self.queue[0]
        return None

    def popItem(self):
        """
        移除队首对象，并返回该对象的值
        :return:
        """
        if not self.isEmpty():
            return self.queue.pop(0)
        return None


    def empty(self):
        """
        清空队列
        :return: 被清空的队列
        """
        self.queue = list()
        return self.queue


# Redis的队列
class Redis_queue():
    """
    创建一个队列 FIFO 先进先出
    """

    def __init__(self, q_name):
        """
        :param q_name:创建一个队列
        """
        self.q_name = 'redis_queue__'+q_name
        self.redis = redis.Redis(
            host='localhost', port=6379, decode_responses=True)

    def isEmpty(self):
        """
        判断队列是否为空
        :return:
        """
        return len(self.pickAll()) == 0

    def pickAll(self):
        """
        :return:返回插入的数据
        """
        rq_b_data_list = self.redis.lrange(self.q_name, 0, -1)
        rq_j_data_list = []
        for rq_b_data in rq_b_data_list:
            try:
                rq_j_data = json.loads(
                    rq_b_data, object_hook=object_hook)
            except:
                rq_j_data = rq_b_data.decode('utf8')
            rq_j_data_list.append(rq_j_data)
        return rq_j_data_list

    def addItem(self, data):
        """
        :param data:
        :return:1表示插入成功 1表示对象已经存在
        """
        rq = self.pickAll()
        if data not in rq:
            self.redis.lpush(self.q_name, data)
            return 1
        return 0

    def pickItem(self):
        """
        查看队首的对象，但不移除
        :return:
        """
        rq_b_data_list = self.redis.lrange(self.q_name, 0, -1)
        rq_j_data = None
        if len(rq_b_data_list) > 0:
            try:
                rq_j_data = json.loads(rq_b_data_list[-1], object_hook=object_hook)
            except:
                rq_j_data = rq_b_data_list[-1].decode('utf8')

        return rq_j_data

    def popItem(self):
        """
        :return:[]表示队列已经空了
        """
        data = self.redis.rpop(self.q_name)
        try:
            rq_j_data = json.loads(data, object_hook=object_hook)
        except:
            if data:
                rq_j_data = data.decode('utf8')
            else:
                rq_j_data = []
        return rq_j_data

    def deleteQueue(self):
        """
        删除队列
        """
        return self.redis.delete(self.q_name)

