import json

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
num_rows=10000
block_size=1000

# 逐块读取稀疏矩阵并拼接
for i in range(0, num_rows, block_size):
    j = min(i + block_size, num_rows)
    # rb for read in binary
    with open('data/user_video/user_video_matrix_{}_{}.pkl'.format(i, j), 'rb') as f:
        if i == 0:
            user_video_matrix = pd.read_pickle(f, compression='zstd')
            # dtype use int16 to decrease memory using
            user_video_matrix = sparse.csr_matrix(user_video_matrix, dtype=np.int16)
        else:
            matrix_block = pd.read_pickle(f, compression='zstd')
            matrix_block = sparse.csr_matrix(matrix_block, dtype=np.int16)
            user_video_matrix = sparse.vstack([user_video_matrix, matrix_block])

user_video_matrix = user_video_matrix.transpose()  # 转置稀疏矩阵，保证行向量为视频
K = 18
# 划分数据集
X_train, X_test = train_test_split(user_video_matrix, test_size=0.7, random_state=42)
kmeans = KMeans(n_clusters=K,random_state=42)  # 设置聚类数量K
kmeans.fit(X_train)  # 执行K-means算法

cluster_centers = kmeans.cluster_centers_  # 获取聚类中心
labels = kmeans.labels_  # 获取每个视频所属的聚类标签

# 将 cluster_centers 转换为可序列化的对象
cluster_centers_serializable = cluster_centers.tolist()

# 将 labels 转换为可序列化的对象
labels_serializable = labels.tolist()

# 构建保存的数据字典
data = {
    'cluster_centers': cluster_centers_serializable,
    'labels': labels_serializable
}

# 保存为 JSON 文件
with open('data/video_cluster.json', 'w') as f:
    json.dump(data, f)

load_f = open('data/title_list.json', 'r', encoding='utf8')
title_list = json.load(load_f)['data']

# 测试输出聚类结果
for i in range(K):
    cluster_videos = [video for video, label in zip(title_list, labels) if label == i]
    print(f"Cluster {i + 1}:")
    for video in cluster_videos:
        print(video)
    print("--------------------")