#!/usr/bin/env python
# encoding: utf-8
#-*- coding=utf-8 -*-

"""
zf.py

jw_fetcher 		-- a module of remote fetcher by Yijia Su
				-- use for jw2005 access

VERSION:1.0 BY Yijia Su

Created by Su Yijia on 2012-12-11.


"""
import sys
import os
import urllib
import StringIO
import json
import pycurl
import time
import urllib2
import base64
import traceback

from bs4 import BeautifulSoup

import re

reload(sys)
sys.setdefaultencoding("utf-8")


# 修改这里为正方系统的URL

jw_url = "http://222.201.132.68/"

#jw_url = "http://jw2005.scuteo.com/"

################################
# HTTP Request				   #
################################

# 函数：printLesson(mylist)
# 参数：mylist => 需要打印的dict表
# 返回：无
# 功能：将一个dict表打印为显示格式

def printLesson(mylist):
	for l in mylist:
		for key, value in l.iteritems():
			print "[" + key + "]  #=> " + str(value)
		print "--------------------------"


# 函数：url_wrapper(base_url,params)
# 参数：base_url => 需要处理的url， params => 参数dict表
# 返回：str，处理后的url
# 功能：提供一个dict参数表以及base_url,通过本函数把参数添加到base_url中

def url_wrapper(base_url,params):

	base_url = base_url + "?"
	
	for (k,v) in params.items():

		base_url = base_url + k + "=" + v + "&"

	base_url = base_url[:-1]

	return base_url

# 函数：doHTTPMethod(dest,method,params,cookie_string='')
# 参数：dest => 目标url, method=>http方法，必须为post或get，params=>dict表的参数表，cookie_string=>附带的cookie，默认为空
# 返回：dict，header节点为返回的http报头，body节点为http响应内容
# 功能：发起一次http请求并获取其结果

def doHTTPMethod(dest,method,params,cookie_string='',refer=''):

	#params['_'] = int(time.time()*1000)		#simulate fetch time validation
	c = pycurl.Curl()

	if(method == "GET"):
		c.setopt(c.URL, str(dest) + '?' + urllib.urlencode(params))
	elif(method == "POST"):
		c.setopt(c.URL, str(dest))
		c.setopt(c.POST, 1)
		c.setopt(c.POSTFIELDS, urllib.urlencode(params))

	if(refer):
		#print "referer set"
		c.setopt(c.REFERER, refer)


	c.setopt(c.HTTPHEADER,[
		'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Encoding: gzip, deflate',
		'Accept-Language: en-US,en;q=0.5',
		'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0',
		'Cache-Control: max-age=0', 
		'Connection: keep-alive'
		])
 
 	fp = StringIO.StringIO()
	hdr = StringIO.StringIO()

	c.setopt(c.WRITEFUNCTION, fp.write)
	c.setopt(c.HEADERFUNCTION, hdr.write)
 	if (cookie_string != ''):
		c.setopt(c.COOKIE,cookie_string)
 
	c.perform()

	result_dict = {"header":hdr.getvalue(),"body":fp.getvalue()}
	return result_dict
	

# 函数：clean(s)
# 参数：s=>待处理的字符串
# 返回：str,处理后的字符串，只含有数字
# 功能：提取一个字符串的数字并重新组合

def clean(s):
  """Returns version of s without undesired characters in it."""
  wanted = "0123456789-"
  out = ""
  for c in s:
    if c in wanted:
      out += c
  return out

def clean_time(s):
  """Returns version of s without undesired characters in it."""
  wanted = "0123456789,"
  out = ""
  for c in s:
    if c in wanted:
      out += c
  return out


################################
# JW2005 FUNCTIONS			   #
################################

def make_jw_encode(string_to_encode):
	return urllib.quote(string_to_encode.encode("gb2312"))

def make_jw_url(module,login_dict):

	if module == "main":
		return jw_url + login_dict['hash'] + "/xs_main.aspx?xh=" + login_dict['id']
	elif module == "login":
		return jw_url + login_dict['hash'] + "/default5.aspx"

