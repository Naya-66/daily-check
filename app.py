import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 1. 基础配置
st.set_page_config(page_title="蓝溪&润姿打卡", page_icon="🍞")
DATA_FILE = "checkin_data.csv"

# 初始化数据文件
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["日期", "打卡人", "积分", "罚金"])
    df.to_csv(DATA_FILE, index=False)

# 2. 界面设计
st.title("🍞 蓝溪 & 润姿自律契约")

user = st.selectbox("是谁在打卡？", ["刘蓝溪", "曾润姿"])

with st.form("checkin_form"):
    col1, col2 = st.columns(2)
    with col1:
        is_early = st.checkbox("1:00 前睡觉 (不达标扣2元)")
        is_weight = st.checkbox("体重管理达标 (+1分)")
    with col2:
        study_hours = st.number_input("学习时长 (h)", min_value=0.0, step=0.5)
        arrival_time = st.time_input("到工位时间")
    
    submit = st.form_submit_button("提交今日成果")

# 3. 逻辑处理
if submit:
    points = 0
    fine = 0
    if not is_early: fine = 2
    if study_hours >= 3: points += 2
    if 10 <= arrival_time.hour < 11: points += 3
    if is_weight: points += 1
    
    # 保存数据
    new_data = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), user, points, fine]], 
                            columns=["日期", "打卡人", "积分", "罚金"])
    new_data.to_csv(DATA_FILE, mode='a', header=False, index=False)
    
    st.balloons()
    st.success(f"打卡成功！今日积分：+{points}，罚金：{fine}元")

# 4. 榜单展示
st.divider()
st.subheader("📊 荣誉榜单 (20分换面包)")
all_data = pd.read_csv(DATA_FILE)
summary = all_data.groupby("打卡人")["积分"].sum().reset_index()
st.table(summary)