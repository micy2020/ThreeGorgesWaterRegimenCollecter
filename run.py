# -*- coding: UTF-8 -*-

import requests,json
import os
import time,datetime
import pymysql
import queue,threading
import xlsxwriter as xlwt
import configparser

url = "http://113.57.190.228:8001/web/Report/RiverReport"

modelIdList=[
        '50c13b5c83554779aad47d71c1d1d8d8', # 三峡
        '622108b56feb41b5a9d1aa358c52c236', # 葛洲坝
        '3245f9208c304cfb99feb5a66e8a3e45', # 向家坝
        '8a2bf7cbd37c4d4f961ed1a6fbdf1ea8'  # 溪洛渡
        ]
modelNameList=[
    '三峡',
    '葛洲坝',
    '向家坝',
    '溪洛渡'
]

col=['ckList','rkList','syList','xyList']
colAlias={
    'ckList':'outSpeed',
    'rkList':'inSpeed',
    'syList':'upLevel',
    'xyList':'downLevel'
}

cf=configparser.ConfigParser()
cf.read(os.path.dirname(os.path.realpath(__file__))+'/config.ini',encoding='utf8')

# 用户配置项
excelFileName=cf['excel-file']['name']
targetDir=cf['excel-file']['path']
# 初始时间
startDate=cf['common']['start_date']
startDate=datetime.datetime.strptime(startDate,"%Y-%m-%d").date()
# recent_sync_days
recent_sync_days=int(cf['common']['recent_sync_days'])

database=cf['mysql-database']
# backup_regimen_hours
backup_regimen_hours = int(database['backup_regimen_hours'])

# conn=pymysql.connect(cf.get('mysql-database','host'),cf.get('mysql-database','user'),cf.get('mysql-database','passwd'),cf.get('mysql-database','db'),cf.get('mysql-database','charset'))
conn=pymysql.connect(host=database['host'],user=database['user'],passwd=database['password'],db=database['db'],charset=database['charset'])

# 加载代理配置
if 'proxies' in cf.sections() and int(cf['proxies']['enabled']):
    proxies={
        'http':cf['proxies']['http'],
        'https':cf['proxies']['https']
    }
else:
    proxies=int(cf['proxies']['enabled'])

thLock=threading.Lock()
dateQueue=queue.Queue()

def get_data_by_date(dt):
    data=[]
    for modelId in modelIdList:
        res=get_water_data_by_id_and_date(modelId,dt)
        if not res:
            return False
        else:
            data.append(res)
    return data

# 检查 json
def check_json(str):
    try:
        json.load(str)
        return True
    except:
        return False

# 根据 modelId 和 date 获取水情信息
def get_water_data_by_id_and_date(modelId,cDate):
    payload='time='+cDate.strftime("%Y-%m-%d")
    headers = {
        #'cookie': "JSESSIONID=694985A069B377839B1249B0D8A9348D",
        'origin': "http://113.57.190.228:8001/web/Report/RiverReport",
        'accept-encoding': "gzip, deflate",
        'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6",
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36",
        'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
        'accept': "application/json, text/javascript, */*; q=0.01",
        'referer': "http://113.57.190.228:8001/web/Report/RiverReport",
        'x-requested-with': "XMLHttpRequest",
        'proxy-connection': "keep-alive",
        'dnt': "1",
        'cache-control': "no-cache"
        }
    querystring = {"moduleId":modelId,"struts.portlet.mode":"view","struts.portlet.action":"/portlet/waterFront!getDatas.action"}
    if proxies:
        response = requests.request("POST", url, data=payload, headers=headers, params=querystring,proxies=proxies,timeout=10)
    else:
        response = requests.request("POST", url, data=payload, headers=headers, params=querystring,timeout=10)
    try:
        if(response.status_code!=200 or check_json(response.text)):
            # 查询出错
            return False
        else:
            res=response.json()
            res['modelId']=modelId
            return res
    except Exception as e:
        return False

def update_database(date,data):
    try:
        cursor=conn.cursor()
        for site in data:
            # 对于每个站
            for c in col:
                # 对于每个参数
                for t in site[c]:
                    # 对于每个时刻, 更新或插入
                    cursor.execute("SELECT id FROM water_regimen WHERE date='%s' and hour=%d and site='%s'"%(date,int(t['time']),site['senName']))
                    oldRowId=cursor.fetchone()
                    if not oldRowId:
                        # 空, 创建新的
                        cursor.execute("INSERT INTO water_regimen (`date`,`hour`,`site`,`%s`) VALUES ('%s',%d,'%s',%f)"%(colAlias[c],date,int(t['time']),site['senName'],float(t['avgv'])))
                    else:
                        # 已经存在, 更新
                        cursor.execute("UPDATE water_regimen SET %s=%f WHERE id=%d"%(colAlias[c],float(t['avgv']),oldRowId[0]))
        cursor.close()
        conn.commit()
    except Exception as e:
        cursor.close()
        return False
