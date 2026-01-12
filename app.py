import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. 基础配置 ---
st.set_page_config(page_title="干啥啥都行", page_icon="🍞", layout="wide")
DATA_FILE = "checkin_data.csv"

# 初始化数据文件 (增加“兑换次数”列)
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
    df.to_csv(DATA_FILE, index=False)

def get_data():
    try:
        df = pd.read_csv(DATA_FILE)
        # 如果旧文件没有兑换次数列，自动补全
        if "兑换次数" not in df.columns:
            df["兑换次数"] = 0
            df.to_csv(DATA_FILE, index=False)
        return df
    except:
        # 如果读取出错（如列名不匹配），重新创建
        return pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])

st.title("🍞 干啥啥都行")

# --- 2. 打卡区域 ---
with st.sidebar:
    st.header("👤 个人中心")
    user = st.radio("当前打卡人：", ["刘蓝溪", "曾润姿"])
    st.divider()
    st.info("规则：做到加分/未做到扣分\n1:00前睡觉/未做到罚2元")

with st.expander("➕ 点击开始今日打卡", expanded=True):
    with st.form("checkin_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**生活类**")
            is_early = st.checkbox("昨晚 1:00 前睡觉 (罚2元 💸)")
            is_weight = st.checkbox("今日体重达标 (+1/-1 ⚖️)")
            arrival_time = st.time_input("到工位时间 (10-11点 +2/-2 ⏰)")
        with col2:
            st.markdown("**学习类**")
            study_hours = st.number_input("有效学习时长 (>=3h +3/-3 📚)", min_value=0.0, step=0.5)
        
        submit = st.form_submit_button("确认提交数据")

# --- 3. 提交逻辑 ---
if submit:
    points, fine = 0, 0
    details = []

    if not is_early: fine = 2; details.append("熬夜(罚2)")
    else: details.append("早睡")
    
    if study_hours >= 3: points += 3; details.append("学习达标(+3)")
    else: points -= 3; details.append("学习未达标(-3)")
        
    if 10 <= arrival_time.hour < 11: points += 2; details.append("准时到位(+2)")
    else: points -= 2; details.append("到位不准时(-2)")
        
    if is_weight: points += 1; details.append("体重达标(+1)")
    else: points -= 1; details.append("体重未达标(-1)")

    all_data = get_data()
    new_id = int(all_data["ID"].max() + 1) if not all_data.empty else 1
    
    new_row = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d %H:%M"), user, points, fine, " | ".join(details), 0]], 
                           columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
    new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
    st.success(f"打卡成功！今日积分：{points}，罚金：{fine}")
    st.rerun()

# --- 4. 积分统计与兑换 ---
all_data = get_data()
st.divider()
st.subheader("🏆 累计成就榜")

col_stats1, col_stats2 = st.columns(2)
for i, name in enumerate(["刘蓝溪", "曾润姿"]):
    user_data = all_data[all_data["打卡人"] == name]
    total_points = user_data["积分"].sum()
    total_breads = user_data["兑换次数"].sum()
    
    with (col_stats1 if i == 0 else col_stats2):
        st.metric(label=f"👤 {name}", value=f"{total_points} 分", delta=f"已吃 {total_breads} 个面包")
        
        # 兑换按钮逻辑
        if total_points >= 20:
            st.balloons()
            if st.button(f"🎉 {name} 兑换一次面包", key=f"redeem_{name}"):
                # 记录一条特殊的兑换数据
                redeem_id = int(all_data["ID"].max() + 1) if not all_data.empty else 1
                redeem_row = pd.DataFrame([[redeem_id, datetime.now().strftime("%Y-%m-%d %H:%M"), name, -20, 0, "兑换面包(扣20分)", 1]], 
                                          columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
                redeem_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
                st.success(f"{name} 成功兑换面包！积分已重置（-20）。")
                st.rerun()

# --- 5. 数据管理 ---
st.divider()
tab1, tab2 = st.tabs(["📊 历史记录", "🛠️ 误填删除"])
with tab1:
    if not all_data.empty:
        st.dataframe(all_data.sort_values(by="ID", ascending=False).head(15), use_container_width=True)
with tab2:
    del_id = st.number_input("输入要删除的记录 ID", min_value=1, step=1)
    if st.button("确认删除记录", type="primary"):
        df_new = all_data[all_data["ID"] != del_id]
        df_new.to_csv(DATA_FILE, index=False)
        st.warning(f"ID {del_id} 已删除")
        st.rerun()

