from __future__ import unicode_literals

import math

import requests
import re
import bilibili_api
from bilibili_api import video, sync, video_zone, rank, Credential, user, ResponseCodeException
import json
import time
import codecs
import pandas as pd
import pymysql
from requests import ConnectTimeout
from requests.exceptions import ChunkedEncodingError
from sqlalchemy import create_engine

#未使用
def search_video(search_name, pages):
    """
    search_name: str; 输入搜索关键词
    pages: int; 输入需要爬取的页数

    return:
    bvid_lst: list; 返回BV号列表
    up_lst: list; 返回up主名字列表；与BV号一一对应
    """

    bvid_lst = []
    up_lst = []
    for page in range(1, pages):
        url = ('http://search.bilibili.com/all?keyword=' + search_name +
               '&single_column=0&&order=dm&page=' + str(page))
        req = requests.get(url)
        content = req.text
        pattern = re.compile('<a href="//www.bilibili.com/video/(.*?)\?from=search" title=')
        pattern_up = re.compile('<a href="//space.bilibili.com/.*?class="up-name">(.*?)</a></span>')
        lst_add = pattern.findall(content)
        up_lst_add = pattern_up.findall(content)

        while len(lst_add) == 0:
            url = ('http://search.bilibili.com/all?keyword=' + search_name +
                   '&single_column=0&&order=dm&page=' + str(page))
            req = requests.get(url)
            content = req.text
            pattern = re.compile('<a href="//www.bilibili.com/video/(.*?)\?from=search" title=')
            pattern_up = re.compile('<a href="//space.bilibili.com/.*?class="up-name">(.*?)</a></span>')
            lst_add = pattern.findall(content)
            up_lst_add = pattern_up.findall(content)

        time.sleep(1)
        print('第{}页'.format(page), lst_add)
        up_lst.extend(up_lst_add)
        bvid_lst.extend(lst_add)
    return bvid_lst, up_lst

######################################################################
########因涉及个人隐私，代码中重要数据已脱敏，故无法直接使用，需要自行配置#########
######################################################################
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'referer': 'https://www.bilibili.com/',
    'x-csrf-token': '',
    'x-requested-with': 'XMLHttpRequest',
    'cookie': '',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/90.0.4430.212 Safari/537.36'
}
POPULAR_URL = "https://api.bilibili.com/x/web-interface/popular"
# pn: 0~26
WEEKLY_URL = "https://api.bilibili.com/x/web-interface/popular/series/one?number="
TAG_URL = "https://api.bilibili.com/x/web-interface/view/detail/tag?"
ZONE_TID = [24, 25, 47, 210, 86, 253, 27, 17, 171, 172, 65, 173, 121, 136, 19, 22, 26, 126, 216, 127, 28, 31, 59, 30,
            29, 193, 243, 244, 130, 20, 198,
            199, 200, 154, 156, 182, 183, 85, 184, 71, 241, 242, 137, 201, 124, 228, 207, 208, 209, 122, 95, 230, 231,
            232, 203, 204, 205, 206, 76,
            212, 213, 214, 215, 138, 254, 250, 251, 239, 161, 162, 21, 245, 246, 247, 248, 240, 227, 176, 157, 252, 258,
            159, 235, 249, 164, 236,
            237, 238, 218, 219, 222, 220, 75, 138, 17]
UP_STAT_URL = "https://api.bilibili.com/x/space/upstat?mid="
VIDEO_DATA = "data/video.json"
UP_DATA = "data/up.json"
VIDEO_ZONE='data/video_zone.json'
SQL = create_engine('mysql+pymysql://root:pwd@localhost:3306/videoinfosql')
SESSDATA = ''
bili_jct = ''
buvid3 = ''
DedeUserID = ''
FOLLOWINGS_DATA = "data/followings.json"
FOLLOWINGS_2_DATA = "data/followings_2.json"
FOLLOWINGS_MAX = 530
FOLLOWINGS_2_MAX = 104


def get_json_length(fileName):
    load_f = codecs.open(fileName, 'r', encoding="utf8")
    videoJson = json.load(load_f)
    videoList = videoJson['list']
    return len(videoList)

