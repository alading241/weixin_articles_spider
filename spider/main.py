# 构造home请求获取 appmsg_token
# 构造分页请求
#
from tools.load_list_parse import list_into_dbdata, list_parse
from phone.operate import Operate
from instance import redis_instance, db_instance, db_loadlist
import json
import re
from time import time
import datetime as d
import requests
from http.cookies import SimpleCookie
from http import cookiejar
import urllib.parse as urlparse

class Fakehomeparams:
    cookies = {
        'rewardsn': '',
        'wxuin': '3604431997',
        'devicetype': 'android-23',
        'version': '27000634',
        'lang': 'zh_CN',
        'pass_ticket': '',
        'wap_sid2': '',
        'wxtokenkey': '777',
    }

    headers = {
        'Host': 'mp.weixin.qq.com',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1; PAR-AL00 Build/HUAWEIPAR-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/044304 Mobile Safari/537.36 MicroMessenger/6.7.3.1360(0x26070333) NetType/WIFI Language/zh_CN Process/tools',
        'x-wechat-uin': '',
        'x-wechat-key': '',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'X-Requested-With': 'com.tencent.mm',
    }

    params = (
        ('action', 'home'),
        ('__biz', ''),
        ('devicetype', 'android-23'),
        ('version', '27000634'),
        ('lang', 'zh_CN'),
        ('nettype', 'WIFI'),
        ('a8scene', '7'),
        ('session_us', 'gh_9e26999263b5'),
        ('pass_ticket', ''),
        ('wx_header', '1'),
    )


class Fakeloadparams:
    cookies = {
        'rewardsn': '',
        'wxtokenkey': '777',
        'wxuin': '3604431997',
        'devicetype': 'android-23',
        'version': '27000634',
        'lang': 'zh_CN',
        'pass_ticket': '',
        'wap_sid2': '',
    }

    headers = {
        'Host': 'mp.weixin.qq.com',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1; PAR-AL00 Build/HUAWEIPAR-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/044304 Mobile Safari/537.36 MicroMessenger/6.7.3.1360(0x26070333) NetType/WIFI Language/zh_CN Process/tools',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*',
        # 'Referer': 'https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzUyMzkwNTQzNQ==&devicetype=android-23&version=27000634&lang=zh_CN&nettype=WIFI&a8scene=7&session_us=gh_9e26999263b5&pass_ticket=%2FwVUpAEtgoBvTouSB3nRI5qyK6t2sGFiihU0qj8IjUsCRWbJixaNVyZ7%2FeO0iFjG&wx_header=1',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
    }

    params = (
        ('action', 'getmsg'),
        ('__biz', 'MzUyMzkwNTQzNQ=='),
        ('f', 'json'),
        ('offset', '0'),
        ('count', '10'),
        ('is_ok', '1'),
        ('scene', ''),
        ('uin', '777'),
        ('key', '777'),
        ('pass_ticket', ''),
        ('wxtoken', ''),
        ('appmsg_token', ''),
        ('x5', '0'),
    )

class NORMAL_URLS:
    home = "https://mp.weixin.qq.com/mp/profile_ext?action=home"
    getmsg = "https://mp.weixin.qq.com/mp/profile_ext?action=getmsg"
    article = "https://mp.weixin.qq.com/s?"

def replace_at_index(tup, ix, val):
    lst = list(tup)
    lst[ix] = val
    return tuple(lst)


def send_request():
    response = requests.get('https://mp.weixin.qq.com/mp/profile_ext',
                        headers=Fakehomeparams.headers, params=Fakehomeparams.params, cookies=Fakehomeparams.cookies)
    if response.content.decode().find('失效的验证页面') > 0:
        print('失效的验证页面')
    else:
        login_cookies = requests.utils.dict_from_cookiejar(response.cookies)
        print('第二次的wap_sid2=' + login_cookies['wap_sid2'])
        print('pass_ticket=' + login_cookies['pass_ticket'])
        Fakeloadparams.cookies['pass_ticket'] = login_cookies['pass_ticket']
        Fakeloadparams.cookies['wap_sid2'] = login_cookies['wap_sid2']
        Fakeloadparams.params = replace_at_index(
            Fakeloadparams.params, 9, ('pass_ticket', login_cookies['pass_ticket']))
        return response.content.decode()



def build_home_request_1(data):
    # print(data)
    cookie = SimpleCookie()
    cookie.load(data['REQUEST_COOKIE'])
    cookies = {}
    cookies = {i.key: i.value for i in cookie.values()}
    Fakehomeparams.cookies['wxuin'] = cookies['wxuin']
    # Fakehomeparams.cookies['version'] = cookies['version']
    Fakehomeparams.cookies['pass_ticket'] = cookies['pass_ticket']
    Fakehomeparams.cookies['wap_sid2'] = cookies['wap_sid2']
    Fakehomeparams.params = replace_at_index(
        Fakehomeparams.params, 8, ('pass_ticket', cookies['pass_ticket']))