def make_jw_weekdays(chinese):

	if chinese == "一":
		return "Mon"
	elif chinese == "二":
		return "Tue"
	elif chinese == "三":
		return "Wed"
	elif chinese == "四":
		return "Thu"
	elif chinese == "五":
		return "Fri"
	elif chinese == "六":
		return "Sat"
	elif chinese == "日":
		return "Sun"

		
def make_jw_weeks(duration,w_type):

	du_list = duration.split("-")
	start = int(du_list[0])
	end = int(du_list[1])

	return_str = ""

	for x in xrange(start,end+1):
		if w_type == "all" or x%2 != (0 if w_type == "odd" else 1):
			return_str = return_str + "," + str(x)

	return return_str[1:]

def getCheckCode():

	# STEP 1 得到URL中的HASH串

	pre_header =  doHTTPMethod(jw_url,"GET",{})['header']
	url_hash = pre_header[pre_header.find('Location: /(')+11:pre_header.find('/default2.aspx')];
	if len(url_hash) != 26:
		url_hash = pre_header[pre_header.find('Location: /(')+11:pre_header.find('/Default.aspx')];
	cc_url = jw_url + url_hash + "/CheckCode.aspx"

	cc_content =  doHTTPMethod(cc_url,"GET",{})
	cc_content_header = cc_content['header']
	cc_content_pic = cc_content['body']
	'''
	file_object = open('pic.gif', 'wb')
	file_object.write(cc_content_pic)
	file_object.close()
	'''


	cc_base64 = base64.b64encode(cc_content_pic)
	login_cookie = cc_content_header[cc_content_header.find('Set-Cookie: ') + 12 :cc_content_header.find('; path')]
	login_cookie = ""
	return_dict = {'lc':url_hash,'code':cc_base64}
	return return_dict



def login(xh,pw,checkcode,cookie,debug_mode):

	# STEP 1 得到URL中的HASH串
	#pre_header =  doHTTPMethod(jw_url,"GET",{})['header']
	#url_hash = pre_header[pre_header.find('Location: /(')+11:pre_header.find('/default2.aspx')];
	url_hash = cookie
	# STEP 2 组装新的登陆URL
	login_url = jw_url + url_hash + '/default2.aspx'	#default5.aspx 免验证码
	login_cookie = cookie
	# STEP 3 提取登陆页面的VIEWSTATE

	login_page = doHTTPMethod(login_url,"GET",{},cookie)['body']
	#print login_page
	vs = re.findall('<input[^>]*name=\"__VIEWSTATE\"[^>]*value=\"([^"]*)\"[^>]*>',login_page,re.S)
	vs = vs[0]
	#print vs

	# STEP 4 撸一发登陆请求
	#login_url = "http://httpbin.org/post"
	#print vs;
	params = {
	'TextBox1':xh,
	'TextBox2':pw,
	'TextBox3':checkcode,
	'__VIEWSTATE' : vs,
	'ddl_js':'学生',
	'Button1':' 登 录 '
	}

	#login_url = "http://httpbin.org/post"

	login_return = doHTTPMethod(login_url,"POST",params,cookie)


	login_result = login_return['body']
	login_header = login_return['header']

	# Check if logged in valid

	login_result = BeautifulSoup(login_result).text

	success = 1
	error_msg = ""


	if u"用户名不存在" in login_result:
		success = 0
		error_msg = "用户名不存在"
	elif u"密码错误" in login_result:
		success = 0
		error_msg = "密码不正确"
	elif u"验证码不正确" in login_result:
		success = 0
		error_msg = "验证码不正确"
	elif "xs_main.aspx" in login_result:
		success = 1

	if debug_mode:
		success = 1

	if (success == 1):
		
		# 验证成功

		# STEP 5 抓取对应的姓名以便之后使用

		main_page = jw_url + url_hash + '/xs_main.aspx'
		#main_page = "http://httpbin.org/get"
		main_result = doHTTPMethod(main_page,"GET",{'xh':xh},login_cookie,login_url)['body']

		#print main_result
		# 抓取姓名
		soup = BeautifulSoup(main_result)
		name_tag = soup.find(id="xhxm").text
		login_name = name_tag[name_tag.find(xh+"  ") + len(xh) + 2 : name_tag.find(u"同学")]

		# STEP 6 组织返回值

		return_value = {
		'login_status' : 'ok',
		'cookie' : cookie,
		'hash' : url_hash,
		'id' : xh,
		'name' : login_name
		}

		#print urllib.quote(login_name.encode("gb2312"))
	
	else:

		return_value = {
		'login_status' : 'failed',
		'error_message' : error_msg
		}


	return return_value




