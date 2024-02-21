import json
import codecs

load_f = codecs.open('data/video.json', 'r', encoding="utf8")
videoJson = json.load(load_f)
video_list = videoJson['data']

bvid_index_map = {}
# 构建哈希表（bv号→索引）
for i, video in enumerate(video_list):
    bvid = video['bvid']
    bvid_index_map[bvid] = i
dump_f = open('data/video_dict.json', 'w', encoding="utf8")
json.dump(bvid_index_map, dump_f, ensure_ascii=False)