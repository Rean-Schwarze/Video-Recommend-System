import codecs
import json
import random
import pandas as pd
import numpy as np
from scipy import sparse
import multiprocessing as mp
import time

load_f = codecs.open('data/video.json', 'r', encoding="utf8")
videoJson = json.load(load_f)
updateTime = videoJson['updateTime']
video_list = videoJson['data']
num_videos = 100000 # 为了防止内存不够，数量减少为10w来模拟（
num_users = 10000
block_size = 1000  # 分块的大小，即每个块的行数和列数均为原来的十分之一

# 确定每个小块的行数和列数
rows_per_block = num_users // 10
cols_per_block = num_videos // 10

if __name__ == '__main__':
    # 生成每个用户的兴趣列表，防止因不同视频数量有差异导致模拟结果过于类似
    user_interests = []
    load_zc = codecs.open('data/zone_count.json', 'r', encoding="utf8")
    zone_count_json = json.load(load_zc)
    zone_list = zone_count_json['zone']
    num_zones = len(zone_list)
    for user_id in range(num_users):
        # 随机生成每个用户对各个分区的兴趣程度
        interests = [random.uniform(0, 1) for _ in range(num_zones)]
        total_interest = sum(interests)
        # 将兴趣程度归一化为概率分布
        interests = [interest / total_interest for interest in interests]
        user_interests.append(interests)
    for i in range(0, num_users, block_size):
        with codecs.open('data/user_video/user_video_matrix_' + str(i) + '_' + str(i + block_size) + '.pkl', 'wb') as f:
            j = min(i + block_size, num_users)
            # watch_history = np.array([[random.randint(0, 1) * random.randint(0, int((updateTime-video_list[k]['pubdate'])/3600)) for k
            #                            in range(num_videos)] for l in range(i, j)])#0代表没有观看，1代表观看了，乘以观看时间（在收集时间与视频发布时间的差值中(/3600s)随机生成）
            block_watch_history = []
            for user_id in range(i, j):
                interests = user_interests[user_id]
                videos_watched = []
                for video_id in range(num_videos):
                    # 根据兴趣分布来确定观看视频的分区
                    zone = video_list[video_id]['tname']
                    index = zone_list.index(zone)
                    random_value = random.uniform(0, max(interests))#生成随机数
                    if random_value >= interests[index]:#如果随机数高于兴趣值
                        # 观看视频
                        videos_watched.append(
                            random.randint(0, int((updateTime - video_list[video_id]['pubdate']) / 3600)))
                    else:
                        videos_watched.append(0)
                block_watch_history.append(videos_watched)
            # 转化为稀疏矩阵，便于后续读取
            block_sparse = sparse.csr_matrix(block_watch_history)
            #use zstd compression to decrease the size of files
            pd.to_pickle(block_sparse, f, compression='zstd')