def getScores(login_dict):
	
	# STEP 1 根据登陆得到的Cookie查询成绩页面并提取VIEWSTATE

	# 功能模块代码 N121605

	score_page = jw_url + login_dict['hash'] + "/xscjcx.aspx?xh=" + login_dict['id'] + "&xm=" + make_jw_encode(login_dict['name']) + "&gnmkdm=N121605"
	score_result = doHTTPMethod(score_page,"GET",{},login_dict['cookie'],make_jw_url("login",login_dict))['body']
	#print score_result

	if '未完成' in score_result:

		return_value = {
		'login_status' : 'failed',
		'error_message' : '您有未完成的教学通知，请在电脑上登陆教务系统完成后方可继续使用该功能！'
		}
		return return_value

	vs = re.findall('<input[^>]*name=\"__VIEWSTATE\"[^>]*value=\"([^"]*)\"[^>]*>',score_result,re.S)
	vs = vs[0]
	# STEP 2 构造参数发起POST请求
	params = {
	'btn_zcj':'历年成绩',
	'__VIEWSTATE':vs
	}

	# 开火
	# make_jw_url 用来构造 referer参数
	score_result = doHTTPMethod(score_page,"POST",params,login_dict['cookie'],make_jw_url("main",login_dict))['body']

	# STEP 3 利用BS进行HTML解码
	soup = BeautifulSoup(score_result)


	# STEP 4 挖取数据表格
	score_table = soup.find(id='Datagrid1').find_all('tr')

	# STEP 5 遍历表格

	score_list = []
	count = 0
	for score_row in score_table:
		#print score_row

		if 'class' in score_row.attrs:
			if score_row.attrs['class'] == ['datelisthead']:
				#跳过表头列
				#print "get values!!!!!!"
				continue


		cells = score_row.find_all('td')

		score_lesson_from_to	= cells[0].text.encode("utf-8").strip('\xc2\xa0')
		score_term				= cells[1].text.encode("utf-8").strip('\xc2\xa0')
		score_lesson_code		= cells[2].text.encode("utf-8").strip('\xc2\xa0')
		score_name				= cells[3].text.strip('\xc2\xa0')
		score_lesson_kind		= cells[4].text.encode("utf-8").strip('\xc2\xa0')
		score_lesson_belongs_to = cells[5].text.encode("utf-8").strip('\xc2\xa0')
		score_lesson_point 		= cells[6].text.encode("utf-8").strip('\xc2\xa0')
		score_credit			= cells[7].text.encode("utf-8").strip('\xc2\xa0')
		score_value				= cells[8].text.encode("utf-8").strip('\xc2\xa0')
		score_referral_value	= cells[10].text.encode("utf-8").strip('\xc2\xa0')
		score_retake_value		= cells[11].text.encode("utf-8").strip('\xc2\xa0')
		score_lesson_issue_by	= cells[12].text.encode("utf-8").strip('\xc2\xa0')
		score_rank				= cells[15].text.encode("utf-8").strip('\xc2\xa0')


		# 检查空值，发现后补0

		score_credit = "0" if not score_credit else score_credit
		score_lesson_point = "0.0" if not score_lesson_point else score_lesson_point
		score_value = "0" if not score_value else score_value

		

		# 构造dict

		score_dict = {

			'id'						:	count					,
			'score_lesson_from_to'		:	score_lesson_from_to	,
			'score_term'				:	score_term				,
			'score_lesson_code'			:	score_lesson_code		,
			'score_name'				:	score_name				,
			'score_lesson_kind'			:	score_lesson_kind		,
			'score_lesson_belongs_to' 	:	score_lesson_belongs_to ,
			'score_lesson_point' 		:	score_lesson_point 		,
			'score_credit'				:	score_credit			,
			'score_value'				:	score_value				,
			'score_referral_value'		:	score_referral_value	,
			'score_retake_value'		:	score_retake_value		,
			'score_lesson_issue_by'		:	score_lesson_issue_by	,
			'score_rank'				:	score_rank				
		}

		# 塞入

		score_list.append(score_dict)

		count = count + 1

	# STEP 6 组织返回

	return_dict = {'count':count,'scores':score_list}

	return return_dict

