# coding:utf-8
"""
blue king scraper
蓝鲸日志批量下载器
"""
import requests
import json
import os.path
import urllib.parse
import sys
from datetime import datetime, timedelta


# 游戏的 appid
appid=100415
# 存储所有的区列表
zone_dict_fname = 'zone.json'
# 存储 区-->该区所有服务器组的映射
module_dict_fname = 'module.json'
# 存储 服务器组-->该组所有服务器ip的映射
ip_list_name = 'ip_list.json'
# 存储 进程名(小写)-->该进程所有日志的映射
all_log_fname = 'log.json'

cookie_str = 'ABCD'

get_zone_header = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    'X-CSRFToken' : 'hglHmVKYCcvlQZ9cD9BBghN8AprjbTiz',
    'Referer' : 'http://app.o.tencent.com/smite_log/log/',
    'Accept' : 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With' : 'XMLHttpRequest',
    'Cookie' : cookie_str
}

# 从文件缓存中取得区列表
# key : 区号
# value: 该区对应的服务器数据
def get_zone_dict_from_file_cache():
    f = open(zone_dict_fname, 'r')
    data = f.read()
    j = json.loads(data)
    ret = {}
    for each in j:
        ret[each['value']] = each

    return ret

# 发起 http 请求来获得区号
def get_zone_dict_from_http_request():
    get_zone_url = 'http://app.o.tencent.com/smite_log/log/get_toposet/?app_id={}'.format(appid)    
    get_zone_data = {'app_id' : appid}
    session = requests.Session()
    req = requests.Request('GET', get_zone_url, data = get_zone_data, headers = get_zone_header)
    prepped = req.prepare()    
    response = session.send(prepped)
    j = json.loads(response.text)
    # write zone list to file
    f = open(zone_dict_fname, 'w', encoding='utf-8')
    print(json.dumps(j, indent=2), file=f)
    f.close()
    ret = {}
    for each in j:
        ret[each['value']] = each
    return ret

def get_zone_dict():
    ret = None    
    if os.path.exists(zone_dict_fname):
        ret = get_zone_dict_from_file_cache()

    need_http = False
    if ret is None:
        need_http = True        
    else:
        if len(ret.keys()) != 0:
            return ret

    if need_http is True:
        ret = get_zone_dict_from_http_request()
        
    return ret

def get_server_list_from_file(zoneid):
    f = open(module_dict_fname, 'r')
    all_json = json.loads(f.read())
    return all_json.get(str(zoneid), [])

def get_server_list_from_http_request(zone_dict, zoneid):
    # 找到该区的id
    zone_set_info = zone_dict.get(str(zoneid), None)
    if zone_set_info is None:
        print("Could not get zone=" + str(zoneid))
        return
    zone_str_id = urllib.parse.quote(zone_set_info['id'])

    # 发起请求
    get_module_url = 'http://app.o.tencent.com/smite_log/log/get_toposet/?app_id={}&id={}'.format(appid, zone_str_id)
    get_module_data = {'app_id' : appid, 'id' : zone_str_id}
    session = requests.Session()
    req = requests.Request('GET', get_module_url, data = get_module_data, headers = get_zone_header)
    prepped = req.prepare()
    response = session.send(prepped)    
    
    # 在所有区的json字符串中,替换掉该区号的值
    j = json.loads(response.text)
    all_json = {}
    if os.path.exists(module_dict_fname):
        f = open(module_dict_fname, 'r')
        all_json = json.loads(f.read())
        f.close()
    all_json[str(zoneid)] = j    
    writef = open(module_dict_fname, 'w', encoding='utf-8')
    print(json.dumps(all_json, indent=2), file = writef)
    writef.close()
    return j

"""
获取某个区的所有服务器列表
zoneid:'7006'(区号)
返回:该区的所有服务器组
先从文件里去找,如果找到了,直接用;找不到，发起http请求
"""
def get_server_list(zoneid):
    ret = []
    if os.path.exists(module_dict_fname):
        ret = get_server_list_from_file(zoneid)

    if len(ret) != 0:
        return ret

    ret = get_zone_dict()
    return get_server_list_from_http_request(ret, zoneid)

def get_ip_list_from_file(module_name):
    f = open(ip_list_name, 'r')
    all_json = json.loads(f.read())
    return all_json.get(module_name, [])

