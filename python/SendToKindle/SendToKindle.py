#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2013-06-10 14:45

@author: Yang Junyong <yanunon@gmail.com>
'''
import urllib2
import os
import subprocess
import smtplib
import json

from bs4 import BeautifulSoup as BS
from email import Encoders
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase


DATA_DIR = 'zhihu'
KINDLE_EMAIL = ''
SENDER_EMAIL = ''
SENDER_PASSWORD = ''

CONTENT_TEMPLATE = '''
<html>
    <body>
    <h1>目录</h1>
    <p style="text-indent:0pt">
        %s
    </p>
    </body>
</html>
'''
CONTENT_ITEM_TEMPLATE = '<a href="%s">%s</a><br/>'

def fetch_blob(url):
    dst = url[url.find(r'://')+3:]
    dst = os.path.join('media', dst)
    dst_path = os.path.join(DATA_DIR, dst)
    if os.path.exists(dst_path):
        return dst

    folder = os.path.dirname(dst_path)
    if not os.path.exists(folder):
        os.makedirs(folder)

    resp = urllib2.urlopen(url)
    f = open(dst_path, 'wb')
    f.write(resp.read())
    f.close()

    return dst

def replace_media(bs):
    for img in bs.find_all('img'):
        img['src'] = fetch_blob(img['src'])

    for link in bs.find_all('link'):
        if link['href'].endswith('css'):
            link['href'] = fetch_blob('http://daily.zhihu.com' + link['href'])

    for script in bs.find_all('script'):
        script['src'] = fetch_blob('http://daily.zhihu.com' + script['src'])


def fetch_zhihu(No):
    url = 'http://daily.zhihu.com/api/1.1/news/%d' % No

    html_filename = '%s/%d.html' % (DATA_DIR, No)
    resp = urllib2.urlopen(url)
    html = resp.read()
    bs = BS(html)
    replace_media(bs)
    nhtml = bs.prettify()
    nhtml = nhtml.encode('utf-8')
    f = open(html_filename, 'wb')
    f.write(nhtml)
    f.close()

    return html_filename

def send_to_kindle(mobi_file, title):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = KINDLE_EMAIL
    msg['Subject'] = title

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(mobi_file, 'rb').read())
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(mobi_file))
    msg.attach(part)

    smtp = smtplib.SMTP('smtp.gmail.com:587')
    smtp.starttls()
    smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
    smtp.sendmail(SENDER_EMAIL, KINDLE_EMAIL, msg.as_string())
    smtp.quit()


def main():
    latest = 'http://daily.zhihu.com/api/1.1/news/latest'
    resp = urllib2.urlopen(latest)
    news = json.loads(resp.read())
    contents_body = ''
    for new in news['news']:
        html_file = os.path.join(DATA_DIR, str(new['id'])+'.html')
        title = new['title'].encode('utf-8')
        print title
        if not os.path.exists(html_file):
            fetch_zhihu(new['id'])

        contents_body += CONTENT_ITEM_TEMPLATE % (str(new['id'])+'.html', title)
        #print title

    contents = CONTENT_TEMPLATE % contents_body
    html_filename = os.path.join(DATA_DIR, news['date']+'.html')
    mobi_filename = os.path.join(DATA_DIR, news['date']+'.mobi')

    if os.path.exists(mobi_filename):
        return

    f = open(html_filename, 'w')
    f.write(contents)
    f.close()

    title = '知乎日报 ' + news['display_date'].encode('utf-8')
    authors = '知乎日报'
    cover = 'Logo.png'

    p = subprocess.Popen(['ebook-convert', html_filename, mobi_filename, '--authors', authors, '--cover', cover, '--title', title], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    send_to_kindle(mobi_filename, title)
    
if __name__ == '__main__':
    main()

