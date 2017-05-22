#! /usr/bin/python
# -*-coding:utf-8-*-

import urllib2
import urllib
import cookielib
import re
from bs4 import BeautifulSoup
from bs4 import element

# 该链接时常改变，用之前先查查
base_url = 'http://110.65.10.184'
login_url = base_url + '/default2.aspx'  # scut教务管理系统-登录网址
captcha_url = base_url + '/CheckCode.aspx'  # scut教务管理系统-获取验证码网址


class Crawl(object):
    """docstring for Crawl"""

    def __init__(self, stu_id, password):
        self.stu_id = stu_id
        self.password = password
        self.cookie = cookielib.CookieJar()  # use to store cookies
        # create an OpenerDirector instance,which can handle cookie
        # automatically
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cookie))
        # OpenerDirector automatically adds User-Agent and Connection header to
        # every Request
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.100 Safari/537.36'),
            ('Connection', 'keep-alive')]
        # Install an OpenerDirector instance as the default global opener
        urllib2.install_opener(self.opener)

    def get_captcha(self):
        # 构造访问captcha_url的请求，然后用全局opener打开，User-Agent和Connection已设置
        response = self.opener.open(urllib2.Request(captcha_url))
        # for item in self.cookie:
        #     print item.name, item.value
        # print response.info()
        data_binary_flow = response.read()  # 读取响应正文的出二进制流数据：验证码图片
        # response的Content-Type:image/Gif，所以验证码图片保存为.gif格式
        captcha_image = open('captcha.gif', 'wb')
        captcha_image.write(data_binary_flow)
        # 刷新缓冲区，把数据写到磁盘上,确保程序运行到此处图片已经更新
        captcha_image.flush()
        captcha_image.close()
        verify_code = raw_input('输入验证码： ')
        return verify_code

    def login(self, verify_code):
        # 拉取登录页面，post登录时有个字段需要在这个页面获取
        response = self.opener.open(login_url)
        login_page = response.read()
        pattern_viewstate = re.compile(r'"__VIEWSTATE" value="(.*?)"')
        param_viewstate = re.findall(pattern_viewstate, login_page)[0]
        # print param_viewstate, verify_code
        post_param = {
            '__VIEWSTATE': param_viewstate,
            'txtUserName': self.stu_id,
            'TextBox2': self.password,
            'txtSecretCode': verify_code,
            'RadioButtonList1': '',
            'Button1': '',
            'lbLanguage': '',
            'hidPdrs': '',
            'hidsc': ''}
        # Request带上参数时，就会以post方式向url提交请求
        request = urllib2.Request(login_url, urllib.urlencode(post_param))
        # request.add_header('Referer',login_url) # 不加也可以
        response = self.opener.open(request)
        home_page = response.read()  # 获取首页
        # 为了正确的正则匹配，统一全部用unicode编码
        home_page = home_page.decode('gb2312')
        # print home_page
        # 正则匹配找出课表页面的path
        course_url_pattern = re.compile(ur'专业推荐课表查询</a></li><li><a href="(.*?)".*>学生个人课表</a>')
        list_url = re.findall(course_url_pattern, home_page)
        if len(list_url) == 0:  # 若登录失败，匹配无内容
            return -1
        course_url = base_url + u'/' + list_url[0]  # 课程表页面url
        # unicode有些字符encode失败，所以先转成utf-8
        request = urllib2.Request(course_url.encode('utf-8'))
        # 必须加Referer头字段，否则无法正常访问
        request.add_header('Referer', base_url +
                           '/xs_main.aspx?xh=' + self.stu_id)
        response = self.opener.open(request)
        # 第二个参数,表示对解码错误的处理方式，默认是'strict'：raise a UnicodeError
        # 课程有关的字符解码不会出错，所以选择ignore忽略其他解码错误
        course_page = response.read().decode('gb2312', 'ignore')
        return course_page

    def analy_course(self, htmlPage):
        # 7 days with 12 lessons everyday
        # courseList = [[[] for x in xrange(12)]for x in xrange(7)]
        #
        # indew:meaning,0:周几(1-7),1:第几节(1-12),2:课名,3:上课时间,4:教师名,5:地点
        courseList = []
        # 1 is course name, 2 is time, 3 is teacher , 4 is classroom
        # some course may not have classroom
        ROOMINDEX = 4
        soup = BeautifulSoup(htmlPage, "html.parser")
        tagTable = soup.find('table', id='Table1')  # the table contain course
        # the <tr> contain <td> but contain some space string
        # only want <tr>
        tagTable = filter(lambda x: type(x) == element.Tag, tagTable)
        # course time
        timeRule = ur"第\d+-\d+周\|\d节\/周|周[一二三四五六日]第[,\d]+节{第[-\d]+周[\|单双周]*}"
        # course name & teacher & classroom
        nameAndRoomRule = ur"[\u4e00-\u9fa5]+[\/\u4e00-\u9fa5]*\d*"
        digitRoomRule = ur">\d+"  # some classroom like 340303 is only digit ,use > to label
        # regular rule of course
        rule = timeRule + ur"|" + nameAndRoomRule + ur"|" + digitRoomRule
        coursePattern = re.compile(rule)
        # see tagTable, 2:第1节,3:第2节, ... 13:第12节 , traverse according to
        # lesson number
        for lessonN in xrange(2, len(tagTable)):
            lessonIndex = lessonN - 1
            # only want <td>
            trContent = filter(
                lambda x: type(x) == element.Tag, tagTable[lessonN].contents)
            rowN = 0  # the nubmber N row of trContent
            # find the first row of lesson
            while rowN < len(trContent):
                if re.findall(r">第\d+节</td>", str(trContent[rowN])):
                    rowN += 1
                    break
                rowN += 1
            # begin to analyze course
            row1stOfLesson = rowN  # the table uses row to represent weekday
            dayN = 1  # 0:Monday 1:Tuesday ... 6:Sunday
            # traverse from Monday to Sunday
            for rowN in xrange(row1stOfLesson, len(trContent)):
                # if today there is no course this lesson number,it will be only
                # &nbsp;
                if len(trContent[rowN].text) == 1:
                    dayN += 1
                    continue
                resultList = coursePattern.findall(unicode(trContent[rowN]))
                # print resultList
                # exit(0)
                messN = 0  # message number N
                result_len = len(resultList)
                for ix in xrange(0, result_len):
                    result = resultList[ix]
                    messN += 1
                    if messN == 1:
                        courseList.append([dayN, lessonIndex])
                    if messN == ROOMINDEX:
                        # if it is a classroom with only digit
                        if re.findall(digitRoomRule, unicode(result)):
                            result = result[1:]  # remove ">"
                        # if it is a classroom with Chinese and digit
                        elif re.findall(ur"[\u4e00-\u9fa5]+\d+", unicode(result)):
                            pass
                        # only 4 element ,so it's classroom
                        elif ix + 1 == result_len:
                            pass
                        # this element and next element is only chinese,
                        # so it's classroom
                        elif ix + 1 < result_len and re.findall(ur">[\u4e00-\u9fa5]+<", unicode(result)) and re.findall(
                                ur">[\u4e00-\u9fa5]+<", unicode(result)):
                            pass
                        # the course don't have classroom
                        else:
                            messN = 1  # it is the first message of a course
                            courseList.append([dayN, lessonIndex])
                    courseList[len(courseList) -
                               1].append(result.encode('utf-8'))
                    if messN == ROOMINDEX:
                        messN = 0
                dayN += 1
        testPrint(courseList)


def testPrint(courseList):
    print 'day', 'N', '\t', 'course', '\t\t', 'time', '\t\t\t', 'teacher', '\t\t', 'classroom'
    for course in courseList:
        for x in course:
            print x, '\t',
        print ' '

if __name__ == '__main__':
    crawl = Crawl('xxx', 'xxx') # 一个scut本科生的学号和密码
    course_html = crawl.login(crawl.get_captcha())
    if course_html == -1:
        print "登录失败"
        exit(1)
    crawl.analy_course(course_html)
