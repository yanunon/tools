#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2013-06-07 19:28

@author: Yang Junyong <yanunon@gmail.com>
'''

import md5
import base64
import urllib2
import urllib
import json
import random
import os

DIR = '.'

def encode_id(id):
    byte1 = bytearray('3go8&$8*3*3h0k(2)2')
    byte2 = bytearray(id)
    byte1len = len(byte1)
    for i in xrange(len(byte2)):
        byte2[i] = byte2[i]^byte1[i%byte1len]
    m = md5.new()
    m.update(byte2)
    result = m.digest().encode('base64')[:-1]
    result = result.replace('/', '_')
    result = result.replace('+', '-')
    return result

def get_artist(name):
    #curl -d "s=孙燕姿&type=100&offset=0&sub=false&limit=10" http://music.163.com/api/search/get
    search_url = 'http://music.163.com/api/search/get'
    params = {
            's': name,
            'type': 100,
            'offset': 0,
            'sub': 'false',
            'limit': 10
    }
    params = urllib.urlencode(params)
    resp = urllib2.urlopen(search_url, params)
    artists = json.loads(resp.read())
    if artists['code'] == 200 and artists['result']['artistCount'] > 0:
        return artists['result']['artists'][0]
    else:
        return None

def get_albums(artist):
    albums = []
    offset = 0
    while True:
        url = 'http://music.163.com/api/artist/albums/%d?offset=%d&limit=50' % (artist['id'], offset)
        resp = urllib2.urlopen(url)
        tmp_albums = json.loads(resp.read())
        albums.extend(tmp_albums['hotAlbums'])
        if tmp_albums['more'] == True:
            offset += 50
        else:
            break
    return albums

def get_songs(album):
    #print 'album:%s' % album['name']
    url = 'http://music.163.com/api/album/%d/' % album['id']
    resp = urllib2.urlopen(url)
    songs = json.loads(resp.read())
    return songs['album']['songs']

def download_song(song):
    album = song['album']['name']
    name = song['name']
    filepath = os.path.join(DIR, album, name+'.mp3')
    if os.path.exists(filepath):
        return

    folder = os.path.join(DIR, album)
    if not os.path.exists(folder):
        os.makedirs(folder)

    id = str(song['bMusic']['dfsId'])
    url = 'http://m%d.music.126.net/%s/%s.mp3' % (random.randrange(1, 3), encode_id(id), id)
    resp = urllib2.urlopen(url)
    f = open(filepath, 'wb')
    f.write(resp.read())
    f.close()
    print 'download album%s song:%s' % (album, name)

if __name__ == '__main__':
    artist = get_artist('孙燕姿')
    albums = get_albums(artist)
    for album in albums:
        songs = get_songs(album)
        for song in songs:
            download_song(song)

