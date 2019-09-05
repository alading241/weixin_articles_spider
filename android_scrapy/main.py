import scrapy
from android_scrapy.spiders.loadSpider import LoadSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor
from twisted.internet.task import deferLater
from instance import mongo_instance, redis_instance
import time

def sleep(self, *args, seconds):
    """Non blocking sleep callback"""
    return deferLater(reactor, seconds, lambda: None)

process = CrawlerProcess(get_project_settings())


def _crawl(result, spider):
    deferred = process.crawl(spider)
    deferred.addCallback(lambda results: print(
        '稍等。6秒后会自动重启...'))
    deferred.addCallback(sleep, seconds=6)
    deferred.addCallback(_crawl, spider)
    return deferred

suber = redis_instance.pubsub()
suber.subscribe('there_is_a_http')
while True:
    res = suber.parse_response()
    httpid = redis_instance.get('__running_http_')
    if httpid:
        # redis_instance.delete('__running_http_')
        print('检测到了新的的http')
        _crawl(None, LoadSpider)
        process.start()
    else:
        print('没有成功捕获到新的http')
