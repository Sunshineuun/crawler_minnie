#!/usr/bin/env python
# encoding: utf-8
# qiushengming-minnie
"""
爬虫机器人
"""
import datetime
import json
from urllib import request, error, parse
from selenium import webdriver

from minnie.common import mlogger

logger = mlogger.get_defalut_logger('crawler.log', 'crawler')


def getHttpStatus(browser):
    """
    字典值：url,status,statusText
    :param browser:
    :return:
    """
    for responseReceived in browser.get_log('performance'):
        try:
            response = json.loads(responseReceived[u'message'])[u'message'][u'params'][u'response']
            if response['status'] is not '200':
                return False
        except BaseException as e:
            logger.error(e)

    return True


class Crawler(object):
    """
    1.网络异常
    2.driver怎么判断请求成
    """

    def __init__(self, urlpool, mongo):
        self.urlpool = urlpool
        self.cursor = mongo.get_cursor('minnie', urlpool.url_name)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0',
        }

        # 驱动器地址
        executable_path = 'D:\\Tech\\Tool\\chromedriver\\chromedriver.exe'

        options = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}

        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(executable_path=executable_path,
                                       chrome_options=options)
        self.driver.set_window_size(width=100, height=100)

        # 代理设置
        # proxy = request.ProxyHandler({'http': '5.22.195.215:80'})  # 设置proxy
        # opener = request.build_opener(proxy)  # 挂载opener
        self.opener = request.build_opener(request.HTTPHandler)
        request.install_opener(opener=self.opener)

    def driver_get_url(self, url, check_rule=None):
        """
        selenium方式请求，浏览器\n
        请求成功更新url；存储响应的html界面
        :param check_rule:
        :param url: 字符串类型\n
        :return: 长文本
        """
        self.driver.get(url)

        if not getHttpStatus(self.driver):
            return False

        index = 4
        # 规则存在执行校验规则
        if check_rule:
            # 校验规则出现三次错误则退出，并且返回False
            while check_rule(self.driver.page_source):
                index -= 1
                if index < 0:
                    return False
        result = self.driver.page_source
        self.update_success_url(url)
        return result

    def request_get_url(self, url, params=None):
        """
        request方式请求\n
        :param url: 字符串格式\n
        :param params: 字典格式\n
        :return: 长文本，或者也可以返回response，建议长文本吧
        """
        data = None
        if params:
            data = parse.urlencode(params).encode('utf-8')

        r = request.Request(url=url, headers=self.headers, data=data)
        response = None

        try:
            response = self.opener.open(r)
        except error.HTTPError as e:
            logger.error(u'HTTPError，错误代码{code}'.format(code=e.code))
            logger.error(e.read().decode('utf-8'))
        except error.URLError as e:
            logger.error(u'URLError，错误提示{reason}'.format(reason=e.reason))
        except ConnectionResetError as e:
            logger.error(e)

        if response is None:
            return
        else:
            self.update_success_url(url)
            # .decode('UTF-8')
            return response.read()

    def update_success_url(self, url):
        if self.cursor.find({'url': url}).count() > 0:
            self.cursor.update({
                'url': url
            }, {
                '$set': {
                    'isenable': '0'
                }
            })

    def get_driver(self):
        return self.driver