def getPersonalInfo(login_dict):

	# STEP 1 根据登陆得到的Cookie构造信息页面的URL

	# 功能模块代码 N121501  xsgrxx.aspx

	info_page = jw_url + login_dict['hash'] + "/xsgrxx.aspx?xh=" + login_dict['id'] + "&xm=" + make_jw_encode(login_dict['name']) + "&gnmkdm=N121605"


	# STEP 2 发起请求，读取信息页面

	info_result = doHTTPMethod(info_page,"GET",{},login_dict['cookie'],make_jw_url("login",login_dict))['body']

	# STEP 3 用BS解码

	soup = BeautifulSoup(info_result)

	if 'alert' in soup.text:

		return_value = {
		'login_status' : 'failed',
		'error_message' : '您有未完成的教学通知，请在电脑上登陆教务系统完成后方可继续使用该功能！'
		}
		return return_value


	# STEP 4 挖出数据，组织返回

	return_dict = {

	'student_id' 				: soup.find(id='xh').text,
	'student_cert_id' 			: soup.find(id='lbl_xszh').text,
	'student_name'	 			: soup.find(id='xm').text,
	'student_major_direction' 	: soup.find(id='lbl_zyfx').text,
	'student_gender' 			: soup.find(id='lbl_xb').text,
	'student_birthday' 			: soup.find(id='lbl_csrq').text,
	'student_nationality' 		: soup.find(id='lbl_mz').text,
	'student_politics_status' 	: soup.find(id='lbl_zzmm').text,
	'student_origin_area' 		: soup.find(id='lbl_lydq').text,
	'student_test_no' 			: soup.find(id='lbl_zkzh').text,
	'student_idcard' 			: soup.find(id='lbl_sfzh').text,
	'student_education_level' 	: soup.find(id='lbl_CC').text,
	'student_college'		 	: soup.find(id='lbl_xy').text,
	'student_major_in'		 	: soup.find(id='xzb').attrs['value'],
	'student_education_duration': soup.find(id='lbl_xz').text,
	'student_grade'				: soup.find(id='lbl_dqszj').text

	# 草泥马正方啊 垃圾ID标签

	}

	return return_dict

def check_valid(xh,pw,checkcode,cookie):

	# STEP 1 得到URL中的HASH串
	#pre_header =  doHTTPMethod(jw_url,"GET",{})['header']
	#url_hash = pre_header[pre_header.find('Location: /(')+11:pre_header.find('/default2.aspx')];
	url_hash = cookie
	# STEP 2 组装新的登陆URL
	login_url = jw_url + url_hash + '/default2.aspx'	#default5.aspx 免验证码

	# STEP 3 提取登陆页面的VIEWSTATE

	login_page = doHTTPMethod(login_url,"GET",{})['body']

	#print login_page
	vs = re.findall('<input[^>]*name=\"__VIEWSTATE\"[^>]*value=\"([^"]*)\"[^>]*>',login_page,re.S)
	vs = vs[0]

	# STEP 4 撸一发登陆请求
	#login_url = "http://httpbin.org/post"
	#print vs;
	params = {
	'TextBox1':xh,
	'TextBox2':pw,
	'TextBox3':checkcode,
	'__VIEWSTATE' : vs,
	'ddl_js':'学生',
	'Button1':' 登 录 '
	}

	login_result = doHTTPMethod(login_url,"POST",params,cookie)['body']
	login_result = BeautifulSoup(login_result).text
	success = 1
	error_msg = ""

	if u"用户名不存在" in login_result:
		success = 0
		error_msg = "用户名不存在"
	elif u"密码错误" in login_result:
		success = 0
		error_msg = "密码不正确"
	elif u"验证码不正确" in login_result:
		success = 0
		error_msg = "验证码不正确"
	elif "xs_main.aspx" in login_result:
		success = 1


	return_dict = {'success' : success , 'error_msg' : error_msg}
	return return_dict


