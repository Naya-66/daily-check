import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import os

# --- 1. 基础配置 ---
st.set_page_config(page_title="干啥啥都行组打卡", page_icon="🍞", layout="wide")

# 升级到 v10 版本，增加喝水和体重kg字段
DATA_FILE = "checkin_data_v10.csv"

def init_data():
    if not os.path.exists(DATA_FILE):
        # 增加字段：喝水杯数, 具体体重
        df = pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])
        df.to_csv(DATA_FILE, index=False)

def get_data():
    init_data()
    try:
        return pd.read_csv(DATA_FILE)
    except:
        return pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])

# --- 2. 界面头部 ---
st.title("🍞 干啥啥都行组自律系统 V10.0")
st.markdown("---")

# 选择打卡人
st.subheader("👤 第一步：请选择身份")
user = st.radio("选择操作人：", ["刘蓝溪", "曾润姿"], horizontal=True, label_visibility="collapsed")
st.markdown("---")

# --- 3. 结构化打卡表单 ---
st.subheader("📝 第二步：分类打卡录入")
with st.form("checkin_form", clear_on_submit=True):
    checkin_date = st.date_input("📅 打卡日期", value=date.today())
    
    # 分类展示
    col_fine, col_score, col_daily = st.columns([1, 1.2, 1])
    
    with col_fine:
        st.markdown("### 💸 罚款类")
        is_early = st.checkbox("昨晚 1:00 前睡觉 (未做到罚 2 元)")
        st.caption("注：早睡不计入积分，仅作罚款判定")

    with col_score:
        st.markdown("### ⭐ 积分类")
        # 1. 到工位时间
        arrival_time = st.time_input("1. 到工位时间 (11:00前+2 / 之后-2)", value=time(10, 0))
        # 2. 学习时长
        study_hours = st.number_input("2. 有效学习时长 (满3h+3 / 否则-3)", min_value=0.0, step=0.5)
        # 3. 体重管理
        is_weight_ok = st.checkbox("3. 体重管理达标 (做到+1 / 否则-1)")
        weight_kg = st.number_input("当前体重 (kg)", min_value=0.0, step=0.1, help="输入具体体重，不计入积分")

    with col_daily:
        st.markdown("### 💧 日常类 (不计分)")
        water_cups = st.number_input("今日喝水杯数", min_value=0, step=1)
        uploaded_file = st.file_uploader("📸 证明上传", type=["jpg", "jpeg", "png"])

    submit = st.form_submit_button("确认提交并计算", use_container_width=True)

# --- 4. 提交逻辑 ---
if submit:
    points, fine = 0, 0
    details = []

    # 1. 罚款类逻辑
    if not is_early: 
        fine = 2
        details.append("熬夜(罚2)")
    else:
        details.append("早睡")
    
    # 2. 积分类逻辑 (按要求顺序)
    # 到位时间
    if arrival_time <= time(11, 0): 
        points += 2
        details.append(f"{arrival_time.strftime('%H:%M')}到位(+2)")
    else: 
        points -= 2
        details.append(f"{arrival_time.strftime('%H:%M')}迟到(-2)")
        
    # 学习时长
    if study_hours >= 3: 
        points += 3
        details.append("学习≥3h(+3)")
    else: 
        points -= 3
        details.append("学习不足(-3)")
        
    # 体重管理
    if is_weight_ok: 
        points += 1
        details.append("体重达标(+1)")
    else: 
        points -= 1
        details.append("体重未达标(-1)")

    # 保存数据
    all_data = get_data()
    new_id = int(all_data["ID"].max() + 1) if not all_data.empty else 1
    
    new_row = pd.DataFrame([[
        new_id, checkin_date.strftime("%Y-%m-%d"), user, points, fine, 
        " | ".join(details), 0, water_cups, weight_kg
    ]], columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])
    
    new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
    
    st.balloons()
    st.success(f"打卡成功！积分：{points}，罚金：{fine}，今日喝水：{water_cups}杯")
    st.rerun()

# --- 5. 累计榜单与统计 ---
all_data = get_data()
st.markdown("---")
st.subheader("🏆 累计成就与面包进度")

c1, c2 = st.columns(2)
for i, name in enumerate(["刘蓝溪", "曾润姿"]):
    u_df = all_data[all_data["打卡人"] == name]
    pts = u_df["积分"].sum()
    reds = u_df["兑换次数"].sum()
    # 喝水总计
    total_water = u_df["喝水杯数"].sum()
    
    with (c1 if i == 0 else c2):
        st.metric(label=f"👤 {name}", value=f"{pts} 分", delta=f"累计兑换 {reds} 次")
        st.write(f"🥤 累计喝水：{int(total_water)} 杯")
        
        if pts >= 20:
            if st.button(f"🎁 {name} 兑换面包", key=f"rd_{name}", use_container_width=True):
                rid = int(all_data["ID"].max() + 1) if not all_data.empty else 1
                r_row = pd.DataFrame([[rid, date.today().strftime("%Y-%m-%d"), name, -20, 0, "兑换奖励", 1, 0, 0]], 
                                     columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])
                r_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
                st.rerun()

# --- 6. 历史记录 ---
st.markdown("---")
tab_list, tab_admin = st.tabs(["📊 历史所有记录", "🛠️ 管理"])
with tab_list:
    if not all_data.empty:
        # 展示历史记录，包含体重和喝水
        st.dataframe(all_data.sort_values(by=["日期", "ID"], ascending=[False, False]), use_container_width=True)
    else:
        st.write("暂无记录。")

with tab_admin:
    target_id = st.number_input("输入删除记录 ID", min_value=1, step=1)
    if st.button("确认删除", type="primary"):
        updated_df = all_data[all_data["ID"] != target_id]
        updated_df.to_csv(DATA_FILE, index=False)
        st.rerun()
