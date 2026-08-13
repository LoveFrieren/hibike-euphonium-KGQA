import os
import json

# ==========================================
# 1. 配置路径
# ==========================================
BASE_DIR = r"C:\Users\Admin\PycharmProjects\京吹知识图谱"
RELATION_FILE = os.path.join(BASE_DIR, "raw_data", "relation.txt")
JSON_FILE = os.path.join(BASE_DIR, "spider", "json", "data.json")


# ==========================================
# 2. 获取性别逻辑 (直接从 JSON 读取)
# ==========================================
def get_gender(name, json_data):
    """直接从 JSON 数据中获取性别"""
    if name in json_data:
        # 直接读取“性别”字段，如果没找到则默认为“女”
        return json_data[name].get("性别", "女")
    else:
        print(f"⚠️ 警告: 在 data.json 中未找到 '{name}' 的信息，默认视为'女'")
        return "女"


# ==========================================
# 3. 关系反向映射逻辑
# ==========================================
def get_reverse_relation(relation, person_b_gender):
    """根据原始关系和B的性别，返回反向关系的名称"""

    # 无向关系 (双向同名)
    undirected = ["好友", "姬友", "青梅竹马", "同级生", "大号君同盟", "同班同学"]
    if relation in undirected:
        return relation

    # 固定反向
    if relation == "女友": return "男友"
    if relation == "男友": return "女友"
    if relation == "憧憬的人": return "被憧憬的人"
    if relation == "被憧憬的人": return "憧憬的人"
    if relation == "顾问": return "学生"
    if relation == "学生": return "顾问"

    # 性别依赖反向 (学长/学姐 -> 学弟/学妹)
    if relation in ["学长", "学姐"]:
        return "学弟" if person_b_gender == "男" else "学妹"
    if relation in ["学弟", "学妹"]:
        return "学长" if person_b_gender == "男" else "学姐"

    # 性别依赖反向 (哥哥/姐姐 -> 弟弟/妹妹)
    if relation in ["哥哥", "姐姐"]:
        return "弟弟" if person_b_gender == "男" else "妹妹"
    if relation in ["弟弟", "妹妹"]:
        return "哥哥" if person_b_gender == "男" else "姐姐"

    # 父母子女 (父亲/母亲 -> 儿子/女儿)
    if relation in ["父亲", "母亲"]:
        return "儿子" if person_b_gender == "男" else "女儿"
    if relation == "女儿":
        return "父亲" if person_b_gender == "男" else "母亲"
    if relation == "儿子":
        return "父亲" if person_b_gender == "男" else "母亲"

    return relation  # 默认不变


# ==========================================
# 4. 主程序
# ==========================================
def main():
    # 1. 加载 JSON 数据
    json_data = {}
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        print(f"✅ 已加载 JSON 数据: {len(json_data)} 个角色")
    else:
        print(f"❌ 找不到文件: {JSON_FILE}")
        return

    # 2. 读取 Relation 文件
    if not os.path.exists(RELATION_FILE):
        print(f"❌ 找不到文件: {RELATION_FILE}")
        return

    with open(RELATION_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 存储现有的关系用于查重: set of (A, B, Relation)
    existing_rels = set()
    new_lines = []

    # 先解析所有现有行
    parsed_data = []
    for line in lines:
        line = line.strip()
        if not line: continue
        parts = line.split(',')
        if len(parts) >= 5:
            pA, pB, rel, deptA, deptB = parts[0], parts[1], parts[2], parts[3], parts[4]
            parsed_data.append((pA, pB, rel, deptA, deptB))
            existing_rels.add((pA, pB, rel))

    print(f"📊 原始数据行数: {len(parsed_data)}")

    # 3. 生成补全数据
    count_added = 0
    for pA, pB, rel, deptA, deptB in parsed_data:
        # 获取 B 的性别 (因为我们要判断 B 是 A 的什么)
        gender_b = get_gender(pB, json_data)

        # 计算反向关系名称
        reverse_rel = get_reverse_relation(rel, gender_b)

        # 构造反向条目: B, A, reverse_rel, deptB, deptA
        reverse_entry_key = (pB, pA, reverse_rel)

        # 查重
        if reverse_entry_key not in existing_rels:
            new_line = f"{pB},{pA},{reverse_rel},{deptB},{deptA}"
            new_lines.append(new_line)
            existing_rels.add(reverse_entry_key)  # 加入集合防止后续重复
            count_added += 1

    # 4. 写入文件 (先备份，再追加)
    if new_lines:
        backup_file = RELATION_FILE + ".bak"
        if not os.path.exists(backup_file):
            with open(RELATION_FILE, 'r', encoding='utf-8') as src:
                with open(backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            print(f" 已备份原文件至: {backup_file}")

        with open(RELATION_FILE, 'a', encoding='utf-8') as f:
            for line in new_lines:
                f.write(line + "\n")
        print(f" 完成! 新增补全了 {count_added} 条双向关系。")
    else:
        print("✨ 数据已经是完美的双向结构，无需补全！")

    print("⚠️ 提示: 请重新运行你的数据导入脚本，将更新后的 relation.txt 写入 Neo4j。")


if __name__ == "__main__":
    main()