#获取每周必看视频
def get_weekly(start, end, flag):  # if flag==true, write to sql too
    load_f = codecs.open(VIDEO_DATA, 'r', encoding="utf8")
    videoJson = json.load(load_f)
    videoJson['updateTime'] = int(time.time())
    videoList = videoJson['data']

    df_video_write = pd.DataFrame(
        columns=['week', 'aid', 'tname', 'pic', 'title', 'pubdate', 'desc', 'cid', 'bvid',
                 'rcmd_reason', 'owner', 'view', 'danmaku',
                 'reply', 'favorite', 'coin', 'share', 'his_rank', 'like',
                 'tag'])
    df_owner_write = pd.DataFrame(columns=['mid', 'name', 'face'])

    count = 0
    try:
        for i in range(start, end + 1):
            url = WEEKLY_URL + str(i)
            res = requests.get(url, headers=HEADERS)
            resJson = res.json()
            dataList = resJson['data']['list']
            length = len(dataList)

            df_video_write.drop(df_video_write.index, inplace=True)
            df_owner_write.drop(df_owner_write.index, inplace=True)

            for j in range(0, length):
                videoObject = {}
                videoObject_sql = {}
                aid = dataList[j]['aid']
                cid = dataList[j]['cid']
                videoObject['week'] = i
                videoObject['aid'] = dataList[j]['aid']  # av号
                videoObject['tname'] = dataList[j]['tname']  # 分区
                videoObject['pic'] = dataList[j]['pic']  # cover
                videoObject['title'] = dataList[j]['title']  # title
                videoObject['pubdate'] = dataList[j]['pubdate']  # upload time
                videoObject['desc'] = dataList[j]['desc']  # description

                videoObject['cid'] = dataList[j]['cid']
                videoObject['bvid'] = dataList[j]['bvid']
                videoObject['rcmd_reason'] = dataList[j]['rcmd_reason']

                if flag:
                    videoObject_sql = videoObject.copy()

                ownerObject = {}
                ownerObject['mid'] = dataList[j]['owner']['mid']  # UID of UP
                ownerObject['name'] = dataList[j]['owner']['name']  # name of UP
                ownerObject['face'] = dataList[j]['owner']['face']  # avatar of UP
                videoObject['owner'] = ownerObject
                if flag:
                    videoObject_sql['owner'] = dataList[j]['owner']['mid']

                statObject = {}  # data of this video
                statObject['view'] = dataList[j]['stat']['view']
                statObject['danmaku'] = dataList[j]['stat']['danmaku']
                statObject['reply'] = dataList[j]['stat']['reply']
                statObject['favorite'] = dataList[j]['stat']['favorite']
                statObject['coin'] = dataList[j]['stat']['coin']
                statObject['share'] = dataList[j]['stat']['share']
                statObject['his_rank'] = dataList[j]['stat']['his_rank']
                statObject['like'] = dataList[j]['stat']['like']
                videoObject['stat'] = statObject

                if flag:
                    videoObject_sql['view'] = dataList[j]['stat']['view']
                    videoObject_sql['danmaku'] = dataList[j]['stat']['danmaku']
                    videoObject_sql['reply'] = dataList[j]['stat']['reply']
                    videoObject_sql['favorite'] = dataList[j]['stat']['favorite']
                    videoObject_sql['coin'] = dataList[j]['stat']['coin']
                    videoObject_sql['share'] = dataList[j]['stat']['share']
                    videoObject_sql['his_rank'] = dataList[j]['stat']['his_rank']
                    videoObject_sql['like'] = dataList[j]['stat']['like']

                tag_url = TAG_URL + "aid=" + str(aid) + "&cid=" + str(cid)
                tag_res = requests.get(tag_url, headers=HEADERS)
                tag_json = tag_res.json()
                tag_list = tag_json['data']
                tagList = []
                tagString = ''
                for k in range(0, len(tag_list)):
                    tagList.append(tag_list[k]['tag_name'])
                    tagString += tag_list[k]['tag_name']
                    if k != (len(tag_list) - 1):
                        tagString += '$'
                videoObject['tag'] = tagList
                if flag:
                    videoObject_sql['tag'] = tagString

                videoList.append(videoObject)

                if flag:
                    df_video_write = df_video_write.append(videoObject_sql, ignore_index=True)
                    df_owner_write = df_owner_write.append(ownerObject, ignore_index=True)

                count += 1
                time.sleep(0.5)

            df_video_write.to_sql('video', SQL, index=False, if_exists='append')
            df_owner_write.to_sql('owner', SQL, index=False, if_exists='append')
            print("successfully get weekly " + str(i))
            time.sleep(1)
    finally:
        videoJson['list'] = videoList
        dump_f = open(VIDEO_DATA, 'w', encoding="utf8")
        if count >= 50:
            json.dump(videoJson, dump_f, ensure_ascii=False)

