'''
#######################################################
author:Ming Nie
date : 2018-04-20
pre: pip install selenium sqlalchemy pymysql
     yum install firefox mariadb
database:
MariaDB [kcs]> desc kcs;
+-------------+---------------+------+-----+---------+-------+
| Field       | Type          | Null | Key | Default | Extra |
+-------------+---------------+------+-----+---------+-------+
| id          | int(11)       | NO   | PRI | NULL    |       |
| title       | varchar(512)  | YES  |     | NULL    |       |
| environment | varchar(1024) | YES  |     | NULL    |       |
| issue       | text          | YES  |     | NULL    |       |
| res         | text          | YES  |     | NULL    |       |
| rc          | text          | YES  |     | NULL    |       |
| ds          | text          | YES  |     | NULL    |       |
| private     | text          | YES  |     | NULL    |       |
+-------------+---------------+------+-----+---------+-------+
8 rows in set (0.00 sec)

Useage: change username,password,mysql connection,start,stop 
        #python3.6 sel.py
        enjoy it :)

已知Bug: 
         1.由于sqlalchemy 仅作为ORM需要调用pymysql,但是pymsql中默认使用latin-1编码，造成编码异常。由于时间较紧没有进一步查找传参的办法临时修改了pymysql
         的库文件，强行指定utf-8编码。

概述：
      1.此脚本使用selenium来直接通过webdriver调用firefox来进行爬取红帽KCS，由于页面中验证较多直接处理post请求较麻烦所以使用此方法，好在总数据量不大。
      2.数据库方面使用mysql作为存储数据库，依据页面内容使用8个字段(kcs id, 标题，环境，问题，解决方案，根本原因，分析步骤，私有内容 )。链接使用pymysql+sqlalchemy
      3.脚本能够自动处理一段时间后自动验证密码问题，解决方法为抛异常自动重新登陆。能够自动处理一段时间后kcs列表hang死问题，解决方案为300秒返回空列表销毁浏览器对象并重新登陆。
      4.部分情况下红帽门户会出现无法登陆的情况，脚本依旧能够自动处理，解决方案任然是抛出异常自动重启。
      5.本脚本能够自动跳过已经入库的kcs，依据kcs的id来进行判断。
      6.默认情况下当出现连续10次登陆失败则主动退出，可能的原因为账户异常或者门户异常。
      7.使用脚本时请配置翻墙或者内部系统代理，否则速度可能会降低90%。
      8.脚本在爬取完成start到stop之内的所有kcs之后会自动退出exit(100)。
      9.此脚本不会更新，随意使用，任何问题概不负责。
##########################################################
'''
from selenium import webdriver
import time
from selenium.common import exceptions
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, ForeignKey,String,Column,VARCHAR,Text
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from selenium.webdriver.common.proxy import *
from sqlalchemy.sql import select
import sys
Base = declarative_base()


class kcs(Base):
    __tablename__ = 'kcs'
    id = Column(Integer,primary_key=True)
    title = Column(VARCHAR)
    environment = Column(VARCHAR)
    issue = Column(VARCHAR)
    res= Column(Text)
    rc = Column(Text)
    ds = Column(Text)
    private = Column(Text)


