import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. 基础配置 ---
st.set_page_config(page_title="每日打卡", page_icon="🍞", layout="wide")
DATA_FILE = "checkin_data.csv"

# 初始化数据文件
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情"])
    df.to_csv(DATA_FILE, index=False)

# 强制读取最新数据
def get_data():
    return pd.read_csv(DATA_FILE)

st.title("🍞 蓝溪 & 润姿自律打卡系统")
st.info("规则：做到加分，没做到扣分；早睡没做到罚款。积分满 20 分奖励面包！")

# --- 2. 打卡区域 ---
with st.sidebar:
    st.header("👤 个人中心")
    user = st.radio("当前打卡人：", ["刘蓝溪", "曾润姿"])
    st.divider()
    st.write("提示：请如实填写，诚信第一。")

with st.expander("➕ 点击开始今日打卡", expanded=True):
    with st.form("checkin_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**基础生活类**")
            is_early = st.checkbox("昨晚 1:00 前睡觉 (未做到罚 2 元 💸)")
            is_weight = st.checkbox("今日体重管理达标 (做到 +1分 / 未做到 -1分 ⚖️)")
            arrival_time = st.time_input("到工位时间 (10:00-11:00 +2分 / 其他 -2分 ⏰)")
            
        with col2:
            st.markdown("**学习进阶类**")
            study_hours = st.number_input("有效学习时长 (>=3h +3分 / <3h -3分 📚)", min_value=0.0, step=0.5)
        
        submit = st.form_submit_button("确认提交数据")

# --- 3. 提交逻辑 ---
if submit:
    points = 0
    fine = 0
    details = []

    # 早睡：仅罚款
    if not is_early:
        fine = 2
        details.append("熬夜(罚2)")
    else:
        details.append("早睡")
    
    # 学习：+3 / -3
    if study_hours >= 3:
        points += 3
        details.append("学习≥3h(+3)")
    else:
        points -= 3
        details.append("学习不够(-3)")
        
    # 工位：+2 / -2
    if 10 <= arrival_time.hour < 11:
        points += 2
        details.append("准时到岗(+2)")
    else:
        points -= 2
        details.append("到岗迟/早(-2)")
        
    # 体重：+1 / -1
    if is_weight:
        points += 1
        details.append("体重达标(+1)")
    else:
        points -= 1
        details.append("体重超标(-1)")

    # 保存数据
    all_data = get_data()
    # 生成唯一 ID
    new_id = int(all_data["ID"].max() + 1) if not all_data.empty else 1
    
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
    st.success(f"打卡成功！{user} 今日获得总分：{points}，需缴纳罚金：{fine} 元")
    st.rerun()

# --- 4. 数据展示与统计 ---
all_data = get_data()

st.divider()
col_stat, col_table = st.columns([1, 2])

with col_stat:
    st.subheader("🏆 累计积分榜")
    if not all_data.empty:
        summary = all_data.groupby("打卡人")["积分"].sum().reset_index()
        for _, row in summary.iterrows():
            st.metric(label=row['打卡人'], value=f"{row['积分']} 分", delta=f"{20 - row['积分']} 分至面包奖励")
            if row['积分'] >= 20:
                st.balloons()
                st.warning(f"🎊 {row['打卡人']} 已达20分！面包安排上！")
    else:
        st.write("暂无数据")

with col_table:
    st.subheader("📊 历史明细")
    if not all_data.empty:
        # 仅展示最后 10 条，按 ID 倒序
        st.dataframe(all_data.sort_values(by="ID", ascending=False).head(10), use_container_width=True)
    else:
        st.write("快去开始第一次打卡吧~")

# --- 5. 管理功能 ---
st.divider()
with st.expander("🛠️ 管理员操作（误填删除）"):
    if not all_data.empty:
        target_id = st.number_input("输入要删除的记录 ID", min_value=1, step=1)
        if st.button("确认删除该条记录", type="primary"):
            # 执行删除
            df_new = all_data[all_data["ID"] != target_id]
            df_new.to_csv(DATA_FILE, index=False)
            st.success(f"ID {target_id} 已删除")
            st.rerun() # 立即刷新界面
    else:
        st.write("当前无记录可删")