#获取每周必看视频（写入数据库）
def get_weekly_sql(start, end):
    for i in range(start, end + 1):
        url = WEEKLY_URL + str(i)
        res = requests.get(url, headers=HEADERS)
        resJson = res.json()
        dataList = resJson['data']['list']
        length = len(dataList)

        for j in range(0, length):
            videoObject = {}
            aid = dataList[j]['aid']
            cid = dataList[j]['cid']
            videoObject['week'] = i
            videoObject['aid'] = dataList[j]['aid']  # av号
            videoObject['tname'] = dataList[j]['tname']  # 分区
            videoObject['pic'] = dataList[j]['pic']  # cover
            videoObject['title'] = dataList[j]['title']  # title
            videoObject['pubdate'] = dataList[j]['pubdate']  # upload time
            videoObject['desc'] = dataList[j]['desc']  # description

            ownerObject = {}
            ownerObject['mid'] = dataList[j]['owner']['mid']  # UID of UP
            ownerObject['name'] = dataList[j]['owner']['name']  # name of UP
            ownerObject['face'] = dataList[j]['owner']['face']  # avatar of UP
            videoObject['owner'] = dataList[j]['owner']['mid']

            videoObject['view'] = dataList[j]['stat']['view']
            videoObject['danmaku'] = dataList[j]['stat']['danmaku']
            videoObject['reply'] = dataList[j]['stat']['reply']
            videoObject['favorite'] = dataList[j]['stat']['favorite']
            videoObject['coin'] = dataList[j]['stat']['coin']
            videoObject['share'] = dataList[j]['stat']['share']
            videoObject['his_rank'] = dataList[j]['stat']['his_rank']
            videoObject['like'] = dataList[j]['stat']['like']

            videoObject['cid'] = dataList[j]['cid']
            videoObject['bvid'] = dataList[j]['bvid']
            videoObject['rcmd_reason'] = dataList[j]['rcmd_reason']

            tag_url = TAG_URL + "aid=" + str(aid) + "&cid=" + str(cid)
            tag_res = requests.get(tag_url, headers=HEADERS)
            tag_json = tag_res.json()
            tag_list = tag_json['data']
            tagString = ''
            for k in range(0, len(tag_list)):
                tagString += tag_list[k]['tag_name']
                if k != (len(tag_list) - 1):
                    tagString += '$'
            videoObject['tag'] = tagString

            df_video_write = pd.DataFrame(
                columns=['week', 'aid', 'tname', 'pic', 'title', 'pubdate', 'desc', 'owner', 'view', 'danmaku',
                         'reply', 'favorite', 'coin', 'share', 'his_rank', 'like', 'cid', 'bvid', 'rcmd_reason', 'tag'])
            df_video_write = df_video_write.append(videoObject, ignore_index=True)
            df_video_write.to_sql('video', SQL, index=False, if_exists='append')

            df_owner_write = pd.DataFrame(columns=['mid', 'name', 'face'])
            df_owner_write = df_owner_write.append(ownerObject, ignore_index=True)
            df_owner_write.to_sql('owner', SQL, index=False, if_exists='append')

            time.sleep(0.1)
        print("successfully get weekly " + str(i))
        time.sleep(1)

