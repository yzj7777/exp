# exp - 命令行记账本

一个在终端里用的记账小工具。

## 用法

添加一笔消费：
    exp add 35.5 午餐 "公司楼下面馆"

查看本月所有记录：
    exp list

查看某个月的记录：
    exp list --month 2024-06

按类别统计本月消费：
    exp summary

导出为 CSV 文件：
    exp export report.csv

## 数据存储

所有数据保存在用户主目录下的 .exp.json 文件中。