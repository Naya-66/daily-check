import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. 基础配置与样式 ---
st.set_page_config(page_title="蓝溪&润姿自律契约 V2.0", page_icon="🍞", layout="wide")
DATA_FILE = "checkin_data.csv"

# 初始化数据文件（增加 ID 列方便删除）
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情"])
    df.to_csv(DATA_FILE, index=False)

st.title("🍞 干啥啥都行")
st.markdown("---")

# --- 2. 打卡区域 ---
st.subheader("📝 今日数据上报")
user = st.radio("选择打卡人：", ["刘蓝溪", "曾润姿"], horizontal=True)

with st.form("checkin_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        is_early = st.checkbox("昨晚 1:00 前睡觉 (未做到罚 2 元 💸)")
        is_weight = st.checkbox("体重管理达标 (做到 +1分 / 未做到 -1分 ⚖️)")
        arrival_time = st.time_input("到工位时间 (10:00-11:00 准时 +2分 / 否则 -2分 ⏰)")
        
    with col2:
        study_hours = st.number_input("有效学习时长 (>=3h 奖励 +3分 / 否则 -3分 📚)", min_value=0.0, step=0.5)
    
    submit = st.form_submit_button("提交今日成果")

# --- 3. 逻辑处理 ---
if submit:
    points = 0
    fine = 0
    details = []

    # 早睡逻辑 (只有罚金)
    if not is_early:
        fine = 2
        details.append("熬夜罚款")
    
    # 学习逻辑 (+3 / -3)
    if study_hours >= 3:
        points += 3
        details.append("学习达标")
    else:
        points -= 3
        details.append("学习未达标")
        
    # 工位逻辑 (+2 / -2)
    if 10 <= arrival_time.hour < 11:
        points += 2
        details.append("准时到位")
    else:
        points -= 2
        details.append("到位迟到/过早")
        
    # 体重逻辑 (+1 / -1)
    if is_weight:
        points += 1
        details.append("体重达标")
    else:
        points -= 1
        details.append("体重未达标")

    # 保存数据
    all_data = pd.read_csv(DATA_FILE)
    new_id = len(all_data) + 1
    new_row = pd.DataFrame([[
        new_id,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        user, 
        points, 
        fine, 
        " | ".join(details)
    ]], columns=["ID", "日期", "打卡人", "积分", "罚金", "详情"])
    
    new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
    
    st.balloons()
    st.success(f"打卡成功！{user} 今日总分：{points}，罚金：{fine} 元")

# --- 4. 数据展示与管理 ---
st.markdown("---")
all_data = pd.read_csv(DATA_FILE)

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📊 历史记录")
    if not all_data.empty:
        # 反转显示，最新的在最上面
        st.dataframe(all_data.sort_values(by="日期", ascending=False), use_container_width=True)
    else:
        st.write("暂无记录")

with col_right:
    st.subheader("🏆 累计总分")
    if not all_data.empty:
        summary = all_data.groupby("打卡人")["积分"].sum().reset_index()
        for _, row in summary.iterrows():
            st.metric(label=row['打卡人'], value=f"{row['积分']} 分", delta="目标 20 分")
            if row['积分'] >= 20:
                st.warning(f"🎊 恭喜 {row['打卡人']}！可以吃面包了！")
    
    st.markdown("---")
    st.subheader("🗑️ 管理记录")
    if not all_data.empty:
        delete_id = st.number_input("输入要删除的记录 ID", min_value=1, step=1)
        if st.button("确认删除记录", type="secondary"):
            all_data = all_data[all_data["ID"] != delete_id]
            all_data.to_csv(DATA_FILE, index=False)
            st.warning(f"ID 为 {delete_id} 的记录已删除，请刷新页面。")