#获取排行榜上的视频（写入数据库）
def get_rank_sql(arg):
    for z in rank.RankType:
        if arg != 'all':
            if z.name != arg:
                continue
        #以下分区没有排行榜，跳过
        if z.name == 'Bangumi' or z.name == 'GuochuanAnime' or z.name == 'Guochuang' or z.name == 'Documentary' \
                or z.name == 'Movie' or z.name == 'TV' or z.name == 'Variety':
            continue
        if arg == 'Kitchen':
            url = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=119&type=all"
            res = requests.get(url, headers=HEADERS)
            resJson = res.json()
            dataList = resJson['data']['list']
        else:
            resJson = sync(rank.get_rank(z))
            dataList = resJson['list']
        for j in range(0, len(dataList)):
            videoObject = {}
            aid = dataList[j]['aid']
            cid = dataList[j]['cid']
            videoObject['aid'] = dataList[j]['aid']  # av号
            videoObject['tname'] = dataList[j]['tname']  # 分区
            videoObject['pic'] = dataList[j]['pic']  # cover
            videoObject['title'] = dataList[j]['title']  # title
            videoObject['pubdate'] = dataList[j]['pubdate']  # upload time
            videoObject['desc'] = dataList[j]['desc']  # description

            ownerObject = {}
            ownerObject['mid'] = dataList[j]['owner']['mid']  # UID of UP
            ownerObject['name'] = dataList[j]['owner']['name']  # name of UP
            ownerObject['face'] = dataList[j]['owner']['face']  # avatar of UP
            videoObject['owner'] = dataList[j]['owner']['mid']

            videoObject['view'] = dataList[j]['stat']['view']
            videoObject['danmaku'] = dataList[j]['stat']['danmaku']
            videoObject['reply'] = dataList[j]['stat']['reply']
            videoObject['favorite'] = dataList[j]['stat']['favorite']
            videoObject['coin'] = dataList[j]['stat']['coin']
            videoObject['share'] = dataList[j]['stat']['share']
            videoObject['his_rank'] = dataList[j]['stat']['his_rank']
            videoObject['like'] = dataList[j]['stat']['like']

            videoObject['cid'] = dataList[j]['cid']
            videoObject['bvid'] = dataList[j]['bvid']

            tag_url = TAG_URL + "aid=" + str(aid) + "&cid=" + str(cid)
            tag_res = requests.get(tag_url, headers=HEADERS)
            tag_json = tag_res.json()
            tag_list = tag_json['data']
            tagString = ''
            for k in range(0, len(tag_list)):
                tagString += tag_list[k]['tag_name']
                if k != (len(tag_list) - 1):
                    tagString += '$'
            videoObject['tag'] = tagString

            df_video_write = pd.DataFrame(
                columns=['aid', 'tname', 'pic', 'title', 'pubdate', 'desc', 'owner', 'view', 'danmaku',
                         'reply', 'favorite', 'coin', 'share', 'his_rank', 'like', 'cid', 'bvid', 'tag'])
            df_video_write = df_video_write.append(videoObject, ignore_index=True)
            df_video_write.to_sql('video', SQL, index=False, if_exists='append')

            df_owner_write = pd.DataFrame(columns=['mid', 'name', 'face'])
            df_owner_write = df_owner_write.append(ownerObject, ignore_index=True)
            df_owner_write.to_sql('owner', SQL, index=False, if_exists='append')

            print('successfully get zone 【' + z.name + '】\'s rank No.' + str(j))
            time.sleep(0.5)
        if arg == 'Kitchen':
            break

#获取单个视频的信息，放入字典返回
def get_videoObject(bvid):
    while True:
        try:
            videoJson = get_videos_info(bvid)
            print("getting 【" + videoJson['title'] + '】……')

            videoObject = {}
            aid = videoJson['aid']
            videoObject['aid'] = videoJson['aid']  # av号
            videoObject['tname'] = videoJson['tname']  # 分区
            videoObject['pic'] = videoJson['pic']  # cover
            videoObject['title'] = videoJson['title']  # title
            videoObject['pubdate'] = videoJson['pubdate']  # upload time
            videoObject['desc'] = videoJson['desc']  # description
            videoObject['owner'] = videoJson['owner']['mid']

            videoObject['view'] = videoJson['stat']['view']
            videoObject['danmaku'] = videoJson['stat']['danmaku']
            videoObject['reply'] = videoJson['stat']['reply']
            videoObject['favorite'] = videoJson['stat']['favorite']
            videoObject['coin'] = videoJson['stat']['coin']
            videoObject['share'] = videoJson['stat']['share']
            videoObject['his_rank'] = videoJson['stat']['his_rank']
            videoObject['like'] = videoJson['stat']['like']

            videoObject['bvid'] = videoJson['bvid']

            if 'cid' in videoJson:
                cid = videoJson['cid']
                videoObject['cid'] = videoJson['cid']
                tag_url = TAG_URL + "aid=" + str(aid) + "&cid=" + str(cid)
                tag_res = requests.get(tag_url, headers=HEADERS)
                tag_json = tag_res.json()
                tag_list = tag_json['data']
                tagString = ''
                for k in range(0, len(tag_list)):
                    tagString += tag_list[k]['tag_name']
                    if k != (len(tag_list) - 1):
                        tagString += '$'
                videoObject['tag'] = tagString

            if 'staff' in videoJson:
                staff = ''
                for i in range(0, len(videoJson['staff'])):
                    staff += str(videoJson['staff'][i]['mid'])
                    staff += '$'
                    staff += videoJson['staff'][i]['title']
                    if i != (len(videoJson['staff']) - 1):
                        staff += '$'
                videoObject['staff'] = staff

            if 'honor' in videoJson:
                honor = ''
                for i in range(0, len(videoJson['honor_reply']['honor'])):
                    honor += videoJson['honor_reply']['honor'][i]['desc']
                    if i != (len(videoJson['honor_reply']['honor']) - 1):
                        honor += '$'
                videoObject['honor'] = honor

            time.sleep(0.5)
            return videoObject
        except TimeoutError:
            time.sleep(10)
        except ConnectTimeout:
            time.sleep(10)
        except ChunkedEncodingError:
            time.sleep(10)

