import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import os

# --- 1. 基础配置 ---
st.set_page_config(page_title="干啥啥都行组打卡", page_icon="🍞", layout="wide")

# 使用 v8 文件名，确保日期字段格式统一
DATA_FILE = "checkin_data_v8.csv"

def init_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
        df.to_csv(DATA_FILE, index=False)

def get_data():
    init_data()
    try:
        return pd.read_csv(DATA_FILE)
    except:
        return pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])

# --- 2. 界面头部 ---
st.title("🍞 干啥啥都行组自律系统 V8.0")
st.markdown("---")

# 第一步：选择打卡人
st.subheader("👤 第一步：请选择身份")
user = st.radio(
    "是谁在操作？", 
    ["刘蓝溪", "曾润姿"], 
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

# 第二步：录入数据
st.subheader("📝 第二步：录入数据（支持补打卡）")
with st.form("checkin_form", clear_on_submit=True):
    # 新增：日期选择功能
    checkin_date = st.date_input("📅 选择打卡日期（默认为今天，补打卡请点击修改）", value=date.today())
    
    st.write("") # 间距
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏡 日常生活**")
        is_early = st.checkbox("1:00 前睡觉 (做到不罚 / 未做到罚 2 元 💸)")
        is_weight = st.checkbox("体重管理达标 (做到 +1 / 未做到 -1 ⚖️)")
        arrival_time = st.time_input("到工位时间 (11:00 之前 +2 / 之后 -2 ⏰)", value=time(10, 0))
    
    with col2:
        st.markdown("**📚 学习进阶**")
        study_hours = st.number_input("有效学习时长 (满 3h +3 / 不满 -3)", min_value=0.0, step=0.5)
    
    submit = st.form_submit_button("确认提交", use_container_width=True)

# --- 3. 计算逻辑 ---
if submit:
    points, fine = 0, 0
    details = []

    # 1. 早睡罚款
    if not is_early: 
        fine = 2
        details.append("熬夜(罚2)")
    else: 
        details.append("早睡")
    
    # 2. 到岗积分 (11:00之前含11:00)
    if arrival_time <= time(11, 0): 
        points += 2
        details.append(f"{arrival_time.strftime('%H:%M')}到岗(+2)")
    else: 
        points -= 2
        details.append(f"{arrival_time.strftime('%H:%M')}晚到(-2)")
        
    # 3. 学习积分
    if study_hours >= 3: 
        points += 3
        details.append("学习≥3h(+3)")
    else: 
        points -= 3
        details.append("学习不足(-3)")
        
    # 4. 体重积分
    if is_weight: 
        points += 1
        details.append("体重达标(+1)")
    else: 
        points -= 1
        details.append("体重未达标(-1)")

    # 保存数据
    all_data = get_data()
    new_id = int(all_data["ID"].max() + 1) if not all_data.empty else 1
    
    new_row = pd.DataFrame([[
        new_id, 
        checkin_date.strftime("%Y-%m-%d"), # 使用用户选择的日期
        user, 
        points, 
        fine, 
        " | ".join(details), 
        0
    ]], columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
    
    new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
    st.balloons()
    st.success(f"打卡成功！日期：{checkin_date}，积分：{points}，罚金：{fine}")
    st.rerun()

# --- 4. 累计榜单 ---
all_data = get_data()
st.markdown("---")
st.subheader("🏆 累计成就与面包进度")

c1, c2 = st.columns(2)
for i, name in enumerate(["刘蓝溪", "曾润姿"]):
    u_df = all_data[all_data["打卡人"] == name]
    pts = u_df["积分"].sum()
    reds = u_df["兑换次数"].sum()
    
    with (c1 if i == 0 else c2):
        st.metric(label=f"👤 {name}", value=f"{pts} 分", delta=f"累计兑换 {reds} 次")
        
        if pts >= 20:
            if st.button(f"🎁 {name} 兑换面包 (-20分)", key=f"rd_{name}", use_container_width=True):
                rid = int(all_data["ID"].max() + 1) if not all_data.empty else 1
                r_row = pd.DataFrame([[rid, date.today().strftime("%Y-%m-%d"), name, -20, 0, "兑换奖励", 1]], 
                                     columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
                r_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
                st.success("兑换记录已添加！")
                st.rerun()

# --- 5. 历史与管理 ---
st.markdown("---")
tab_list, tab_admin = st.tabs(["📊 查看所有记录", "🛠️ 误填管理"])

with tab_list:
    if not all_data.empty:
        # 按日期倒序排列，让最新的（或最新补录的）排在前面
        st.dataframe(all_data.sort_values(by=["日期", "ID"], ascending=[False, False]), use_container_width=True)
    else:
        st.write("暂无打卡记录。")

with tab_admin:
    target_id = st.number_input("请输入想要删除的记录 ID", min_value=1, step=1)
    if st.button("确认删除该记录", type="primary"):
        updated_df = all_data[all_data["ID"] != target_id]
        updated_df.to_csv(DATA_FILE, index=False)
        st.warning(f"ID {target_id} 已删除")
        st.rerun()
