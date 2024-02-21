import codecs
import math
import os
import sys
import webbrowser
from functools import partial

import matplotlib
import pandas as pd
import numpy as np
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QSize, pyqtSignal, QStringListModel
from PyQt5.QtWidgets import QPushButton, QLabel, QFrame, QProgressBar, QMainWindow, QApplication, QStackedWidget, \
    QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtWinExtras import QtWin
from scipy import sparse
from win32mica import ApplyMica, MICAMODE
from module.blurwindow import ExtendFrameIntoClientArea, GlobalBlur
import darkdetect
from light import *

import requests
import json
import time
import random

import statsmodels.api as sm
import matplotlib.pyplot as plt

HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'referer': 'https://www.bilibili.com/',
    'x-csrf-token': '',
    'x-requested-with': 'XMLHttpRequest',
    'cookie': '',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/90.0.4430.212 Safari/537.36'
}
VIDEO_URL = 'https://www.bilibili.com/video/'
UP_URL = 'https://space.bilibili.com/'
ZONE_LIST = ['番剧', '国创', '动画', '游戏', '鬼畜', '音乐', '舞蹈', '影视', '娱乐', '知识', '科技', '资讯', '美食',
             '生活', '汽车', '时尚', '运动', '动物圈']


class Button(QPushButton):
    entered = pyqtSignal()
    leaved = pyqtSignal()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.entered.emit()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.leaved.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # MICA FOR WINDOW
        hwnd = self.winId().__int__()
        mode = MICAMODE.DARK
        mode = MICAMODE.LIGHT
        mode = darkdetect.isDark()
        ApplyMica(hwnd, mode)

        # MICA FOR MENUS
        def ApplyMenuBlur(hwnd: int):
            hwnd = int(hwnd)
            if darkdetect.isDark() == True:
                GlobalBlur(hwnd, Acrylic=True, hexColor="#21212140", Dark=True, smallCorners=True)
            else:
                GlobalBlur(hwnd, Acrylic=True, hexColor="#faf7f740", Dark=True, smallCorners=True)

        self.setAttribute(Qt.WA_TranslucentBackground)
        if QtWin.isCompositionEnabled():
            QtWin.extendFrameIntoClientArea(self, -1, -1, -1, -1)
        else:
            QtWin.resetExtendedFrame(self)

        # CUSTOM LIST IN COMBOBOX
        self.ui.listview = QtWidgets.QListView()
        self.ui.user_comboBox.setView(self.ui.listview)

        self.ui.user_comboBox.view().window().setWindowFlags(
            Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.ui.user_comboBox.view().window().setAttribute(Qt.WA_TranslucentBackground)
        self.ui.user_comboBox.setCurrentIndex(-1)
        ApplyMenuBlur(self.ui.user_comboBox.view().window().winId().__int__())

        #各个stackedWidget内窗口初始化
        self.home_init()
        self.ui.user_comboBox.addItem('默认')
        for i in range(1, 10001):
            self.ui.user_comboBox.addItem(str(i))
        self.ui.user_comboBox.currentIndexChanged.connect(self.combobox_index_change)
        self.video_init()
        self.user_init()
        self.ui.stackedWidget.setCurrentIndex(0)

        self.show()

    #控制侧边栏状态
    sideFlag = True

    #展开按钮的槽函数
    def onExpandClicked(self):
        if self.sideFlag:
            self.expand_sidebar()
        else:
            self.collapse_sidebar()

    #展开侧边栏
    def expand_sidebar(self):
        anim = QPropertyAnimation(self.ui.sidebar)
        anim.setTargetObject(self.ui.sidebar)
        anim.setPropertyName(b'size')#IMPORTANT
        anim.setDuration(50)#动画持续时间
        anim.setStartValue(QSize(60, 720))#起始值
        anim.setEndValue(QSize(180, 720))#结束值
        anim.start()
        #改变按钮图标
        self.ui.foldBtn.setStyleSheet("QPushButton\n"
                                      "{\n"
                                      "background-color: transparent;\n"
                                      "border-radius:31px;\n"
                                      "border-image: url(:/icon/fold.png)\n"
                                      "}\n"
                                      "\n"
                                      "QPushButton:pressed\n"
                                      "{\n"
                                      "border-image: url(:/icon/fold_selected.png)\n"
                                      "}")
        #改变侧边栏状态
        self.sideFlag = False

    #收起侧边栏
    def collapse_sidebar(self):
        anim = QPropertyAnimation(self.ui.sidebar)
        anim.setTargetObject(self.ui.sidebar)
        anim.setPropertyName(b'size')
        anim.setDuration(50)
        anim.setStartValue(QSize(180, 720))
        anim.setEndValue(QSize(60, 720))
        anim.start()
        self.ui.foldBtn.setStyleSheet("QPushButton\n"
                                      "{\n"
                                      "background-color: transparent;\n"
                                      "border-radius:31px;\n"
                                      "border-image: url(:/icon/unfold.png)\n"
                                      "}\n"
                                      "\n"
                                      "QPushButton:pressed\n"
                                      "{\n"
                                      "border-image: url(:/icon/unfold_selected.png)\n"
                                      "}")
        self.sideFlag = True

    #不同用处字体
    font_title = QtGui.QFont()
    font_title.setFamily("阿里巴巴普惠体 2.0 55 Regular")
    font_title.setPointSize(9)
    font_title.setBold(False)

    font_up = QtGui.QFont()
    font_up.setFamily("阿里巴巴普惠体 2.0 55 Regular")
    font_up.setPointSize(7)
    font_up.setBold(False)

    font_info = QtGui.QFont()
    font_info.setFamily("阿里巴巴普惠体 2.0 65 Medium")
    font_info.setPointSize(7)
    font_info.setBold(False)

    font_zone = QtGui.QFont()
    font_zone.setFamily("阿里巴巴普惠体 2.0 65 Medium")
    font_zone.setPointSize(8)
    font_zone.setBold(False)

    # 数字单位转换
    def number_trans(self, number):
        def strofsize(num, level):
            if level >= 2:
                return num, level
            elif num >= 10000:
                num /= 10000
                level += 1
                return strofsize(num, level)
            else:
                return num, level

        units = ['', '万', '亿']
        num, level = strofsize(number, 0)
        if level > len(units):
            level -= 1
        return '{}{}'.format(round(num, 2), units[level])

    # 时间戳转换
    def duration_trans(self, dur):
        if dur < 3600:
            return time.strftime("%M:%S", time.gmtime(int(dur)))
        else:
            return time.strftime("%H:%M:%S", time.gmtime(int(dur)))

    # 二分搜索（up主）
    def search_up_binary(self, up):
        load_f = codecs.open('../data/up.json', 'r', encoding="utf8")
        upJson = json.load(load_f)
        up_list = upJson['data']
        begin = 0
        end = len(up_list)
        while begin < end:
            middle = math.floor((end + begin) / 2)
            if up < up_list[middle]['mid']:
                end = middle
            elif up > up_list[middle]['mid']:
                begin = middle
            else:
                return up_list[middle]['name']

    # def on_btn_click(self, url, bvid):
    #     mouse_button = QApplication.mouseButtons()
    #     if mouse_button == Qt.LeftButton:
    #         self.open_url(url)
    #     elif mouse_button == Qt.RightButton:
    #         self.video_selected=bvid
    #         self.ui.predict_btn.setText('热度变化预测：'+bvid)

    #用浏览器打开视频，同时将所点击视频的bv号赋给video_selected
    def open_url(self, url, bvid):
        webbrowser.open(url, new=2, autoraise=True)
        self.video_selected = bvid
        self.ui.predict_btn.setText('热度变化预测：' + bvid)

    video_selected = ''

    #清空grid layout
    def clear_grid_layout(self, gridLayout):
        item_list = list(range(gridLayout.count()))
        item_list.reverse()  # 倒序删除，避免影响布局顺序

        for i in item_list:
            item = gridLayout.itemAt(i)
            gridLayout.removeItem(item)
            if item.widget():
                item.widget().deleteLater()

    #获取指定用户的推荐视频
    def get_recommended_video(self, id):
        # 从相似用户中获取推荐视频
        recommended_videos = []
        load_f = codecs.open('../data/user_similar.json', 'r', encoding="utf8")
        similarJson = json.load(load_f)
        similar_list = similarJson['data'][id]
        for user in similar_list:
            # 获取相似用户的观看记录
            user_history = self.user_video_matrix[user]

            # 找到相似用户观看的视频，并将其加入推荐列表
            videos = np.where(user_history.toarray() != 0)[1]
            recommended_videos.extend(videos)

        # 去除重复的视频并返回推荐结果
        recommended_videos = list(set(recommended_videos))
        return recommended_videos

    user_selected=0

    #点击comboBox不同用户时，将当前界面的视频替换为该用户的推荐视频
    def combobox_index_change(self, index):
        if index==0:
            self.home_init()
        else:
            self.user_selected=index
            recommended_videos = self.get_recommended_video(index-1)
            load_f = codecs.open('../data/video.json', 'r', encoding="utf8")
            videoJson = json.load(load_f)
            video_list = videoJson['data']
            self.put_video_to_grid_layout(self.ui.gridLayout, video_list, recommended_videos)

    #首页初始化
    def home_init(self):
        self.clear_grid_layout(self.ui.gridLayout)
        if self.user_selected==0:
            load_f = codecs.open('../data/video.json', 'r', encoding="utf8")
            videoJson = json.load(load_f)
            video_list = videoJson['data']
            total_video = len(video_list)
            self.ui.home_label.setText('更新时间：' + time.strftime("%Y-%m-%d  %H:%M:%S", time.localtime(
                videoJson['updateTime'])) + '\n视频总量：' + str(total_video))
            self.put_video_to_grid_layout(self.ui.gridLayout, video_list)
        else:
            self.combobox_index_change(self.user_selected)

    #点击侧边栏不同按钮，切换到对应窗口
    def home_show(self):
        self.ui.stackedWidget.setCurrentIndex(0)

    def video_show(self):
        self.ui.stackedWidget.setCurrentIndex(1)

    def user_show(self):
        self.ui.stackedWidget.setCurrentIndex(2)

    def analyze_show(self):
        self.ui.stackedWidget.setCurrentIndex(3)

    current_zone = ''

    #针对中英文混合时的textwrap，将2个英文/数字字符视为1个
    def textwrap_ch_en(self, text, max_width):
        wrap_text = ''
        len = 0
        for char in text:
            unicode_value = ord(char)#获取每个字符的unicode编码
            #如果落在中文字符的范围内
            if 19968 <= unicode_value <= 40959 or 12288 <= unicode_value <= 12351:
                len += 1
                wrap_text += char
            else:
                len += 0.5
                wrap_text += char
            if len >= max_width:
                len = 0
                wrap_text += '\n'
        return wrap_text

    #将视频放入grid layout中
    def put_video_to_grid_layout(self, gridLayout, video_list, recommended_video_list=None):
        if recommended_video_list is None:
            recommended_video_list = []
            video_list_random = random.sample(range(0, len(video_list) - 1), 8)
        else:
            #防止推荐视频不够8个（
            if len(recommended_video_list) < 8:
                video_list_random = random.sample(range(0, len(recommended_video_list) - 1),
                                                  len(recommended_video_list)-1)
            else:
                video_list_random = random.sample(range(0, len(recommended_video_list) - 1), 8)
        self.clear_grid_layout(gridLayout)

        pic_btn_list = []
        title_btn_list = []
        up_btn_list = []

        count = 0
        for i in video_list_random:
            bvid = video_list[i]['bvid']
            url = video_list[i]['pic']
            title = video_list[i]['title']
            title = self.textwrap_ch_en(title, 13)
            pubdate = video_list[i]['pubdate']
            owner = video_list[i]['owner']
            view = video_list[i]['view']
            danmaku = video_list[i]['danmaku']
            duration = video_list[i]['duration']
            img_name = str(url).split('/')[5]
            img_path = 'cache/' + img_name
            #如果当前视频的封面没有获取过，才进行获取
            if not os.path.exists(img_path):
                img_content = requests.get(url, headers=HEADERS).content
                with open(img_path, 'wb') as f:
                    f.write(img_content)

            #vertical layout，从上到下分别为封面、标题、up主及发布时间
            vertical_layout_widget = QtWidgets.QWidget()
            vertical_layout_widget.setFixedSize(265, 240)
            vertical_layout = QtWidgets.QVBoxLayout(vertical_layout_widget)
            vertical_layout.setContentsMargins(0, 0, 0, 0)
            vertical_layout.setSpacing(11)

            #封面，包括图片、播放、弹幕、视频时长
            pic_widget = QtWidgets.QWidget()
            pic_widget.setFixedSize(265, 150)
            picBtn = Button(pic_widget)
            picBtn.setFixedSize(265, 150)
            picBtn.setMinimumSize(QSize(265, 150))
            picBtn.setStyleSheet("QPushButton {\n"
                                 "    border-image: url(" + img_path + ");\n"
                                                                       "    border-image-repeat: scale;\n"
                                                                       "    border: 1px solid rgb(0, 0, 0, 13);\n"
                                                                       "    border-radius: 7px;\n"
                                                                       "}\n"
                                 )
            pic_label_widget = QtWidgets.QWidget(pic_widget)
            pic_label_widget.setGeometry(0, 120, 265, 30)
            pic_btn_list.append(picBtn)
            #使用partial传参，才能正确将每一个视频的按钮连接到正确的槽函数
            pic_btn_list[count].clicked.connect(partial(self.open_url, VIDEO_URL + bvid, bvid))
            pic_label_bg = QtWidgets.QLabel(pic_label_widget)
            pic_label_bg.setGeometry(0, 0, 265, 30)
            pic_label_bg.setStyleSheet("background-color: rgba(0, 0, 0, 60);\n"
                                       "    border: 1px solid rgb(0, 0, 0, 13);\n"
                                       "    border-radius: 7px;")
            pic_label_view_icon = QtWidgets.QLabel(pic_label_widget)
            pic_label_view_icon.setGeometry(12, 8, 17, 14)
            pic_label_view_icon.setStyleSheet("border-image:url(:/icon/view.png);")
            pic_label_view_text = QtWidgets.QLabel(pic_label_widget)
            pic_label_view_text.setGeometry(35, 8, 60, 14)
            pic_label_view_text.setFont(self.font_info)
            pic_label_view_text.setStyleSheet("background-color:transparent;\ncolor:white;")
            pic_label_view_text.setText(str(self.number_trans(view)))
            pic_label_danmaku_icon = QtWidgets.QLabel(pic_label_widget)
            pic_label_danmaku_icon.setGeometry(105, 8, 17, 14)
            pic_label_danmaku_icon.setStyleSheet("border-image:url(:/icon/danmaku.png);")
            pic_label_danmaku_text = QtWidgets.QLabel(pic_label_widget)
            pic_label_danmaku_text.setGeometry(130, 8, 50, 14)
            pic_label_danmaku_text.setFont(self.font_info)
            pic_label_danmaku_text.setStyleSheet("background-color:transparent;\ncolor:white;")
            pic_label_danmaku_text.setText(str(self.number_trans(danmaku)))
            pic_label_duration_text = QtWidgets.QLabel(pic_label_widget)
            pic_label_duration_text.setGeometry(180, 8, 75, 14)
            pic_label_duration_text.setFont(self.font_info)
            pic_label_duration_text.setStyleSheet("background-color:transparent;\ncolor:white;")
            pic_label_duration_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pic_label_duration_text.setText(str(self.duration_trans(duration)))
            vertical_layout.addWidget(pic_widget, 0)

            title_btn = QtWidgets.QPushButton()
            title_btn.setFixedSize(265, 46)
            title_btn.setText(title)
            title_btn.setFont(self.font_title)
            title_btn.setStyleSheet("QPushButton {\n"
                                    "text-align: left;\n"
                                    "color: black;\n"
                                    "}\n"

                                    "QPushButton:hover {\n"
                                    "color: rgb(0, 174, 236);\n"
                                    "}\n"

                                    "QPushButton::pressed {\n"
                                    "color: rgb(0, 174, 236);\n"
                                    "}\n")
            title_btn_list.append(title_btn)
            title_btn_list[count].clicked.connect(partial(self.open_url, VIDEO_URL + bvid, bvid))
            vertical_layout.addWidget(title_btn, 1)

            up_widget = QtWidgets.QWidget()
            up_icon = QtWidgets.QLabel(up_widget)
            up_icon.setGeometry(0, 2, 17, 14)
            up_icon.setStyleSheet("border-image:url(:/icon/up.png);")
            up_btn = QtWidgets.QPushButton(up_widget)
            up_btn.setGeometry(20, 0, 245, 18)
            up_btn.setFont(self.font_up)
            up_btn.setStyleSheet("QPushButton {\n"
                                 "text-align: left;\n"
                                 # "text-align: top;\n"
                                 "color: rgb(111, 116, 123);\n"
                                 "}\n"

                                 "QPushButton:hover {\n"
                                 "color: rgb(0, 174, 236);\n"
                                 "}\n"

                                 "QPushButton::pressed {\n"
                                 "color: rgb(0, 174, 236);\n"
                                 "}\n")
            up_btn.setText(self.search_up_binary(owner) + ' · ' + time.strftime("%Y-%m-%d", time.localtime(pubdate)))
            up_btn_list.append(up_btn)
            up_btn_list[count].clicked.connect(partial(self.open_url, UP_URL + str(owner)))
            vertical_layout.addWidget(up_widget, 2)

            #第1~8个视频分别从左到右、从上到下放入grid layout
            gridLayout.addWidget(vertical_layout_widget, math.floor(count / 4), math.floor(count % 4),
                                 Qt.AlignTop)
            count += 1

    def get_video_list_by_currnet_zone(self):
        load_f = codecs.open('../data/video_' + self.current_zone + '.json', 'r', encoding="utf8")
        videoJson = json.load(load_f)
        return videoJson['data']

    #分区按钮点击时的槽函数
    def zone_btn_clicked(self, zone):
        self.current_zone = zone
        self.put_video_to_grid_layout(self.ui.gridLayout_video_main, self.get_video_list_by_currnet_zone())

    def refresh_video_btn_clicked(self):
        self.put_video_to_grid_layout(self.ui.gridLayout_video_main, self.get_video_list_by_currnet_zone())

    #视频总览窗口初始化
    def video_init(self):
        self.clear_grid_layout(self.ui.gridLayout_video_button)
        self.clear_grid_layout(self.ui.gridLayout_video_main)

        zone_btn_list = []

        for i in range(0, len(ZONE_LIST)):
            zone_btn = QtWidgets.QPushButton()
            zone_btn.setFixedSize(105, 40)
            zone_btn.setFont(self.font_zone)
            zone_btn.setText(ZONE_LIST[i])
            zone_btn.setStyleSheet("QPushButton {\n"
                                   "background-color: rgb(246, 247, 248);\n"
                                   "border: 1px solid rgb(0, 0, 0, 13);\n"
                                   "border-radius: 7px;\n"
                                   "min-height: 40px;\n"
                                   "max-height: 38px;\n"
                                   "}\n"

                                   "QPushButton:hover {\n"
                                   "background-color: rgb(226, 228, 230);\n"
                                   "border: 1px solid rgb(0, 0, 0, 13);\n"
                                   "}\n"

                                   "QPushButton::pressed {\n"
                                   "color: rgb(0, 0, 0, 150);\n"
                                   "}\n")
            zone_btn_list.append(zone_btn)
            zone_btn.clicked.connect(partial(self.zone_btn_clicked, ZONE_LIST[i]))
            self.ui.gridLayout_video_button.addWidget(zone_btn, math.floor(i / 9), math.floor(i % 9))

    user_list = []
    user_video_matrix = sparse.csr_matrix((10000, 100000))

    # 读取用户观看视频矩阵
    def read_sparse_matrix_from_blocks(self, num_rows, num_cols, block_size):
        # 逐块读取稀疏矩阵并拼接
        for i in range(0, num_rows, block_size):
            j = min(i + block_size, num_rows)
            with open('../data/user_video/user_video_matrix_{}_{}.pkl'.format(i, j), 'rb') as f:
                if i == 0:
                    result = pd.read_pickle(f, compression='zstd')
                    result = sparse.csr_matrix(result, dtype=np.int16)
                else:
                    matrix_block = pd.read_pickle(f, compression='zstd')
                    matrix_block = sparse.csr_matrix(matrix_block, dtype=np.int16)
                    result = sparse.vstack([result, matrix_block])

        return result

    model_list_video = QStringListModel()
    model_list_similar = QStringListModel()

    #用户列表每一项被点击时的槽函数
    def user_list_clicked(self, qModelIndex):
        #先清空listview中原有内容
        self.model_list_video.removeRows(0, self.model_list_video.rowCount())
        self.model_list_similar.removeRows(0, self.model_list_similar.rowCount())
        watch_video_info_list = []
        load_f = codecs.open('../data/video.json', 'r', encoding="utf8")
        videoJson = json.load(load_f)
        video_list = videoJson['data']
        video_count = {}
        row = int(self.user_list[qModelIndex.row()]) - 1
        for i in range(0, self.user_video_matrix.shape[1]):
            if self.user_video_matrix[row, i] != 0:
                tagString = ''
                zone = video_list[i]['tname']
                if zone in video_count:
                    video_count[zone] += 1
                else:
                    video_count[zone]=1
                if 'tag' in video_list[i]:
                    tag_list = video_list[i]['tag']
                    if isinstance(tag_list, list):
                        for k in range(0, len(tag_list)):
                            tagString += tag_list[k]
                            if k != (len(tag_list) - 1):
                                tagString += ' | '
                info = ('【标题】：' + video_list[i]['title'] + '\n【分区】：' + video_list[i][
                    'tname'] + '\n【标签】：' + tagString)
                watch_video_info_list.append(info)
        self.model_list_video.setStringList(watch_video_info_list)
        self.ui.listView_video.setModel(self.model_list_video)
        # 找到视频数量最多的分区
        max_counts = sorted(video_count.values(), reverse=True)[:3]  # 获取前三个最大的值
        most_zones = [zone for zone, count in video_count.items() if count in max_counts][:3]
        most_zone_string = ' | '.join(most_zones)
        self.ui.video_count_label.setText('观看视频最多：' + most_zone_string)
        #获取相似用户
        load_f = codecs.open('../data/user_similar.json', 'r', encoding="utf8")
        similarJson = json.load(load_f)
        #获取json中对应用户的行向量，转换为list，同时通过map将数据类型转换为str，便于加入listview的model中
        similar_list = list(map(str,similarJson['data'][row]))
        self.model_list_similar.setStringList(similar_list)
        self.ui.listView_similar.setModel(self.model_list_similar)
        self.ui.similar_count_label.setText('相似用户数：'+str(len(similar_list)))

    #用户总览窗口初始化
    def user_init(self):
        model = QStringListModel()
        for i in range(1, 10001):
            self.user_list.append(str(i))

        # 设置模型列表视图，加载数据列表
        model.setStringList(self.user_list)

        # 设置列表视图的模型
        self.ui.listView_user.setModel(model)
        self.ui.listView_user.clicked.connect(self.user_list_clicked)
        #读取分块的稀疏矩阵到内存中
        self.user_video_matrix = self.read_sparse_matrix_from_blocks(10000, 100000, 1000)

    #通过字典（哈希表）获取bv号对应的索引
    def get_bvid_index(self, bvid):
        load_f = codecs.open('../data/video_dict.json', 'r', encoding='utf8')
        bvid_dict = json.load(load_f)
        return bvid_dict[bvid]

    #根据传入data不同，获取不同数据
    def get_data_in_json(self, index, data, flag=True):
        load_f = codecs.open('../data/video.json', 'r', encoding="utf8")
        videoJson = json.load(load_f)
        video_list = videoJson['data']
        if flag:
            return video_list[index][data]
        else:
            return videoJson['updateTime']

    #视频热度预测
    def predict_video(self):
        bvid=self.video_selected
        if bvid=='':
            QMessageBox.information(self, '提示', '当前尚未选择视频！')
            return
        elif self.get_bvid_index(bvid)>100000:
            QMessageBox.information(self, '提示', '该视频暂不支持热度预测！')
        else:
            video_vector = self.user_video_matrix.getcol(self.get_bvid_index(bvid)).toarray().flatten()  # 获取目标用户向量
            #原本稀疏矩阵为了压缩使用int16，这里需要还原为int32，这样计算出来的时间戳才不会溢出
            video_vector=video_vector.astype(np.int32)
            pubdate = self.get_data_in_json(self.get_bvid_index(bvid),'pubdate')
            current_time = self.get_data_in_json(self.get_bvid_index(bvid),'updateTime', False)
            title=self.get_data_in_json(self.get_bvid_index(bvid),'title')
            #将行向量中数据还原为正确的时间戳
            for i in range(len(video_vector)):
                if video_vector[i] != 0:
                    video_vector[i] = video_vector[i] * 3600 + pubdate
            # 假设时间窗口大小为 delta_t（秒）(1 day)
            delta_t = 3600*24
            # 统计时间窗口内的观看次数
            n=14
            X= np.arange(1, n+1)
            view_count = [0 for _ in range(n)]
            heat = [0 for _ in range(n)]
            for timestamp in video_vector:
                # 判断观看时间是否在时间窗口内
                for i in range(n):
                    if delta_t >= current_time - i * 3600*24 - timestamp > 0:
                        view_count[i] += 1
            # 进行观看热度的计算
            for i in range(n):
                heat[i] = view_count[i] / delta_t  # 观看次数除以时间窗口大小

            # 拟合回归模型
            model = sm.OLS(heat, sm.add_constant(X))
            result = model.fit()

            # 预测未来值
            X_new = np.arange(n+1,n+15)  # 用于预测的新相关变量
            X_new = sm.add_constant(X_new)
            forecast = result.predict(X_new)  # 预测未来值

            # 绘制统计值和预测值的图表
            plt.figure(figsize=(10, 5))
            # 设置中文字体
            matplotlib.rcParams['font.family'] = 'Microsoft YaHei'

            # 绘制统计值的图表
            plt.subplot(2, 1, 1)
            plt.plot(X, heat, 'bo-', label='Observation')
            plt.xlabel('Time(Day)')
            plt.ylabel('Heat')
            plt.title('Observation Heat\n'+title)

            # 绘制预测值的图表
            plt.subplot(2, 1, 2)
            plt.plot(X_new[:, 1], forecast, 'ro-', label='Prediction')
            plt.xlabel('Time(Day)')
            plt.ylabel('Heat')
            plt.title('Prediction Heat\n'+title)

            # 设置刻度保持一致
            plt.xlim(1, n + 14)
            plt.ylim(0, max(max(heat), max(forecast)))

            # 显示图表
            plt.tight_layout()
            plt.show()

    model_list_cluster = QStringListModel()
    model_list_cluster_detail = QStringListModel()
    cluster_selection=''

    #聚类分析listview中每一项被点击时的槽函数
    def cluster_list_clicked(self,qModelIndex):
        if self.cluster_selection=='user':
            i=qModelIndex.row()+1
        else:
            i=qModelIndex.row()
        with open('../data/'+self.cluster_selection+'_cluster.json', 'r') as f:
            data = json.load(f)
        # 提取 cluster_centers 和 labels 数据
        cluster_centers_serializable = data['cluster_centers']
        labels_serializable = data['labels']
        # 将数据转换为相应的类型
        cluster_centers = np.array(cluster_centers_serializable)
        labels = np.array(labels_serializable)
        cluster_detail_list = []
        #根据当前选择聚类分析的类型进行不同的数据读取
        if self.cluster_selection=='video':
            load_f = open('../data/title_list.json', 'r', encoding='utf8')
            title_list = json.load(load_f)['data']
            cluster_videos = [video for video, label in zip(title_list, labels) if label == i]
            for video in cluster_videos:
                cluster_detail_list.append(video)
        elif self.cluster_selection=='user':
            user_list=np.arange(1, 10001)
            cluster_users = [user for user, label in zip(user_list, labels) if label == i]
            for user in cluster_users:
                cluster_detail_list.append(str(user))
        self.model_list_cluster_detail.setStringList(cluster_detail_list)
        self.ui.listView_cluster_detail.setModel(self.model_list_cluster_detail)

    # 视频聚类分析按钮的槽函数
    def video_cluster(self):
        self.cluster_selection='video'
        #先清空当前listview
        self.model_list_cluster.removeRows(0, self.model_list_cluster.rowCount())
        self.model_list_cluster_detail.removeRows(0, self.model_list_cluster_detail.rowCount())
        cluster_list=[]
        # 共 18 个簇
        for i in range(1,19):
            cluster_list.append('簇'+str(i))
        self.model_list_cluster.setStringList(cluster_list)
        self.ui.listView_cluster.setModel(self.model_list_cluster)
        self.ui.listView_cluster.clicked.connect(self.cluster_list_clicked)

    # 用户聚类分析按钮的槽函数
    def user_cluster(self):
        self.cluster_selection = 'user'
        self.model_list_cluster.removeRows(0, self.model_list_cluster.rowCount())
        self.model_list_cluster_detail.removeRows(0, self.model_list_cluster_detail.rowCount())
        cluster_list = []
        # 共 9 个簇
        for i in range(1, 10):
            cluster_list.append('簇' + str(i))
        self.model_list_cluster.setStringList(cluster_list)
        self.ui.listView_cluster.setModel(self.model_list_cluster)
        self.ui.listView_cluster.clicked.connect(self.cluster_list_clicked)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    centralwidget = MainWindow()
    sys.exit(app.exec_())