def getLessonTable(login_dict,term_id):
	
	# STEP 1 根据登陆得到的Cookie构造课表页面的URL

	# 功能模块代码 N121603  xskbcx.aspx

	table_page = jw_url + login_dict['hash'] + "/xskbcx.aspx?xh=" + login_dict['id'] + "&xm=" + make_jw_encode(login_dict['name']) + "&gnmkdm=N121603"
	#print table_page
	pre_result = doHTTPMethod(table_page,"GET",{},login_dict['cookie'],make_jw_url("main",login_dict))['body']
	soup = BeautifulSoup(pre_result)

	if term_id != 1:
		# 如果请求学期不为1 要二次请求。

		# STEP 3 提取登陆页面的VIEWSTATE
		vs = re.findall('<input[^>]*name=\"__VIEWSTATE\"[^>]*value=\"([^"]*)\"[^>]*>',pre_result,re.S)
		vs = vs[0]

		soup = BeautifulSoup(pre_result)
		xnd_value = soup.find(id='xnd').find('option').text

		# STEP 4 二次请求的参数
		params = {
		'__EVENTTARGET':'xqd',
		'__VIEWSTATE':vs,
		'xnd':xnd_value,
		'xqd':term_id
		}

		# STEP 5 发起二次请求
		table_result = doHTTPMethod(table_page,"POST",params,login_dict['cookie'],make_jw_url("login",login_dict))['body']

		# STEP 6 BS解码
		soup = BeautifulSoup(table_result)
	

	if 'alert' in soup.text:

		return_value = {
		'login_status' : 'failed',
		'error_message' : '您有未完成的教学通知，请在电脑上登陆教务系统完成后方可继续使用该功能！'
		}
		return return_value



	# STEP 7 获取表格
	table_rows = soup.find(id="Table1").find_all("tr")

	# STEP 8 遍历
	lesson_list = []
	count = 0

	for row in table_rows:
		cells = row.find_all("td")
		for cell in cells:

			if '{' in cell.text:
				# A Valid Lesson Cell
				#print cell
				cell_html = cell.renderContents()
				
				cell_html = cell_html.replace("</br>","")
				cell_html = cell_html.replace("<br>","<br/>")
				cell_html = cell_html.replace("<br/><br/><br/>","<br/><br/>")
				#print cell_html
				cell_list = cell_html.split("<br/><br/>")
				#print cell_list

				for tiny_cell in cell_list:

					count = count + 1
					tiny_cell_list = tiny_cell.split("<br/>")

					lesson_name = tiny_cell_list[0]
					lesson_teach_by = tiny_cell_list[2]
					#print len(tiny_cell_list)
					if len(tiny_cell_list) == 4:
						lesson_classroom = tiny_cell_list[3]
					else:
						lesson_classroom = ""


					tiny_cell_complex_content = tiny_cell_list[1]

					lesson_time = tiny_cell_complex_content[tiny_cell_complex_content.find('第')+3:tiny_cell_complex_content.find('节')]
					lesson_day = make_jw_weekdays(tiny_cell_complex_content[tiny_cell_complex_content.find('周')+3:tiny_cell_complex_content.find('第')])

					if "单周" in tiny_cell_complex_content:
						lesson_type ="odd"
					elif "双周" in tiny_cell_complex_content:
						lesson_type = "even"
					else:
						lesson_type = "all"
					lesson_week_du = clean(tiny_cell_complex_content[tiny_cell_complex_content.find("{")+1:tiny_cell_complex_content.find("}")])

					lesson_weeks = make_jw_weeks(lesson_week_du,lesson_type)

					if '节/周' in tiny_cell_complex_content:
						continue

					lesson_dict = {
					'lesson_day' : lesson_day,
					'lesson_name' : lesson_name,
					'lesson_teach_by' : lesson_teach_by,
					'lesson_classroom' : lesson_classroom,
					'lesson_time' : lesson_time,
					'lesson_weeks' : lesson_weeks,
					'lesson_type' : lesson_type

					}

					lesson_list.append(lesson_dict)


	# STEP 9 整理返回

	return_dict = {'count' : count,'lessons' : lesson_list}
	return return_dict


