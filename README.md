# 三峡库区库水位采集脚本 V1.0
## 介绍
本脚本用于采集三峡库区每日库水位数据，数据来源为[中国长江三峡集团有限公司](http://www.ctg.com.cn/sxjt/sqqk/index.html)
采集结果放置在 mysql 数据库中, 方便用户查询下载。

博客: https://blog.cuger.cn/p/54193/

直接下载链接: https://api.cuger.cn/ThreeGorgesWaterRegimenCollecter/ThreeGorgesWaterRegimen.xlsx

## 使用说明
此脚本用于服务端。自动自动采集数据，并存到数据库，提供文件下载。

### 配置文件

```bash
[common]
； 同步设置
; 最早同步时间
start_date=2019-2-28
; 近期同步天数
recent_sync_days=7

; mysql 数据库配置
[mysql-database]
host=127.0.0.1
user=root
password=
db=three_gorges_water_regimen
main_table=water_regimen
charset=utf8

; Excel文件名及路径
[excel-file]
name=ThreeGorgesWaterRegimen.xlsx
path=

; 代理设置
[proxies]
; 是否开启 1/0
enabled=0
; http 代理
http=127.0.0.1:8118
; https 代理
https=127.0.0.1:8118
```

## 数据预览

![2001-2019水位](https://github.com/Doradx/ThreeGorgesWaterRegimenCollecter/blob/master/res/%E4%B8%89%E5%B3%A1%E5%BA%93%E5%8C%BA%E6%B0%B4%E4%BD%8D2001-2019.png?raw=true)
![2019年上游水位](https://raw.githubusercontent.com/CUGxia/ThreeGorgesWaterRegimenCollecter/master/res/三峡库区水位2019.png)

## 数据下载地址
直接下载地址为: https://api.cuger.cn/ThreeGorgesWaterRegimenCollecter/ThreeGorgesWaterRegimen.xlsx

# 联系
Blog: https://blog.cuger.cn
Email: cug_xia@foxmail.com

## 赞助
![赞助](https://blog.cuger.cn/images/pay.jpg)