def get_all_water_data_by_date_section(startDate,endDate):
    # 开始获取
    print("开始获取数据,日期区间:"+startDate.strftime("%Y-%m-%d")+" - "+endDate.strftime("%Y-%m-%d"))
    currentDate=startDate
    while(currentDate<=endDate):
        # 获取该天数据
        try:
        	currentDateData=get_data_by_date(currentDate)
        	# 存储数据到 sql 数据库中
        	update_database(currentDate.strftime("%Y-%m-%d"),currentDateData)
        	# 日期+1
        	print(currentDate," 已同步")
        	currentDate=currentDate+datetime.timedelta(days=1)
        except Exception as e:
                print("获取数据失败,运行出错")
                print(e)
                return False
    return True

def create_table():
    try:
        cursor=conn.cursor()
        with open('water_regimen.sql',encoding='utf8') as f:
            sql_list=f.read().split(';')[:-1]
            sql_list=[x.replace('\n', ' ') if '\n' in x else x for x in sql_list]
        for sql_item  in sql_list:
            cursor.execute(sql_item)
        cursor.close()
        conn.commit()
        return True
    except Exception as e:
        print(e)
        cursor.close()
        conn.commit()
        return False

def delete_old_tables():
    print('开始清理旧表...')
    # 需要保持的日期
    startDatetime=datetime.datetime.today()-datetime.timedelta(hours=backup_regimen_hours)
    # 获取旧表名称列表
    cursor=conn.cursor()
    cursor.execute("SHOW TABLES LIKE 'water_regimen_%'")
    # 获取所有表
    for t in cursor.fetchall():
        # 检查时间是否超过限制
        dbDatetime=datetime.datetime.strptime(t[0][14:],"%Y%m%d%H%M%S")
        if dbDatetime<startDatetime:
            cursor.execute("DROP TABLE "+t[0])
            print("删除过旧的表: "+t[0])
    cursor.close()
    return True

def database_backup():
    cursor=conn.cursor()
    cursor.execute("SHOW TABLES LIKE 'water_regimen'")
    if not cursor.fetchone():
        print("不存在该表,创建表")
        create_table()
    # 复制表
    cursor.execute("CREATE TABLE water_regimen_%s SELECT * FROM water_regimen" % datetime.datetime.today().strftime("%Y%m%d%H%M%S"))
    print('复制表成功')
    # 获取最大的日期
    cursor.execute("SELECT max(date) FROM water_regimen")
    row=cursor.fetchone()
    cursor.close()
    # 删除过久的备份
    delete_old_tables()
    if not row or not row[0]:
        return False
    else:
        return row[0]

def update_excel_file():
    outputFile=xlwt.Workbook(targetDir+excelFileName)
    print("打开Excel文件:"+targetDir+excelFileName)
    cursor=conn.cursor()
    # 分站点类型导出为表
    for site in modelNameList:
        # 对于每个站点
        cursor.execute("SELECT date,hour,site,upLevel,downLevel,inSpeed,outSpeed FROM water_regimen WHERE site='%s' ORDER BY date DESC,hour DESC"%site)
        # fields=cursor.description
        fields=['日期','时间','站点','上游水位(m)','下游水位(m)','入库(m^3/s)','出库(m^3/s)']
        # cursor.scroll(0,mode='absolute')
        results=cursor.fetchall()
        # 记录为表
        sheet=outputFile.add_worksheet(site)
        # 标题
        for field in range(0,len(fields)):
            sheet.write(0,field,fields[field])
        # 添加行
        row = 1
        col = 0
        for row in range(1,len(results)+1):
            for col in range(0,len(fields)):
                sheet.write(row,col,u'%s'%results[row-1][col])
    cursor.close()
    outputFile.close()
    print("文件写入完成.")
    # outputFile.save(excelFileName)
    # 将文件复制到下载目录
    # outputFile.save(targetDir+excelFileName)
    # shutil.copy(excelFileName,targetDir)

def loop():
    while True:
        thLock.acquire()
        if dateQueue.empty():
            # 已经完成任务
            thLock.release()
            break
        # 从队列获取日期
        date=dateQueue.get()
        thLock.release()
        # 获取参数
        currentDateData=get_data_by_date(date)
        # 存储数据到 sql 数据库中
        update_database(date.strftime("%Y-%m-%d"),currentDateData)
        print(date," 已同步")

def collectTask():
    print("任务启动:",datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%I"))
    # 设置初始时间
    sDate=startDate
    # 获取当前日期
    eDate=datetime.date.today()
    # 备份数据库, 找到上次备份的日期
    dtLastDate=database_backup()
    if dtLastDate and dtLastDate>sDate:
        # 若数据库有数据
        currentDate=dtLastDate-datetime.timedelta(days=recent_sync_days)
    else:
        # 设置的初始时间
        currentDate=sDate
    print("初始日期:",currentDate)
    # # 创建 dateQueue
    # while currentDate<=eDate:
    #     thLock.acquire()
    #     dateQueue.put(currentDate)
    #     thLock.release()
    #     currentDate=currentDate+datetime.timedelta(days=1)
    # # 创建多线程
    # thList=[]
    # for i in range(5):
    #     t=threading.Thread(target=loop)
    #     t.start()
    #     thList.append(t)
    # for t in thList:
    #     t.join()
    get_all_water_data_by_date_section(currentDate,eDate)
    print("任务结束:",datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%I"))
        

if __name__=='__main__':
    # 采集数据
    collectTask()
    # database_backup()
    # 转为 csv 提供下载
    update_excel_file()
