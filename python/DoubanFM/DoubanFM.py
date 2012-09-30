#!/usr/bin/env python
#-*- coding:utf-8 -*-
'''
Created on 2012-7-20

@author: "Yang Junyong <yanunon@gmail.com>"
'''

import urllib
import urllib2
import cookielib
import StringIO
import json
import os
import eyeD3
import sys

class DoubanFM(object):
    headers_web = {'User-Agent':'Mozilla/5.0(iPad; U; CPU OS 4_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F191 Safari/6533.18.5'}
    headers_android = {'User-Agent' : 'Android-4.1.1'}
    
    def __init__(self, user_name, user_passwd):
        self.user_name = user_name
        self.user_passwd = user_passwd
    
    def login_android(self):
        login_url = 'http://www.douban.com/j/app/login'
        data = {'username' : self.user_name,
                'version' : 608,
                'client' : 's:mobile|y:android 4.1.1|f:608|m:Google|d:-1178839463|e:google_galaxy_nexus',
                'app_name' : 'radio_android',
                'password' : self.user_passwd,
                'from' : 'android_608_Google',
                }
        data = urllib.urlencode(data)
        req = urllib2.Request(login_url, data, self.headers_android)
        resp = urllib2.urlopen(req)
        login_data = json.loads(resp.read())
        #print login_data
        if login_data['err'] == 'ok':
            self.user_id = login_data['user_id']
            self.token = login_data['token']
            self.expire = login_data['expire']
        return login_data['err']
    
    def _get_liked_list(self, count):
        liked_list_url = 'http://www.douban.com/j/app/radio/liked_songs?exclude=675558|12384|642358|546734|10761|761079|1394944|546727|676245|431315&version=608&client=s:mobile|y:android+4.1.1|f:608|m:Google|d:-1178839463|e:google_galaxy_nexus&app_name=radio_android&from=android_608_Google&formats=aac'
        liked_list_url += '&count=' + str(count) + '&token=' + self.token + '&user_id=' + self.user_id + '&expire=' + self.expire
        
        req = urllib2.Request(liked_list_url, None, self.headers_android)
        resp = urllib2.urlopen(req)
        liked_list = json.loads(resp.read())
        songs = liked_list['songs']
        
        return songs
        #print json.dumps(liked_list, sort_keys=True, indent=4)
       
    def download(self, count, dir='liked'):
        ret = self.login_android()
        if ret != 'ok':
            print ret
            return
        songs = self._get_liked_list(count)
        
        if os.path.isdir(dir) is False:
            os.makedirs(dir)
        dir = os.path.abspath(dir)
        
        for song in songs:
            song['title'] = song['title'].replace('/', '&')
            name = os.path.join(dir,song['title']+'.mp3')
            if os.path.exists(name):
                continue
            resp = urllib2.urlopen(song['url'])
            data = resp.read()
            songf = open(name, 'w')
            songf.write(data)
            songf.close()
            #eyeD3在Windows工作不正常
            if sys.platform == 'linux2':
                self._add_tag(song, name)
            print song['title']
            
    def _add_tag(self, song, filename):
        tag = eyeD3.Tag()
        tag.link(filename)
        tag.setVersion(eyeD3.ID3_V2_3)
        tag.setTitle(song['title'])  
        tag.setArtist(song['artist'])  
        tag.setAlbum(song['albumtitle'])
        tag.update() 
        
def setup_cookie():
    cookie = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    urllib2.install_opener(opener)

if __name__ == '__main__':
    setup_cookie()
    d = DoubanFM('DOUBAN_ID', 'DOUBAN_PASSWORD') #豆瓣帐号和密码
    d.download(100) #红心歌曲数量
