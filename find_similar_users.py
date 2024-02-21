import codecs
import json
import random
import time
import multiprocessing as mp
import pandas as pd
import numpy as np
from scipy import sparse
from annoy import AnnoyIndex


# 读取用户观看视频矩阵
def read_sparse_matrix_from_blocks(num_rows, num_cols, block_size):
    # 逐块读取稀疏矩阵并拼接
    result = None
    for i in range(0, num_rows, block_size):
        j = min(i + block_size, num_rows)
        with open('data/user_video/user_video_matrix_{}_{}.pkl'.format(i, j), 'rb') as f:
            matrix_block = pd.read_pickle(f, compression='zstd')
            matrix_block = sparse.csr_matrix(matrix_block, dtype=np.int16)
            if result is None:
                result = matrix_block
            else:
                result = sparse.vstack([result, matrix_block])
    return result

def build_annoy_index(matrix):
    num_users, num_videos = matrix.shape
    t = AnnoyIndex(num_videos, 'angular')  # 创建Annoy索引对象
    # 逐行向Annoy索引中添加向量
    for i in range(num_users):
        vector = matrix.getrow(i).toarray().flatten()  # 获取用户的向量
        t.add_item(i, vector)  # 向索引中添加向量
    t.build(n_trees=50)  # 构建索引
    return t

def find_similar_users(annoy_index, user_video_matrix, user_id, k=10):
    # 计算目标用户与其他用户之间的相似度
    user_vector = user_video_matrix.getrow(user_id).toarray().flatten()  # 获取目标用户向量
    # 使用Annoy索引查找相似用户
    similar_user_ids = annoy_index.get_nns_by_vector(user_vector, k + 1, search_k=-1, include_distances=False)[1:]
    return similar_user_ids


if __name__ == '__main__':
    user_video_matrix = read_sparse_matrix_from_blocks(10000, 100000, 1000)
    annoy_index = build_annoy_index(user_video_matrix)
    similarJson = {'updateTime': int(time.time())}
    # load_f=open('data/user_similar.json', 'r', encoding="utf8")
    # temp_json=json.load(load_f)
    # if 'data' in temp_json:
    #     similarList=temp_json['data']
    # else:
    similarList = []
    for i in range(0, 10000):
        list=find_similar_users(annoy_index,user_video_matrix, i)
        similarList.append(list)
        #每1000个用户保存一次，防止意外发生（
        if i%1000==0:
            similarJson['data'] = similarList
            dump_f = open('data/user_similar.json', 'w', encoding="utf8")
            json.dump(similarJson, dump_f, ensure_ascii=False)
    similarJson['data'] = similarList
    dump_f = open('data/user_similar.json', 'w', encoding="utf8")
    json.dump(similarJson, dump_f, ensure_ascii=False)
