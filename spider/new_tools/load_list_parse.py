import json


"""
1. 出错return原样
2. general_msg_list不是字符串return 原样
3. list无内容return原样
4. 成功有内容的return load_list
"""


def list_parse(load_res_dict):
    print(load_res_dict['ret'])
    if not load_res_dict['ret'] == 0:
        return load_res_dict
    elif not type(load_res_dict['general_msg_list']) == type(str('s')):
        return load_res_dict
    else:
        load_list = eval(load_res_dict['general_msg_list'])
        if(len(load_list['list']) == 0):
            return load_res_dict
        else:
            print('Success')
            # print(load_list)
            return load_list


"""
return list
具体结构见items/list.json
"""


def list_into_dbdata(obj):
    list_lo = obj['list']
    list_db = list()
    if len(list_lo) > 0:
        for big_li in list_lo:
            big_item = {}
            for b_key, b_value in big_li['app_msg_ext_info'].items():
                if b_key == 'content_url' or b_key == 'cover' or b_key == 'source_url':
                    b_value = b_value.replace('\\', '')
                if b_key == 'multi_app_msg_item_list' and len(b_value) > 0:
                    for small_li in b_value:
                        # print(small_li)
                        small_item = {}
                        for s_key, s_value in small_li.items():
                            if s_key == 'content_url' or s_key == 'cover' or s_key == 'source_url':
                                s_value = s_value.replace('\\', '')
                            small_item[s_key] = s_value
                        list_db.append(small_item)
                else:
                    big_item[b_key] = b_value
            list_db.append(big_item)
        print(list_db)
        return list_db