def build_home_request_2(data):
    # print(data)
    Fakehomeparams.headers['x-wechat-uin'] = data['REQUEST_HEADERS']['X-WECHAT-UIN']
    Fakehomeparams.headers['x-wechat-key'] = data['REQUEST_HEADERS']['X-WECHAT-KEY']
    biz = urlparse.parse_qs(data['REQUEST_DATA'])['__biz'][0]
    print('X-WECHAT-UIN=' + data['REQUEST_HEADERS']['X-WECHAT-UIN'])
    print('X-WECHAT-KEY=' + data['REQUEST_HEADERS']['X-WECHAT-KEY'])
    print('biz=' + biz)
    Fakehomeparams.params = replace_at_index(
        Fakehomeparams.params, 1, ('__biz', biz))



def build_load_request(appmsg_token):
    print(appmsg_token)

    Fakeloadparams.params = replace_at_index(
        Fakeloadparams.params, 1, ('__biz', Fakehomeparams.params[1][1]))

    Fakeloadparams.params = replace_at_index(
        Fakeloadparams.params, 11, ('appmsg_token', appmsg_token))

    print(Fakeloadparams.headers)
    print(Fakeloadparams.cookies)
    print(Fakeloadparams.params)


def save_list_to_db(list_db):
    # TODO fix
    db_loadlist.insert_many(list_db)
    pass

def loop_request_load():
    import time
    print(d.datetime.now().strftime("%Y.%m.%d-%H:%M:%S"))
    idx=0
    items_len=0
    offset=0
    # return
    # 循环机制改变一下 需要捕捉到所有的真实错误
    # ANCHOR 测试结果 一天最多请求 1000次
    while True:
        try:
            try:
                response = requests.get(
                    'https://mp.weixin.qq.com/mp/profile_ext',
                    headers=Fakeloadparams.headers,
                    params=Fakeloadparams.params,
                    cookies=Fakeloadparams.cookies
                )
            except Exception as request_err:
                print(request_err)
                raise Exception('HUMAN_ERROR: 请求出错了')

            idx+=1
            offset+=10

            Fakeloadparams.params = replace_at_index(
                Fakeloadparams.params, 3, ('offset', offset))

            list_parse_res = list_parse(eval(response.text))
            print(type(list_parse_res))
            if type(list_parse_res['ret']) == type(0):
                print(list_parse_res)
                raise Exception('HUMAN_ERROR: 这条数据parse失败了')
            list_db_data = list_into_dbdata(list_parse_res)
            if not list_db_data:
                raise Exception('HUMAN_ERROR: 后面无数据了')

            try:
                save_list_to_db(list_db_data)
            except Exception as db_err:
                print(db_err)
                raise Exception('HUMAN_ERROR: 数据库插入出错了')
            items_len += len(list_db_data)
            print('成功处理第 {} 个load请求，当前 offset= {} items_len= {}'.format(
                idx, offset, items_len))
            time.sleep(3)
        except Exception as err:
            print('失败处理第 {} 个load请求，当前 offset= {} items_len= {}'.format(
                idx, offset, items_len))
            print(err)
            if str(err).find('无数据') > 0:
                break
    print(d.datetime.now().strftime("%Y.%m.%d-%H:%M:%S"))


def operate_phone(client):
    client.home_click()
    # client.search_text()
    # client.tab_click()
    # client.enter_into_gzh()


if __name__ == '__main__':
    print('__main__')

    from get_redis_data import get_data_from_redis
    get_data_from_redis()


    # client = Operate('苏州青舞舞蹈艺术')
    # operate_phone(client)


    # 一组一组拿出来
    # keys = redis_instance.keys('*_REQUEST')
    # # 1.json
    # geticon_key = str(keys[0], encoding="utf-8")
    # # 2.json
    # getappmsgext_key = str(keys[1], encoding="utf-8")
    # geticon_value = redis_instance.get(geticon_key)
    # getappmsgext_value = redis_instance.get(getappmsgext_key)
    # geticon_value = json.loads(geticon_value.decode())
    # getappmsgext_value = json.loads(getappmsgext_value.decode())
    # # print(geticon_value)
    # # print(getappmsgext_value
    # build_home_request_1(geticon_value)
    # build_home_request_2(getappmsgext_value)
    # content = send_request()
    # if not content:
    #     print('无效content')
    #     content = ''


    # if content.find('操作频繁') > 0:
    #     print('HUMAN_ERROR: 操作频繁 限制24小时 请更换微信')


    # pat = re.compile(r'window.appmsg_token = "(.*?)"')
    # appmsg_tokens = pat.findall(content, pos=0)

    # for m in appmsg_tokens:
    #     build_load_request(m)
    #     loop_request_load()