#获取关注列表中UP主所有视频
def get_followings_sql(flag, start, end, PN=1):
    CREDENTIAL = Credential(SESSDATA, bili_jct, buvid3, DedeUserID)

    if flag:
        load_f = codecs.open(FOLLOWINGS_DATA, 'r', encoding="utf8")
    else:
        load_f = codecs.open(FOLLOWINGS_2_DATA, 'r', encoding="utf8")
    followingsJson = json.load(load_f)
    followingsList = followingsJson['data']['list']

    for i in range(start - 1, end):
        df_owner_write = pd.DataFrame(columns=['mid', 'name', 'face', 'sign'])
        ownerObject = {}
        ownerObject['mid'] = followingsList[i]['mid']  # UID of UP
        ownerObject['name'] = followingsList[i]['uname']  # name of UP
        ownerObject['face'] = followingsList[i]['face']  # avatar of UP
        ownerObject['sign'] = followingsList[i]['sign']
        df_owner_write = df_owner_write.append(ownerObject, ignore_index=True)

        USER = user.User(followingsList[i]['mid'], credential=CREDENTIAL)
        videoJson = sync(USER.get_videos())
        pn_total = math.ceil(videoJson['page']['count'] / 30)
        for j in range(PN, pn_total + 1):
            videoJson = sync(USER.get_videos(pn=j))
            videoList = videoJson['list']['vlist']
            df_video_write = pd.DataFrame(
                columns=['aid', 'tname', 'pic', 'title', 'pubdate', 'desc', 'owner', 'view', 'danmaku',
                         'reply', 'favorite', 'coin', 'share', 'his_rank', 'like', 'cid', 'bvid', 'tag', 'staff',
                         'honor'])
            for k in range(0, len(videoList)):
                try:
                    videoObject = get_videoObject(videoList[k]['bvid'])
                    df_video_write = df_video_write.append(videoObject, ignore_index=True)
                except ResponseCodeException:
                    continue

            df_video_write.to_sql('video', SQL, index=False, if_exists='append')
            print('successfully get 【' + followingsList[i]['uname'] + '】\'s video in page ' + str(j))

        df_owner_write.to_sql('owner', SQL, index=False, if_exists='append')

#未使用
def get_single_video_sql(bvid):
    df_video_write = pd.DataFrame(
        columns=['aid', 'tname', 'pic', 'title', 'pubdate', 'desc', 'owner', 'view', 'danmaku',
                 'reply', 'favorite', 'coin', 'share', 'his_rank', 'like', 'cid', 'bvid', 'tag', 'staff',
                 'honor'])
    videoObject = get_videoObject(bvid)
    df_video_write = df_video_write.append(videoObject, ignore_index=True)
    df_video_write.to_sql('video', SQL, index=False, if_exists='append')

    df_owner_write = pd.DataFrame(columns=['mid', 'name', 'face', 'sign'])
    videoJson = get_videos_info(bvid)
    ownerObject = {}
    ownerObject['mid'] = videoJson['owner']['mid']  # UID of UP
    ownerObject['name'] = videoJson['owner']['uname']  # name of UP
    ownerObject['face'] = videoJson['owner']['face']  # avatar of UP
    df_owner_write.to_sql('owner', SQL, index=False, if_exists='append')
    print('successfully get 【' + videoObject['title'] + '】')

