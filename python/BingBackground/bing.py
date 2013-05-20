#!/usr/bin/env python
#-*- coding:utf-8 -*-
import urllib2
import re
import os
import subprocess
import getpass

IMG_DIR = 'bing'

def download_img():
    url = 'http://cn.bing.com'
    img_path = ''
    try:
        resp = urllib2.urlopen(url)
        html_str = resp.read()
        img_re_str = r'g_img={url:\'(.*?1366x768\.jpg)\''
        result = re.search(img_re_str, html_str)
        if result:
            img_url = result.group(1)
            #print img_url
  
            if not os.path.exists(IMG_DIR):
                os.makedirs(IMG_DIR)
            tmp_img_path = img_url[img_url.rfind('/')+1:]
            tmp_img_path = os.path.join(IMG_DIR, tmp_img_path)
            tmp_img_path = os.path.abspath(tmp_img_path)
            if os.path.exists(tmp_img_path):
                img_path = tmp_img_path
                return img_path

            resp = urllib2.urlopen(img_url)
            data = resp.read()
            img_f = open(tmp_img_path, 'wb')
            img_f.write(data)
            img_f.close()
            img_path = tmp_img_path
            
    except Exception, e:
        print e
    return img_path

def get_dbus_config():
    user_name = getpass.getuser()
    dir = os.path.join('/home', user_name, '.dbus/session-bus')
    files = os.listdir(dir)
    if len(files) == 0:
        return ''

    modified_times = dict([(x, os.stat(os.path.join(dir, x)).st_mtime) for x in files])
    config_path = max(modified_times, key=lambda k: modified_times.get(k))
    cf = open(os.path.join(dir, config_path), 'r')
    config = cf.readlines()
    cf.close()
    for line in config:
        if line.startswith('DBUS_SESSION_BUS_ADDRESS='):
            line = line.replace('DBUS_SESSION_BUS_ADDRESS=','')
            line = line.replace('\n', '')
            return line

    return ''

def get_dbus_config_new():
    cmd= "cat /proc/$(ps -u `whoami` | grep -i gnome-session$ | awk '{print $1}')/environ | grep -z DBUS_SESSION_BUS_ADDRESS>/tmp/dbus_config"
    ret = os.system(cmd)
    config = ''
    if ret == 0:
        f = open('/tmp/dbus_config', 'r')
        config = f.read()
        f.close()
        config = config.replace('DBUS_SESSION_BUS_ADDRESS=', '')
        config = config.replace('\x00', '')
    return config

def set_background():
    img_path = download_img()
    if img_path == '':
        return
    img_path = 'file://' + img_path
    env = os.environ.copy()
    env['DBUS_SESSION_BUS_ADDRESS'] = get_dbus_config_new()
    cmd = ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', img_path]
    pro = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
    out, err = pro.communicate()
    if pro.returncode == 0:
        print 'set ok!!!'
    else:
        print 'err:' + err

if __name__ == '__main__':
    set_background()
