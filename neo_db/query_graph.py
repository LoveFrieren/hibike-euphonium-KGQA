from neo_db.config import graph, CA_LIST, similar_words
from spider.show_profile import get_profile
import os
import json
import base64


def query(name):
    """
    用于前端“检索人物关系”页面。
    展示该人物的所有相关关系（包括指向别人的和别人指向他的），所以使用双向查询。
    """
    data = graph.run(
        "MATCH (p)-[r]->(n:Person {Name: '%s'}) RETURN p.Name, r.relation, n.Name, p.cate, n.cate "
        "UNION ALL "
        "MATCH (p:Person {Name: '%s'})-[r]->(n) RETURN p.Name, r.relation, n.Name, p.cate, n.cate" % (name, name)
    )
    data = list(data)
    return get_json_data(data)


def get_json_data(data):
    """
    将 Neo4j 查询结果转换为前端 ECharts 关系图所需的 JSON 格式。
    """
    json_data = {'data': [], "links": []}
    d = []

    # 提取所有节点并去重
    for i in data:
        d.append(i['p.Name'] + "_" + i['p.cate'])
        d.append(i['n.Name'] + "_" + i['n.cate'])
        d = list(set(d))

    name_dict = {}
    count = 0
    for j in d:
        j_array = j.split("_")
        data_item = {}
        name_dict[j_array[0]] = count
        count += 1
        data_item['name'] = j_array[0]
        # 如果类别不在 CA_LIST 中，默认归为"其他"(10)
        data_item['category'] = CA_LIST.get(j_array[1], 10)
        json_data['data'].append(data_item)

    # 提取所有关系连线
    for i in data:
        link_item = {}
        link_item['source'] = name_dict[i['p.Name']]
        link_item['target'] = name_dict[i['n.Name']]
        link_item['value'] = i['r.relation']
        json_data['links'].append(link_item)

    return json_data


def get_KGQA_answer(array):
    """
    核心问答逻辑。
    前提：Neo4j 数据库已进行双向互补存储（如同时存在 A-[:学妹]->B 和 B-[:学姐]->A）。
    逻辑：问“A的X是谁”，统一查找“谁是A的X”，即查找指向 A 的入边。
    """
    if not array:
        return [{"data": [], "links": []}, "未识别到有效实体", ""]

    data_array = []
    current_name = None

    for word in array:
        # 如果当前词是关系词（在 similar_words 字典中）
        if word in similar_words:
            if current_name:
                relation_type = similar_words[word]

                # 【统一查入边】：找 p，使得 p -[:relation_type]-> current_name
                cypher = (
                             "MATCH (n:Person {Name: '%s'})<-[r:%s]-(p:Person) "
                             "RETURN p.Name as `p.Name`, n.Name as `n.Name`, type(r) as `r.relation`, p.cate as `p.cate`, n.cate as `n.cate`"
                         ) % (current_name, relation_type)

                print(f"执行 Cypher: {cypher}")
                data = list(graph.run(cypher))
                print("查询结果:", data)

                if data:
                    data_array.extend(data)
                    # 多跳关键：下一轮查询的起点，应该是刚才找到的那个人 (p)
                    current_name = data[-1]['p.Name']
                else:
                    # 没查到数据，路断了，直接中断循环
                    break
        else:
            # 如果当前词是实体词（人名），更新 current_name
            current_name = word

    # 如果最终没有查到任何数据，返回结构一致的默认值，防止前端 JS 解析崩溃
    if not data_array:
        return [
            {"data": [], "links": []},
            "抱歉，知识图谱中没有找到相关信息。请检查实体名称或关系是否正确。",
            ""
        ]

    # 正常查到数据的处理逻辑
    try:
        # 取最后一次找到的人 (p) 作为展示图片和简介的对象
        target_name = str(data_array[-1]['p.Name'])

        with open("./spider/images/" + "%s.jpg" % target_name, "rb") as image:
            base64_data = base64.b64encode(image.read())
            b = str(base64_data)
            img_str = b.split("'")[1]
    except FileNotFoundError:
        # 如果图片不存在，返回空字符串，防止程序崩溃
        img_str = ""

    return [get_json_data(data_array), get_profile(target_name), img_str]


def get_answer_profile(name):
    """
    用于获取单个人物的简介和图片（Base64格式）。
    """
    try:
        with open("./spider/images/" + "%s.jpg" % str(name), "rb") as image:
            base64_data = base64.b64encode(image.read())
            b = str(base64_data)
            img_str = b.split("'")[1]
    except FileNotFoundError:
        img_str = ""
    return [get_profile(str(name)), img_str]