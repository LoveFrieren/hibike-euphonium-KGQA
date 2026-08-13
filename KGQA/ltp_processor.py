# -*- coding: utf-8 -*-
import os
from ltp import LTP

# ==========================================
# 路径配置
# ==========================================
LOCAL_MODEL_PATH = "E:/ltp-models/ltp-base"
CUSTOM_DICT_PATH = "E:/ltp-models/ltp-base/custom_dict.txt"

# ==========================================
# 1. 初始化 LTP 模型
# ==========================================
try:
    print(f"正在从本地加载 LTP 模型：{LOCAL_MODEL_PATH}")
    ltp = LTP(LOCAL_MODEL_PATH)
    print("✅ LTP 模型本地加载成功！\n")
except Exception as e:
    print(f"❌ LTP 模型加载失败: {e}")
    ltp = None

# ==========================================
# 2. 读取自定义词典到内存
# ==========================================
CUSTOM_WORDS = []
if os.path.exists(CUSTOM_DICT_PATH):
    with open(CUSTOM_DICT_PATH, 'r', encoding='utf-8-sig') as f:
        for line in f:
            word = line.strip().split()[0]
            if word:
                CUSTOM_WORDS.append(word)
    print(f"✅ 已加载 {len(CUSTOM_WORDS)} 个自定义实体，将用于强制匹配。\n")


# ==========================================
# 3. 核心业务逻辑：提取目标实体 (带子串过滤)
# ==========================================
def get_target_array(words):
    if not words or not ltp:
        return []

    raw_entities = []

    try:
        # 步骤 A: 使用 LTP 进行基础的分词和词性标注
        result = ltp.pipeline([words], tasks=["cws", "pos"])
        seg_array = result.cws[0]
        pos_array = result.pos[0]

        target_pos = ['nh', 'n', 'ns', 'ni', 'nz']

        # 步骤 B: 提取 LTP 识别出的常规实体
        for i in range(len(pos_array)):
            if pos_array[i] in target_pos:
                raw_entities.append(seg_array[i])

        # 步骤 C: 强制匹配自定义词典中的核心实体
        for custom_word in CUSTOM_WORDS:
            if custom_word in words and custom_word not in raw_entities:
                raw_entities.append(custom_word)

        # ==========================================
        # 步骤 D: 【核心修复】子串过滤，确保长词优先，不保留被包含的碎片
        # ==========================================
        # 1. 去重
        unique_entities = list(set(raw_entities))
        # 2. 按长度降序排序，确保长词优先被保留
        unique_entities.sort(key=len, reverse=True)

        final_entities = []
        for entity in unique_entities:
            # 检查当前 entity 是否是已经决定保留的某个更长实体的子串
            # 如果是，则跳过（不保留碎片）；如果不是，则保留
            if not any(entity in kept_entity for kept_entity in final_entities if entity != kept_entity):
                final_entities.append(entity)

        # 3. (可选优化) 按照它们在原句中首次出现的顺序重新排序，使结果更自然
        final_entities.sort(key=lambda x: words.find(x))

        return final_entities

    except Exception as e:
        print(f"处理文本出错: {e}")
        return []


# ==========================================
# 4. 本地测试代码
# ==========================================
if __name__ == "__main__":
    print("=" * 60)
    test_sentence = "黄前久美子和加藤叶月在北宇治高中吹奏乐部练习上低音号,加藤叶月曾经暗恋黄前久美子的男朋友冢本秀一。"
    print(f"测试句子: {test_sentence}\n")

    target_result = get_target_array(test_sentence)
    print(f"提取的目标实体: {target_result}")
    print("=" * 60)