"""
根据模块名(7006-sc)获取改模块的所有服务器Ip(所有场景服务器的ip地址)
hack : 如果直接传 id=7006-gs 的话，会返回所有区的服务器ip地址列表
"""
def get_ip_list_from_http_request(module_name, module_id):
    encoded_module_id = urllib.parse.quote(module_id)
    get_ip_url = 'http://app.o.tencent.com/smite_log/log/get_toposet/?app_id={}&id={}'.format(appid, encoded_module_id)
    get_ip_data = {'app_id':appid, 'id':encoded_module_id}
    session = requests.Session()
    req = requests.Request('GET', get_ip_url, data = get_ip_data, headers = get_zone_header)
    prepped = req.prepare()
    response = session.send(prepped)    

    # 替换已有的区文件,并存档
    j = json.loads(response.text)
    all_json = {}
    if os.path.exists(ip_list_name):
        f = open(ip_list_name, 'r')
        all_json = json.loads(f.read())
        f.close()

    all_json[module_name] = j
    writef = open(ip_list_name, 'w', encoding='utf-8')
    print(json.dumps(all_json, indent=2), file=writef)
    writef.close()
    return j

def get_ip_list(module_name, module_id):
    ret = None
    if os.path.exists(ip_list_name):
        ret = get_ip_list_from_file(module_name)
    
    if ret is None or len(ret) == 0:
        ret = get_ip_list_from_http_request(module_name, module_id)
    return ret

def get_zone_all_server_ip_list(zoneid):
    modulename_to_iplist = {}    
    modules = get_server_list(zoneid)
    for one_module in modules:
        iplist = []        
        tmp_ip_list = get_ip_list(one_module['value'], one_module['id'])        
        for tmp_ip in tmp_ip_list:
            iplist.append(tmp_ip['value'])
        modulename_to_iplist[one_module['value']] = iplist

    return modulename_to_iplist


# 服务器名 --> 模块名的映射,约定俗称的...
#'miscserver' : 'gs',
servername_to_modulename = {
    'superserver' : 'gs',
    'sessionserver' : 'gs',
    'recordserver' : 'gs',
    'mailserver' : 'gs',
    'functionserver' : 'gs',    
    'miscserver' : 'gs',
    'scenesserver' : 'sc',
    'gatewayserver' : 'gw'    
}

"""
最关键的函数:
根据要查询的日志类型,构造出文件列表
"""
def get_one_date_file_list(zoneid, need_download_server_list, one_date, hour_list):
    modulename_to_iplist = get_zone_all_server_ip_list(zoneid)
    filelist = []

    # 遍历每个服务器
    for one_server in need_download_server_list:
        # 获取该服务器所在的模块,进而获取到该服务器的ip地址列表
        module_name = str(zoneid) + "-" + servername_to_modulename[one_server]
        filename_prefix = '/data/home/user00/log/' + one_server + '/'
        filename_suffix = '.log'        
        today_date = datetime.today().date()        
        if one_date < today_date:
            filename_prefix = '/data/home/user00/log/' + one_server + '/' + one_date.strftime("%y%m%d") + '/'
        iplist = modulename_to_iplist.get(module_name, [])
        filename_list = []
        if len(iplist) == 1:
            filename_list = [iplist[0] + "," + filename_prefix + one_server + filename_suffix]
        elif len(iplist) > 1:
            if one_server == 'scenesserver':
                for i in range(len(iplist)):
                    filename_list.append(iplist[i] + "," + filename_prefix + one_server + str(21+i) + filename_suffix)
            elif one_server == 'gatewayserver':
                for i in range(len(iplist)):
                    filename_list.append(iplist[i] + "," + filename_prefix + one_server + str(2201+i) + filename_suffix)

        # 遍历每一个文件,加上对应的小时后缀
        for one_filename in filename_list:            
            for one_hour in hour_list:
                delta = datetime.today().now() - datetime(one_date.year, one_date.month, one_date.day, int(one_hour), 1, 1)
                # todo,超过 48+15 小时的日志文件，会被压缩为 .gz 格式的日志文件
                if delta.days > 2 or (delta.days == 2 and delta.seconds / 3600 >= 14):
                    one_hour = one_hour + '.gz'
                filelist.append(one_filename + "." + one_date.strftime("%y%m%d") + "-" + one_hour + ",1KB")
    return filelist