#获取热门榜单上的视频列表
def get_popular_list():
    bvidList = []
    for i in range(1, 26):
        query = "pn=" + str(i)
        r = requests.get(POPULAR_URL, headers=HEADERS, params=query)
        resultList = r.json()['data']['list']
        for item in resultList:
            bvidList.append(
                bilibili_api.aid2bvid(
                    item['aid']
                )
            )
    return bvidList


def get_videos_info(bvid):
    # 实例化 Video 类
    v = video.Video(bvid=bvid)
    # 获取视频信息
    info = sync(v.get_info())
    # 返回视频信息
    return info

#获取UP主数据（写入数据库）
def get_up_sql(start):
    db = pymysql.connect(host='localhost', user='root', passwd='pwd', database='videoinfosql')
    # 创建游标对象
    cursor = db.cursor()
    # 使用execute()方法执行sql语句
    sql = 'select owner from video order by owner'
    cursor.execute(sql)

    # 获取所有记录列表
    results = cursor.fetchall()

    CREDENTIAL = Credential(SESSDATA, bili_jct, buvid3, DedeUserID)
    up = ''
    count = start
    for i in range(start, len(results)):
        count += 1
        if up != str(results[i]).split('(')[1].split(',')[0]:
            up = str(results[i]).split('(')[1].split(',')[0]
        else:
            continue
        USER = user.User(int(up), credential=CREDENTIAL)

        print('getting 【' + up + '】……')
        ownerObject = {}
        try:
            infoJson = sync(USER.get_user_info())
            ownerObject['mid'] = infoJson['mid']
            ownerObject['name'] = infoJson['name']
            name = infoJson['name']
            ownerObject['face'] = infoJson['face']
            ownerObject['sign'] = infoJson['sign']
        except ResponseCodeException:
            ownerObject['mid'] = int(up)
            ownerObject['name'] = '账号已注销'
            name = '账号已注销'

        foJson = sync(USER.get_relation_info())
        ownerObject['following'] = foJson['following']
        ownerObject['follower'] = foJson['follower']

        statJson = sync(USER.get_up_stat())
        ownerObject['archive'] = statJson['archive']['view']
        ownerObject['article'] = statJson['article']['view']
        ownerObject['likes'] = statJson['likes']

        df_owner_write = pd.DataFrame(columns=['mid', 'name', 'face', 'sign', 'following', 'follower', 'archive',
                                               'article', 'likes'])
        df_owner_write = df_owner_write.append(ownerObject, ignore_index=True)
        df_owner_write.to_sql('owner', SQL, index=False, if_exists='append')

        print('successfully insert 【' + name + '】, count=' + str(count))
        time.sleep(1)

    # 关闭数据库连接
    db.close()

#从数据库中获取视频信息（返回字典）
def get_video_object_from_sql(results,i,flag=True):
    if flag:
        videoObject = {'bvid': results[i][9], 'tname': results[i][3], 'title': results[i][5],
                       'pubdate': results[i][6], 'desc': results[i][7], 'owner': results[i][11],
                       'view': results[i][12], 'danmaku': results[i][13], 'reply': results[i][14],
                       'favorite': results[i][15], 'coin': results[i][16], 'share': results[i][17],
                       'his_rank': results[i][18], 'like': results[i][19], 'pic': results[i][4],
                       'rcmd_reason': results[i][10], 'duration': results[i][23]}
        if results[i][20] != '':
            if '$' in str(results[i][20]):
                tag_string = results[i][20].split('$')
                tagList = []
                for j in tag_string:
                    tagList.append(j)
                videoObject['tag'] = tagList
            else:
                videoObject['tag'] = results[i][19]

        if results[i][21] is not None and results[i][21] != '-':
            staff_string = results[i][21].split('$')
            staffList = []
            for j in range(0, len(staff_string) - 1, 2):
                staffObject = {'mid': staff_string[j], 'title': staff_string[j + 1]}
                staffList.append(staffObject)
            videoObject['staff'] = staffList

        if results[i][22] is not None and results[i][22] != '-':
            honor_string = results[i][22].split('$')
            honorList = []
            for j in honor_string:
                honorList.append(j)
            videoObject['honor'] = honorList
    else:
        videoObject = {'bvid': results[i][9], 'tname': results[i][3], 'title': results[i][5],
                       'pubdate': results[i][6], 'owner': results[i][11],
                       'view': results[i][12], 'danmaku': results[i][13],
                        'pic': results[i][4],
                       'duration': results[i][23]}

    return videoObject

