import requests
import os

# GitHub 仓库信息
repo_owner = 'Kengxxiao'  # 仓库拥有者
repo_name = 'ArknightsGameData'    # 仓库名称
file_path = 'zh_CN/gamedata/excel/roguelike_topic_table.json'  # 文件在仓库中的路径
data_path = 'assets/resource/data/roguelike_topic_table.json'  # 保存文件的路径
# GitHub API URL
url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}'

# 请求头，如果需要认证
headers = {}

# 发送请求
response = requests.get(url, headers=headers)

if response.status_code == 200:
    file_info = response.json()
    download_url = file_info['download_url']
    
    # 下载文件内容
    file_response = requests.get(download_url)
    
    if file_response.status_code == 200:
        # 保存文件到本地
        with open(os.path.basename(data_path), 'wb') as file:
            file.write(file_response.content)
        print(f"文件已下载: {os.path.basename(data_path)}")
    else:
        print(f"下载文件失败: {file_response.status_code}")
else:
    print(f"获取文件信息失败: {response.status_code}")

import json

def filter_relics(input_path, output_path):
    # 读取原始JSON数据
    with open(input_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # 创建新的数据结构
    filtered_data = {
        "details": {}
    }

    # 需要保留的主题列表
    target_topics = ["rogue_1", "rogue_2", "rogue_3", "rogue_4"]
    
    for topic in target_topics:
        # 获取原始主题数据
        original_topic = original_data['details'].get(topic)
        if not original_topic:
            continue
        
        # 创建过滤后的主题数据
        filtered_topic = {
            "items": {
                k: v for k, v in original_topic['items'].items()
                if v.get('type') == 'RELIC'
            }
        }
        
        # 将其他非items字段保留（如果需要可以取消注释）
        # filtered_topic = original_topic.copy()
        # filtered_topic['items'] = {k: v for k, v in original_topic['items'].items() if v['type'] == 'RELIC'}
        
        filtered_data['details'][topic] = filtered_topic
    
    # 写入新的JSON文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        print(f"精简后的JSON已保存至: {output_path}")

filter_relics(data_path, data_path)