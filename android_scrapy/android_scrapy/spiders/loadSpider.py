import datetime
import scrapy
import re
from ..spider_config import FakeLoadParams, NORMAL_URLS
from bson.objectid import ObjectId
from instance import mongo_instance, redis_instance
from http.cookies import SimpleCookie
from w3lib.url import add_or_replace_parameter
from w3lib.url import url_query_parameter
from ..load_list_parse import list_parse, list_into_dbdata


class LoadSpider(scrapy.Spider):
    name = 'LoadSpider'
    allowed_domains = ['mp.weixin.qq.com']
    custom_settings = {
        # midlewares
        'ITEM_PIPELINES': {},
        'SPIDER_MIDDLEWARES': {
            # 'android_scrapy.loadmiddlewares.LoadSpiderMiddleware': 543
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddleware.httpproxy.HttpProxyMiddleware': None,
            'android_scrapy.proxymiddleware.ProxyMiddleware': 543,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None
        },
        # 设置请求间隔
        "DOWNLOAD_DELAY": round(5, 10),
        "COOKIES_ENABLED": True,
    }


    def start_requests(self):

        httpid = redis_instance.get('__running_http_')
        redis_instance.delete('__running_http_')
        print('httpid %s' % httpid)
        http = mongo_instance.https.find_one(filter={'_id': ObjectId(httpid)})

        task_obj_id = http['taskid']
        print('taskid %s' % str(task_obj_id))
        task = mongo_instance.tasks.find_one(filter={'_id': task_obj_id})
        print('- task finded')
        print(task)
        self.http = http
        self.task = task


        cookie_str = http['actionhome']['REQUEST_HEADERS']['Cookie'].replace(
            ' ', '')
        cookie_arr = cookie_str.split(';')
        # NOTE 我曹！
        cookies = {item.split('=', 1)[0]: item.split('=', 1)[1]
                   for item in cookie_arr}
        print('- cookies')
        print(cookies)

        FakeLoadParams.cookies['pass_ticket'] = http['pass_ticket']
        FakeLoadParams.cookies['wap_sid2'] = cookies['wap_sid2']
        FakeLoadParams.cookies['wxuin'] = cookies['wxuin']
        FakeLoadParams.cookies['version'] = cookies['version']

        FakeLoadParams.params['__biz'] = http['biz']
        FakeLoadParams.params['pass_ticket'] = http['pass_ticket']
        FakeLoadParams.params['appmsg_token'] = http['appmsg_token']

        url = NORMAL_URLS.load
        arr = []
        for key, val in FakeLoadParams.params.items():
            # print(val)
            arr.append(key + '=' + val)
        queryString = '?' + '&'.join(arr)
        print(queryString)
        print('- FakeLoadParams cookies')
        print(FakeLoadParams.cookies)
        self.crawled_times = 1

        if 'running_in_http' in self.task['task_status']:
            yield scrapy.Request(url=url+queryString, headers=FakeLoadParams.headers, cookies=FakeLoadParams.cookies, method='GET')
        else:
            return

    def parse(self, response):
        t = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
        print(' - in next_request: {} '.format(t))
        print(response.url)
        print(response.body.decode())

        """
        可以继续爬取的条件
        new: 转换后的list中没有出现start_article中的list
        按量 count <= crawl_count
        all:
        """

        switches = {
            'new': self.run_crawl_new,
            'count': self.run_crawl_count,
            'all': self.run_crawl_all,
        }
        method = switches.get(self.task['task_mode'])
        return method(response)

    def run_crawl_new(self, response):
        print(' --- run_crawl_new --- ')
        t = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
        next_offset = int(url_query_parameter(response.url, 'offset')) + 10
        list_parse_res = list_parse(eval(response.body.decode()))
        list_db_data = list_into_dbdata(
            list_parse_res, self.task['task_biz_enname'], self.task['task_biz_chname'], self.task['_id'])

        # 到头了或者出错了
        if not list_db_data:
            self.task['task_status'] = 'end_success'
            print('要出去了')
        else:
            load_obj_id = self.task['task_start_loadid']
            print(load_obj_id)
            stop_idx = None

            # 不是公众号第一次的话，就要找到一个位置停下
            if load_obj_id == None:
                if self.crawled_times == self.task['task_crawl_min'] / 10:
                    res = mongo_instance.loads.insert_many(list_db_data)
                    self.task['task_start_loadid'] = res.inserted_ids[0]
                    self.task['task_status'] = 'end_success'
                    print('要出去了')
                else:
                    res = mongo_instance.loads.insert_many(list_db_data)
                    if self.crawled_times == 1:
                        self.task['task_start_loadid'] = res.inserted_ids[0]
                    self.crawled_times += 1
                    print('还有请求呢别着急出去')
            else:
                # 判断这次的list里面有没有出现上次一样的title
                load = mongo_instance.loads.find_one(
                    filter={"_id": load_obj_id})
                title = load['title']
                print(title)
                for idx, item in enumerate(list_db_data):
                    if item['is_multi_app_msg_item_list'] == 'NO' and title == item['title']:
                        stop_idx = idx
                        print('找到了:  stop_idx {}'.format(idx))
                        break
                    else:
                        pass

                if stop_idx == None:
                    res = mongo_instance.loads.insert_many(list_db_data)
                    self.task['task_start_loadid'] = res.inserted_ids[0]
                    self.crawled_times += 1
                elif stop_idx == 0:
                    self.task['task_status'] = 'end_success'
                    print('要出去了')
                elif stop_idx != 0:
                    res = mongo_instance.loads.insert_many(list_db_data[0::stop_idx])
                    self.task['task_start_loadid'] = res.inserted_ids[0]
                    self.task['task_status'] = 'end_success'
                    print('要出去了')


        self.task['task_updatetime'] = t
        self.task['task_endtime'] = t
        mongo_instance.tasks.find_one_and_update(
            filter={'_id': self.task['_id']}, update={
                '$set': self.task
            })


        if not 'running' in self.task['task_status']:
            return
        else:
            yield scrapy.Request(url=add_or_replace_parameter(response.url, 'offset', next_offset), headers=FakeLoadParams.headers, cookies=FakeLoadParams.cookies, method='GET')

    def run_crawl_count(self, response):
        print(' --- run_crawl_count --- ')
        t = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
        next_offset = int(url_query_parameter(response.url, 'offset')) + 10

        list_parse_res = list_parse(eval(response.body.decode()))
        list_db_data = list_into_dbdata(
            list_parse_res, self.task['task_biz_enname'], self.task['task_biz_chname'], self.task['_id'])

        # 到头了或者出错了
        if not list_db_data:
            self.task['task_status'] = 'end_success'
            print('要出去了')
        else:
            if self.crawled_times == self.task['task_crawl_count'] / 10:
                res = mongo_instance.loads.insert_many(list_db_data)
                self.task['task_start_loadid'] = res.inserted_ids[0]
                self.task['task_status'] = 'end_success'
                print('要出去了')
            else:
                res = mongo_instance.loads.insert_many(list_db_data)
                if self.crawled_times == 1:
                    self.task['task_start_loadid'] = res.inserted_ids[0]
                self.crawled_times += 1
                print('还有请求呢别着急出去')


        self.task['task_updatetime'] = t
        self.task['task_endtime'] = t
        mongo_instance.tasks.find_one_and_update(
            filter={'_id': self.task['_id']}, update={
                '$set': self.task
            })


        if not 'running' in self.task['task_status']:
            return
        else:
            yield scrapy.Request(url=add_or_replace_parameter(response.url, 'offset', next_offset), headers=FakeLoadParams.headers, cookies=FakeLoadParams.cookies, method='GET')

    def run_crawl_all(self, response):
        print(' --- run_crawl_all --- ')
        t = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
        next_offset = int(url_query_parameter(response.url, 'offset')) + 10

        list_parse_res = list_parse(eval(response.body.decode()))
        list_db_data = list_into_dbdata(
            list_parse_res, self.task['task_biz_enname'], self.task['task_biz_chname'], self.task['_id'])

        # 到头了或者出错了
        if not list_db_data:
            self.task['task_status'] = 'end_success'
            print('要出去了')
        else:
            res = mongo_instance.loads.insert_many(list_db_data)
            if self.crawled_times == 1:
                print(' 插入的第一个id是: %s' % res.inserted_ids[0])
                self.task['task_start_loadid'] = res.inserted_ids[0]
            self.crawled_times += 1
            print('还有请求呢别着急出去')

        self.task['task_updatetime'] = t
        self.task['task_endtime'] = t
        mongo_instance.tasks.find_one_and_update(
            filter={'_id': self.task['_id']}, update={
                '$set': self.task
            })

        if not 'running' in self.task['task_status']:
            return
        else:
            yield scrapy.Request(url=add_or_replace_parameter(response.url, 'offset', next_offset), headers=FakeLoadParams.headers, method='GET')
