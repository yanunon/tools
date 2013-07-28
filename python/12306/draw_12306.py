#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2013-07-28 20:03

@author: Yang Junyong <yanunon@gmail.com>
'''
import ticket
import matplotlib.pyplot as plt
from datetime import datetime


if __name__ == '__main__':
    leave_time = datetime.strptime('2013-08-16', '%Y-%m-%d')
    id = 'K117'
    td = ticket.TicketDB()
    td.open_db('12306.db')
    ticket_info = td.get_ticket_info(id, leave_time)
    td.close_db()
    data_time = []
    rw = []
    yw = []
    rz = []
    yz = []
    wz = []
    for ticket in ticket_info:
        rw.append(ticket[9])
        yw.append(ticket[10])
        rz.append(ticket[11])
        yz.append(ticket[12])
        wz.append(ticket[13])
        data_t = datetime.strptime(ticket[15], '%Y-%m-%d %H:%M:%S')
        data_time.append(data_t)
    
    plt.plot(data_time, yz, 'bo', label='yz')
    plt.plot(data_time, wz, 'b+', label='wz')
    plt.plot(data_time, rw, 'ro', label='rw')
    plt.plot(data_time, yw, 'r+', label='yw')
    #plt.plot([1,2],[1,2] , label='yz')
    plt.legend(loc="upper left", bbox_to_anchor=(1,1))
    plt.show()