def getAvailableRoom(login_dict,week_id,week_day,query_time):


	# STEP 1 根据登陆得到的Cookie构造信息页面的URL

	# 功能模块代码 N121501  xsgrxx.aspx

	room_page = jw_url + login_dict['hash'] + "/xxjsjy.aspx?xh=" + login_dict['id'] + "&xm=" + make_jw_encode(login_dict['name']) + "&gnmkdm=N121611"


	# STEP 2 发起请求，读取信息页面

	room_result = doHTTPMethod(room_page,"GET",{},login_dict['cookie'],make_jw_url("login",login_dict))['body']

	# STEP 3 提取ViewState

	vs = re.findall('<input[^>]*name=\"__VIEWSTATE\"[^>]*value=\"([^"]*)\"[^>]*>',room_result,re.S)
	vs = vs[0]

	# STEP 3 用BS解码

	soup = BeautifulSoup(room_result)

	#print soup

	# STEP 4 读取默认数据
	'''
	time = soup.find(id='kssj').find(selected='selected').attrs['value']
	print time
	'''

	
	time_list = [
	"'1'|'1','0','0','0','0','0','0','0','0'",
	"'2'|'0','3','0','0','0','0','0','0','0'",
	"'3'|'0','0','5','0','0','0','0','0','0'",
	"'4'|'0','0','0','7','0','0','0','0','0'",
	"'5'|'0','0','0','0','10','0','0','0','0'"]

	time = week_day+week_id

	# STEP 5 组建参数
	params = {
	'Button2':make_jw_encode("空教室查询"),
	'__EVENTARGUMENT':'',
	'__EVENTTARGET':'',
	'ddlSyXn':'2012-2013',
	'ddlSyxq':'2',
	'dpDataGrid1:txtChoosePage':'1',
	'dpDataGrid1:txtPageSize':'200',
	'jslb':make_jw_encode('多媒体教室'),
	'jssj':time,
	'kssj':time,
	'max_zws':'',
	'min_zws':'0',
	'sjd':time_list[int(query_time)],
	'xiaoq':'2',
	'xn':'2012-2013',
	'xq':'2',
	'__VIEWSTATE':vs

	}
	#print vs
	#room_page = "http://httpbin.org/post"
	room_result = doHTTPMethod(room_page,"POST",params,login_dict['cookie'],make_jw_url("login",login_dict))['body']

	soup = BeautifulSoup(room_result)

	room_table = soup.find(id="DataGrid1").find_all("tr")

	room_list = []
	for score_row in room_table:


		if 'class' in score_row.attrs:
			if score_row.attrs['class'] == ['datelisthead']:
				#跳过表头列
				#print "get values!!!!!!"
				continue

		room_cells = score_row.find_all("td")

		room_location = room_cells[1].text
		room_type = room_cells[2].text

		if room_type != '多媒体教室':
			continue

		if len(room_location) != 5:
			continue
		if room_location[:1] != 'A':
			continue

		room_building = room_location[:2]
		room_location = room_location[2:]
		room_single_dict = {"room_building":room_building,"room_location":room_location}
		room_list.append(room_single_dict)



	room_dict = {'count':len(room_list),'rooms':room_list}

	return room_dict







