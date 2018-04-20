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
        proxy = Proxy({'proxyType': ProxyType.MANUAL,
        'httpProxy' : "http://squid.redhat.com:3128",
        'ftpProxy': "http://squid.redhat.com:3128",
        'sslProxy': "http://squid.redhat.com:3128",
        'noProxy':''})
        self.browser = webdriver.Firefox(proxy=proxy)
        self.browser.set_page_load_timeout(300)
        self.username = 'rhn-support-minie'
        self.password = 'nieming0'
        self.kcs_list_url = 'https://access.redhat.com/solutions?title=&product=25&category=All&state=All&kcs_state=All&language=en&field_internal_tags_tid=All'
        if startpage == 0:
            self.walkpage = ''
        else:
            self.walkpage = str(startpage)
        self.stop = str(stop)
        self.engine = create_engine("mysql+pymysql://root:redhat@10.66.212.199/kcs", echo=True)
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
            raise Exception("kcs list hang,re start login.......")
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
            # if skip_count >=4 :
            #     self.walkpage =str(int(self.walkpage) + 1)
            #     print('too many skiped kcs , skip page 1......')
            self.walkpage = str(int(self.walkpage) + 1)
            if self.stop  != '0' and int(self.walkpage) >= int(self.stop):
                sys.exit(100)

    def getarticle(self):
        pass


if __name__ == '__main__':
    fail_count = 10
    workpage = 4827
    stop = 5695
    # workpage = 510
    # workpage = 1000
    # workpage = 1500

    while fail_count != 0:
        s = sel(workpage, stop=stop)
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
            workpage = s.walkpage
            fail_count+=1
            s.browser.quit()
            del s
        fail_count-=1