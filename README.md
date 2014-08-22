openzf
======

an open-source project of zhengfang(正方教务系统) web scraper

一套用于抓取正方教务系统数据的Python脚本

1）说明

这是一套利用Python抓取正方教务系统脚本，目前支持正方系统的成绩、课表、个人信息、登陆等操作。

2）依赖组件

BeautifulSoup pycurl

Python版本2.6以上

3) 如何使用？

抓取成绩：

python zf.py '{"type":"score","id":"学号","pw":"密码"}'

抓取课表：

python zf.py '{"type":"table","id":"学号","pw":"密码"}'

4) 支持的学校列表

1.华南理工大学

其他学校还未做测试

5）其他说明

这套代码主要是为了抛砖引玉，代码质量实在不怎么样，希望各路大神在本套代码的基础之上进行完善~
本人由于工作原因无法及时更新Github，有任何问题请通过email联系我。