#导出数据库中数据到json文件（视频&UP主）
def export_to_json_from_sql(flag):
    db = pymysql.connect(host='localhost', user='root', passwd='pwd', database='videoinfosql')
    cursor = db.cursor()

    if flag:
        sql = 'select * from owner'
        cursor.execute(sql)
        results = cursor.fetchall()

        upJson = {'updateTime': int(time.time())}
        upList = []
        for i in range(0, len(results)):
            upObject = {'mid': results[i][0], 'name': results[i][1]}
            upList.append(upObject)
        upJson['data'] = upList
        dump_f = open(UP_DATA, 'w', encoding="utf8")
        json.dump(upJson, dump_f, ensure_ascii=False)
    else:
        sql = 'select * from video'
        cursor.execute(sql)
        results = cursor.fetchall()
        videoJson = {'updateTime': int(time.time())}
        videoList = []
        for i in range(0, len(results)):
            videoObject=get_video_object_from_sql(results,i)
            videoList.append(videoObject)
        videoJson['data'] = videoList
        dump_f = open(VIDEO_DATA, 'w', encoding="utf8")
        json.dump(videoJson, dump_f, ensure_ascii=False)

#获取视频持续时间
def get_duration(bvid):
    while True:
        try:
            info = get_videos_info(bvid)
            return info['duration']
        except TimeoutError:
            time.sleep(10)
        except ConnectTimeout:
            time.sleep(10)
        except ChunkedEncodingError:
            time.sleep(10)
        except ResponseCodeException:
            return 0

#更新视频信息（持续时间）（写入数据库）
def get_duration_sql(start):
    db = pymysql.connect(host='localhost', user='root', passwd='pwd', database='videoinfosql')
    cursor = db.cursor()
    sql = 'select bvid from video'
    cursor.execute(sql)
    results = cursor.fetchall()
    for i in range(start, len(results)):
        dur = get_duration(results[i][0])
        update = 'update video set duration=' + str(dur) + ' where bvid=\'' + results[i][0] + '\''
        cursor.execute(update)
        db.commit()  # 执行update操作时需要写这个，否则就会更新不成功
        print(update + ' count=' + str(i + 1))
        # time.sleep(0.1)

#根据不同分区导出不同json
def export_json_from_sql_by_zone():
    load_f = codecs.open(VIDEO_ZONE, 'r', encoding="utf8")
    zoneJson = json.load(load_f)
    db = pymysql.connect(host='localhost', user='root', passwd='pwd', database='videoinfosql')
    cursor = db.cursor()
    for i in range(0,len(zoneJson['data'])):
        video_json_str='data/video_'+zoneJson['data'][i]['name']+'.json'
        video_list=[]
        video_sub_list=[]
        if 'sub' in zoneJson['data'][i] and len(zoneJson['data'][i]['sub'])>0:
            for j in range(0,len(zoneJson['data'][i]['sub'])):
                sql='select * from video where tname=\''+zoneJson['data'][i]['sub'][j]['name']+'\''
                cursor.execute(sql)
                results = cursor.fetchall()
                for k in range(0, len(results)):
                    videoObject = get_video_object_from_sql(results,k,False)
                    video_list.append(videoObject)
        video_json={'data':video_list}
        dump_f = open(video_json_str, 'w', encoding="utf8")
        json.dump(video_json, dump_f, ensure_ascii=False)

if __name__ == '__main__':
    # get_weekly(196,207,True)
    # get_weekly_sql(208,208)
    # get_rank_sql("Kitchen")
    # get_rank_sql("all")
    # print(get_videos_info("BV1Y24y1G7if"))
    # get_followings_sql(True,530,530)
    # get_followings_sql(False,9,FOLLOWINGS_2_MAX)
    # CREDENTIAL = Credential(SESSDATA, bili_jct, buvid3, DedeUserID)
    # USER = user.User(276281827, credential=CREDENTIAL)
    # print(sync(USER.get_user_info()))
    # get_up_sql(163732)
    # export_to_json_from_sql(True)
    # get_duration_sql(155477)
    export_json_from_sql_by_zone()
