import json
import codecs

load_f = codecs.open('data/video.json', 'r', encoding="utf8")
videoJson = json.load(load_f)
video_list = videoJson['data']

zone_count = {}
zone_list=[]
#统计所有视频的分区总数
for i in range(len(video_list)):
    zone = video_list[i]['tname']
    if zone in zone_list:
        continue
    else:
        zone_list.append(zone)
zone_count['zone']=zone_list
dump_f = open('data/zone_count.json', 'w', encoding="utf8")
json.dump(zone_count, dump_f, ensure_ascii=False)