class sel:
    def __init__(self,startpage=0, stop=0):
        self.browser = webdriver.Firefox(proxy=proxy)
        self.browser.set_page_load_timeout(300)
        ############# login here ######################
        self.username = '<your username here>'
        self.password = '<your password here>'
        ###############################################
        self.kcs_list_url = 'https://access.redhat.com/solutions?title=&product=25&category=All&state=All&kcs_state=All&language=en&field_internal_tags_tid=All'
        if startpage == 0:
            self.walkpage = ''
        else:
            self.walkpage = str(startpage)
        self.stop = str(stop)
        ############# mysql connect ##################
        self.engine = create_engine("mysql+pymysql://root:redhat@<your mysql ip>/kcs", echo=True)
        ##############################################
        Session_class = sessionmaker(bind=self.engine)
        self.Session = Session_class()

    def login(self):
        self.browser.get('https://access.redhat.com')
        time.sleep(2)
        login_btn = self.browser.find_element_by_id('home-login-btn')
        login_btn.click()
        time.sleep(3)
        self.browser.find_element_by_id('username').send_keys(self.username)
        self.browser.find_element_by_id('password').send_keys(self.password)
        login_btn2 = self.browser.find_element_by_id('_eventId_submit')
        login_btn2.click()

    def getkcslist(self):
        got_list = []
        if self.walkpage != '':
            url = self.kcs_list_url+'&page='+self.walkpage
        else:
            url = self.kcs_list_url
        self.browser.get(url)
        ids = self.browser.find_elements_by_class_name('views-field-nid')
        for i in ids:
            try:
                id = int(i.text)
                if id not in got_list:
                    got_list.append(id)
            except Exception:
                pass
        print('current work page :'+self.walkpage)
        print('current kcs list'+str(got_list))
        if got_list == []:
            raise Exception("kcs list hang,restart login.......")
        return got_list

    def insert_data(self, data):
        insert_kcs = kcs(id=data['id'], title=data['title'], environment=data['environment'], issue=data['issue'], res=data['resolution'],rc=data['rc'],ds=data['ds'],private=data['private'])
        print('current kcs::'+str(data['id']))
        self.Session.add(insert_kcs)
        self.Session.commit()

    def recvdata(self):
        while True:
            kcs_list = self.getkcslist()
            skip_count = 0
            for id in kcs_list:
                if self.Session.execute(select([kcs.id]).where(kcs.id == id)).rowcount == 0:
                    url = 'https://access.redhat.com/solutions/'+str(id)
                    self.browser.get(url)
                    try:
                        title = self.browser.find_element_by_class_name('title').text
                    except exceptions.NoSuchElementException:
                        title = ''
                    try:
                        environment = self.browser.find_element_by_class_name('field_kcs_environment_txt').text
                    except exceptions.NoSuchElementException:
                        environment = ''
                    try:
                        issue = self.browser.find_element_by_class_name('field_kcs_issue_txt').text
                    except exceptions.NoSuchElementException:
                        issue = ''
                    try:
                        resolution = self.browser.find_element_by_class_name('field_kcs_resolution_txt').text
                    except exceptions.NoSuchElementException:
                        resolution = ''
                    try:
                        rc = self.browser.find_element_by_class_name('field_kcs_rootcause_txt').text
                    except exceptions.NoSuchElementException:
                        rc = ''
                    try:
                        private = self.browser.find_element_by_class_name('private-notes--(red-hat-internal)').text
                    except exceptions.NoSuchElementException:
                        private = ''
                    try:
                        ds = self.browser.find_element_by_class_name('field_kcs_diagnostic_txt').text
                    except exceptions.NoSuchElementException:
                        ds = ''
                    self.insert_data({'id':id,'title':title,'environment':environment, 'issue':issue, 'resolution':resolution, 'rc':rc, 'private':private, 'ds':ds})
                else:
                    print('found duplicate kcs::'+str(id)+' skip, current skiped count '+str(skip_count))
                    skip_count += 1
            if self.walkpage == '':
                self.walkpage = '0'
            self.walkpage = str(int(self.walkpage) + 1)
            if self.stop  != '0' and int(self.walkpage) >= int(self.stop):
                sys.exit(100)

    def getarticle(self):
        pass


if __name__ == '__main__':
    fail_count = 10
    ########## start/stop page here (int)############
    start = <>
    stop = <>
    ################################################
    while fail_count != 0:
        s = sel(start, stop=stop)
        try:
            s.login()
            time.sleep(3)
        except Exception:
            print('login error:: restart........')
            s.browser.quit()
            s = None
            pass
        try:
            if s != None:
                s.recvdata()
        except Exception:
            start = s.walkpage
            fail_count+=1
            s.browser.quit()
            del s
        fail_count-=1
