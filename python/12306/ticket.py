#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2013-07-28 13:53

@author: Yang Junyong <yanunon@gmail.com>
'''

import os
import urllib2
import urllib
import json
import re
import sqlite3
import sys

from datetime import datetime, timedelta

QueryLeftTicketUrl = 'http://dynamic.12306.cn/otsquery/query/queryRemanentTicketAction.do?method=queryLeftTicket&orderRequest.train_date=%s&orderRequest.from_station_telecode=%s&orderRequest.to_station_telecode=%s&orderRequest.train_no=&trainPassType=QB&trainClass=QB%%23D%%23Z%%23T%%23K%%23QT%%23&includeStudent=%s&seatTypeAndNum=&orderRequest.start_time_str=00%%3A00--24%%3A00'


HTML_ELEMENT_RE = re.compile('<.+?>')
ST_TIME_RE = re.compile(r'(.+?)(\d{2}:\d{2})')
TRIAN_INFO_ITEMS = ['no', 'id', 'from', 'to', 'time', 'sw', 'td', 'yd', 'ed', 'gr', 'rw', 'yw', 'rz', 'yz', 'wz', 'qt']

DB_TEXT_ITEMS = ['id', 'from', 'to', 'time']
DB_INTEGER_ITEMS = ['sw', 'td', 'yd', 'ed', 'gr', 'rw', 'yw', 'rz', 'yz', 'wz', 'qt']

DATA_DIR = 'data'

def query_left_ticket(from_st, to_st, date, is_student):
    student = '00'
    if is_student:
        student = '0X00'

    url = QueryLeftTicketUrl % (date, from_st, to_st, student)
    resp = urllib2.urlopen(url)
    html_str = resp.read()
    if html_str == '-1':
        print url
        return None

    ticket_info = json.loads(html_str)
    time_str = ticket_info['time']
    ticket_data = ticket_info['datas']
    trains =  ticket_data.split('\\n')
    train_infos = []
    for train in trains:
        train_info = load_train_info(train)
        train_infos.append(train_info)

    today = datetime.today().strftime('%Y-%m-%d_')
    data_time = today+time_str

    return {'data_time':data_time, 'leave_time':date, 'data':train_infos, 'is_student':is_student}

def parse_st_time(st):
    m = ST_TIME_RE.match(st)
    st = m.group(1)
    time = m.group(2)
    return (st, time)

def load_train_info(train_str):
    train_str = train_str.replace('&nbsp;', '')
    train_str = HTML_ELEMENT_RE.sub('', train_str)
    item = train_str.split(',')
    train = {}
    for i in xrange(len(TRIAN_INFO_ITEMS)):
        train[TRIAN_INFO_ITEMS[i]] = item[i]
    
    st, time = parse_st_time(train['from'])
    train['from'] = st
    train['from_time'] = time

    st, time = parse_st_time(train['to'])
    train['to'] = st
    train['to_time'] = time

    return train


class TicketDB(object):
    def __init__(self):
        pass

    def open_db(self, name):
        self.conn = sqlite3.connect(name)
        self.__create_table()

    def __create_table(self):
        cur = self.conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS ticket (id text, from_st text, to_st text, time text, sw integer, td integer, yd integer, ed integer, gr integer, rw integer, yw integer, rz integer, yz integer, wz integer ,qt integer, data_time integer, leave_time integer)')
        self.conn.commit()
        cur.close()

    def close_db(self):
        self.conn.close()

    def get_ticket_info(self, id, leave_time):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM ticket WHERE id=? AND leave_time=? ORDER BY data_time', (id, leave_time))
        tickets = cur.fetchall()
        cur.close()
        return tickets 

    def insert_item(self, data):
        data_time_str = data['data_time']
        data_time = datetime.strptime(data_time_str, '%Y-%m-%d_%H:%M')
        leave_time = datetime.strptime(data['leave_time'],'%Y-%m-%d')

        cur = self.conn.cursor()

        for d in data['data']:
            cur.execute('SELECT data_time, id, leave_time FROM ticket WHERE data_time=? AND id=? AND leave_time=?', (data_time, d['id'], leave_time))
            pre_fetch = cur.fetchone()
            if pre_fetch:
                continue

            to_insert = []
            for it in DB_TEXT_ITEMS:
                to_insert.append(d[it])
            for it in DB_INTEGER_ITEMS:
                value = d[it]
                if not re.match(r'\d+', value):
                    value = 0
                else:
                    value = int(value)
                to_insert.append(value)
            to_insert.append(data_time)
            to_insert.append(leave_time)
            
            cur.execute('INSERT INTO ticket VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', to_insert)
            self.conn.commit()
        cur.close()

    def import_from_file(self, dir):
        files = os.listdir(dir)
        for fn in files:
            if not fn.endswith('json'):
                continue
            fp = open(os.path.join(dir, fn), 'r')
            data = json.load(fp)
            fp.close()
            data['leave_time'] = fn.split('_')[2]
            self.insert_item(data)

    def fetch_from_net(self, from_st, to_st):
        today = datetime.today()
        for i in range(20):
            date = today + timedelta(days=i)
            date = date.strftime('%Y-%m-%d')
            self.process_left_ticket(from_st, to_st, date, False)
            self.process_left_ticket(to_st, from_st, date, False)

        for i in range(20, 30):
            date = today + timedelta(days=i)
            date = date.strftime('%Y-%m-%d')
            self.process_left_ticket(from_st, to_st, date, True)
            self.process_left_ticket(to_st, from_st, date, True)

    def process_left_ticket(self, from_st, to_st, date, is_student):
        result = query_left_ticket(from_st, to_st, date, is_student)
        if result:
            self.insert_item(result)

if __name__ == '__main__':
    tb = TicketDB()
    tb.open_db('12306.db')
    if len(sys.argv) == 2:
        tb.import_from_file(sys.argv[1])
    else:
        tb.fetch_from_net('CDW', 'BJP')
    tb.close_db()

