import streamlit as st
import pandas as pd
from datetime import datetime, time
import os

# --- 1. 基础配置 ---
st.set_page_config(page_title="干啥啥都行组打卡", page_icon="🍞", layout="wide")

# 使用 v6 文件名以彻底避免旧数据干扰
DATA_FILE = "checkin_data_v6.csv"

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

st.title("🍞 干啥啥都行组")
st.markdown("---")

# --- 2. 侧边栏 ---
with st.sidebar:
    st.header("👤 个人中心")
    user = st.radio("选择打卡人：", ["刘蓝溪", "曾润姿"])
    st.divider()
    st.info("📌 核心规则：\n- 11:00前到岗: +2 / 晚到: -2\n- 学习>=3h: +3 / 否则: -3\n- 体重达标: +1 / 否则: -1\n- 凌晨1:00后睡: 罚2元")

# --- 3. 打卡表单 ---
with st.expander("➕ 开启今日打卡", expanded=True):
    with st.form("checkin_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**日常作息**")
            is_early = st.checkbox("昨晚 1:00 前睡觉 (未做到罚 2 元 💸)")
            is_weight = st.checkbox("今日体重管理达标 (做到 +1 / 否则 -1 ⚖️)")
            arrival_time = st.time_input("到工位时间 (11:00之前到 +2 / 晚于11:00扣2 ⏰)", value=time(10, 0))
        with col2:
            st.markdown("**任务达成**")
            study_hours = st.number_input("有效学习时长 (满 3h +3 / 不满 -3 📚)", min_value=0.0, step=0.5)
        
        submit = st.form_submit_button("提交数据")

# --- 4. 计算逻辑 ---
if submit:
    points, fine = 0, 0
    details = []

    # 1. 罚款项：早睡
    if not is_early: 
        fine = 2
        details.append("熬夜(罚2)")
    else: 
        details.append("早睡")
    
    # 2. 加扣分项：工位时间 (修正逻辑：11:00之前包含11:00)
    if arrival_time <= time(11, 0): 
        points += 2
        details.append(f"{arrival_time.strftime('%H:%M')}到位(+2)")
    else: 
        points -= 2
        details.append(f"{arrival_time.strftime('%H:%M')}晚到(-2)")
        
    # 3. 加扣分项：学习时间
    if study_hours >= 3: 
        points += 3
        details.append("学习满3h(+3)")
    else: 
        points -= 3
        details.append("学习不满3h(-3)")
        
    # 4. 加扣分项：体重
    if is_weight: 
        points += 1
        details.append("体重达标(+1)")
    else: 
        points -= 1
        details.append("体重不达标(-1)")

    # 保存数据
    all_data = get_data()
    new_id = int(all_data["ID"].max() + 1) if not all_data.empty else 1
    
    new_row = pd.DataFrame([[
        new_id, 
        datetime.now().strftime("%Y-%m-%d %H:%M"), 
        user, 
        points, 
        fine, 
        " | ".join(details), 
        0
    ]], columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
    
    new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
    st.balloons()
    st.success(f"提交成功！今日积分变化：{points}，罚金：{fine} 元")
    st.rerun()

# --- 5. 累计看板 ---
all_data = get_data()
st.divider()

c1, c2 = st.columns(2)
for i, name in enumerate(["刘蓝溪", "曾润姿"]):
    u_df = all_data[all_data["打卡人"] == name]
    pts = u_df["积分"].sum()
    reds = u_df["兑换次数"].sum()
    
    with (c1 if i == 0 else c2):
        st.metric(label=f"👤 {name}", value=f"{pts} 分", delta=f"累计兑换 {reds} 次")
        
        if pts >= 20:
            if st.button(f"🎁 {name} 兑换面包 (需20分)", key=f"rd_{name}"):
                rid = int(all_data["ID"].max() + 1) if not all_data.empty else 1
                r_row = pd.DataFrame([[rid, datetime.now().strftime("%Y-%m-%d %H:%M"), name, -20, 0, "兑换面包", 1]], 
                                     columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
                r_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
                st.success("兑换成功，积分已扣除！")
                st.rerun()

# --- 6. 明细管理 ---
st.divider()
t_list, t_admin = st.tabs(["📊 历史明细", "🛠️ 管理后台"])

with t_list:
    if not all_data.empty:
        st.dataframe(all_data.sort_values(by="ID", ascending=False), use_container_width=True)
    else:
        st.write("还没有打卡记录哦~")

with t_admin:
    target_id = st.number_input("请输入想要删除的记录 ID", min_value=1, step=1)
    if st.button("确认删除该记录", type="primary"):
        updated_df = all_data[all_data["ID"] != target_id]
        updated_df.to_csv(DATA_FILE, index=False)
        st.warning(f"ID {target_id} 已被删除")
        st.rerun()