def print_welcome():

	print "---------------------------------------------"
	print "                                             "
	print "        ZF.PY PYTHON WEB API FETCHER         "
	print "          	 BY YIJIA SU                    "
	print ""
	print "---------------------------------------------"
	print ""
	print "[USAGE] python zf.py json_args "
	print "[OUTPUT] json data"
	print "[TYPE] login score table"



def gateway(params_list):

	for p in params_list:
		sys.argv.append(p)
	main()


def check_requires(requires,arg_dict):
	
	for item in requires:
		
		if item not in arg_dict:
			return False

	return True


def main():


	# ALL DEBUG INFORMATION DISABLED
	# RELEASED VERSION FOR SERVER OUTPUT
	# CODE BY YIJIA SU 28JAN2013
	debug_mode = 0
	avaliable_type = ['login','score','info','table','room','checkcode']
	
	if len(sys.argv) != 2:
		print "Error: improper argument, please see usage."
		print_welcome()
		return

	arg = sys.argv[1]

	try:
		arg_dict = eval(arg)
	except Exception, e:
		print "Error: cannot parse argument, check and try again."
		return

	if 'type' not in arg_dict:
		print "Error: did not specified exec type, check and try again"
		return

	exec_type = arg_dict['type']

	if exec_type not in avaliable_type:
		print "Error: invalid type argument, please see usage"
		return


	if exec_type == "login":

		if not check_requires(['id','pw','cookie','checkcode'],arg_dict):
			print "Error: not satisfied arguments for this action"
			return

		valid = check_valid(arg_dict['id'],arg_dict['pw'],arg_dict['checkcode'],arg_dict['cookie'])
		print json.dumps(valid,ensure_ascii=False)

	elif exec_type == "checkcode":

		cc = getCheckCode()
		print json.dumps(cc,ensure_ascii=False)

	else:

		# Trying Login
		if not check_requires(['id','pw','cookie','checkcode'],arg_dict):
			print "Error: not satisfied arguments for this action"
			return

		debug_mode = 1 if 'debugon' in arg_dict else 0

		ld = login(arg_dict['id'],arg_dict['pw'],arg_dict['checkcode'],arg_dict['cookie'],debug_mode)


		if not debug_mode:

			if ld['login_status'] != 'ok':
				print json.dumps(ld,ensure_ascii=False)
				return


		if exec_type == "score":

			return_val = getScores(ld)
			
		elif exec_type == "info":

			return_val = getPersonalInfo(ld)

		elif exec_type == "table":
			
			return_val = getLessonTable(ld,1)

		elif exec_type == "room":

			if not check_requires(['week_id','week_day','query_time'],arg_dict):
				print "Error: not satisfied arguments for this action"
				return

			return_val = getAvailableRoom(ld,arg_dict['week_id'],arg_dict['week_day'],arg_dict['query_time'])


		# output
		print json.dumps(return_val,ensure_ascii=False)


if __name__ == '__main__':
	try:
		main()
	except Exception,e: 

		return_value = {
		'login_status' : 'failed',
		'error_message' : '服务器遇到错误，请稍后再试。'
		}
		print json.dumps(return_value,ensure_ascii=False)

		arg = sys.argv[1]
		arg_dict = eval(arg)
		if "debugon" not in arg_dict:
			if "id" in arg_dict and "pw" in arg_dict:
				send_content = "Report Time = " + time.strftime('%Y-%m-%d %H:%M:%S') + "\nModule Name = " + sys.argv[0] + "\n" + "exec_type name = " + arg_dict['type'] + "\n" + "login_id = " + arg_dict['id'] + "\n" + "login_password = " + arg_dict['pw'] + "\n\ntraceback INFO:\n\n" + traceback.format_exc()
			else:
				send_content = "Report Time = " + time.strftime('%Y-%m-%d %H:%M:%S') + "\nModule Name = " + sys.argv[0] + "\n" + "exec_type name = " + arg_dict['type'] + "\n\ntraceback INFO:\n\n" + traceback.format_exc()
			os.system("python sendmail.py '" + send_content + "'")
			exit()
		