"""
获取平台文件列表
"""
def get_plat_file_list():
    pass

def batch_download(zoneid, server_list,one_date, hour_list):
    post_url = 'http://app.o.tencent.com/smite_log/log/get_batch_file/'
    #flist = get_one_date_file_list(7006, servername_to_modulename.keys(), datetime.today().date(), all_hour_list)
    #all_hour_list = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15','16','17','18','19', '20','21', '22', '23']    
    flist = get_one_date_file_list(zoneid, server_list, one_date, hour_list)    
    
    post_data = {
        'app_id' : appid,
        'estimated_download_time' : 1,
        'file_list[]' : flist
    }
    session = requests.Session()
    response = session.post(post_url, data = post_data, headers = get_zone_header)
    print(response.text)

def test_single_file_download(fname, serverip):
    post_url = 'http://app.o.tencent.com/smite_log/log/quick_download/'
    post_data = {
        'app_id' : 100415,
        'qs_ip' : serverip,
        'qs_filename' : fname
    }
    session = requests.Session()
    response = session.post(post_url, data = post_data, headers = get_zone_header)
    if response.status_code == 200:
        print('Download file success:' + fname)
    else:
        print('Fuck, Download file failed:' + fname)


"""
根据日期,下载某个区,某个日期的全部日志.
如果是要下载今天的全部日志，注意判断下当前小时数,如果当前是5点，则不能下载超过5点的日志,即只下载[0,1,2,3,4]点的日志
如果是下载今天之前的日志，直接传24小时即可
每6个小时打一个包,防止作业过大被终止
"""
def download_allday_log_by_date(zoneid, one_date):
    all_hour_list = ['00','01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15','16','17','18','19', '20','21', '22', '23']
    hour_list = []    
    if one_date < datetime.today().date():
        hour_list = all_hour_list
    else:
        hour_list = [format(i, '02d') for i in range(datetime.today().hour)]
        
    batch_download(zoneid, servername_to_modulename.keys(),one_date, hour_list)

"""
下载当前小时的日志文件
只能一个一个下载，忍着吧
操蛋的蓝鲸,对于当前小时的文件，只能一个一个下载
"""
def download_current_hour_log_one_by_one(zoneid, server_list):    
    hour_list = [str(datetime.today().hour)]
    today_date = datetime.today().date()
    flist = get_one_date_file_list(zoneid, server_list, today_date, hour_list)
    for eachf in flist:
        tmp_array = eachf.split(',')
        if len(tmp_array) < 2:
            print('fuck, file list error=' + eachf)
        test_single_file_download(tmp_array[1], tmp_array[0])

"""
下载今天指定某几个小时的日志
"""
def download_hour_log(zoneid, server_list, hour_list):
    
    current_hour = datetime.today().hour
    current_hour_str = str(current_hour)
    if current_hour < int(hour_list[-1]):
        print('fuck, request to download future log file')
        return
    if current_hour_str in hour_list:
        download_current_hour_log_one_by_one(zoneid, server_list)
        hour_list.remove(current_hour_str)
    
    
    batch_download(zoneid, server_list, datetime.today().date(), hour_list)
    #batch_download(zoneid, server_list, datetime(2019,6,8), hour_list)

# 注意:某天停服维护时,会导致日志下载失败,因为构造的文件列表里包含了不存在文件
# 此时要根据停服时间,传进去 hour_list
"""
0:正式服plat0
00:预发布plat00
000:压测plat000
0000:自研云plat0000
"""
today_date = datetime.today().date()
#download_allday_log_by_date(8300,  today_date - timedelta(3))
# 190731
#download_allday_log_by_date(1001,  today_date - timedelta(2))
#batch_download('0', ['superserver'], today_date - timedelta(1), ['00','01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15','16','17','18','19', '20','21', '22', '23'])
#batch_download(1001, ['mailserver'], today_date - timedelta(2), ['15','16'])
# 20190903
#batch_download(1001, ['superserver', 'scenesserver'], today_date - timedelta(1), ['00','01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15','16','17','18','19', '20','21', '22', '23'])
#download_current_hour_log_one_by_one(8200, ['scenesserver', 'functionserver'])
#download_current_hour_log_one_by_one(8200, ['mailserver'])
#download_hour_log(8200, servername_to_modulename.keys(), ['17'])
