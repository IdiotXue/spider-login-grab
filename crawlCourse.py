#! /usr/bin/python
# -*-coding:utf-8-*-

import urllib2
import cookielib
# import urllib

# 该链接时常改变，用之前先查查
login_url = 'http://110.65.10.184/default2.aspx'  # scut教务管理系统-登录网址
captcha_url = 'http://110.65.10.184/CheckCode.aspx'  # scut教务管理系统-获取验证码网址


class Crawl(object):
    """docstring for Crawl"""

    def __init__(self, stu_id, password):
        self.stuId = stu_id
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
        # response的Content-Type:image/Gif，所以保存为.gif格式
        captcha_image = open('captcha.gif', 'wb')
        captcha_image.write(data_binary_flow)
        captcha_image.flush()  # 刷新缓冲区，把数据写到磁盘上
        captcha_image.close()



if __name__ == '__main__':
    crawl = Crawl('xxx', 'xxx')
    crawl.get_captcha()
