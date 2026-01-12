import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. 基础配置 ---
st.set_page_config(page_title="干啥啥都行组打卡", page_icon="🍞", layout="wide")

# 使用 v5 文件名以确保环境干净
DATA_FILE = "checkin_data_v5.csv"

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

st.title("🍞 干啥啥都行组自律系统 V5.0")
st.markdown("---")

# --- 2. 侧边栏与打卡人选择 ---
with st.sidebar:
    st.header("👤 个人中心")
    user = st.radio("当前打卡人：", ["刘蓝溪", "曾润姿"])
    st.divider()
    st.info("💡 提醒：\n- 晚于 11:00 到工位会扣分哦！\n- 累计 20 分即可兑换美味面包。")

# --- 3. 打卡表单 ---
with st.expander("➕ 点击录入今日数据", expanded=True):
    with st.form("checkin_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**生活习惯**")
            is_early = st.checkbox("昨晚 1:00 前睡觉 (未做到罚 2 元 💸)")
            is_weight = st.checkbox("今日体重管理达标 (+1 / -1 ⚖️)")
            arrival_time = st.time_input("到工位时间 (10:00-11:00 +2 / 晚于11:00扣2分 ⏰)")
        with col2:
            st.markdown("**学习进阶**")
            study_hours = st.number_input("有效学习时长 (>=3h +3 / <3h -3 📚)", min_value=0.0, step=0.5)
        
        submit = st.form_submit_button("确认提交")

# --- 4. 提交逻辑 ---
if submit:
    points, fine = 0, 0
    details = []

    # 早睡逻辑
    if not is_early: 
        fine = 2
        details.append("熬夜(罚2)")
    else: 
        details.append("早睡")
    
    # 学习逻辑
    if study_hours >= 3: 
        points += 3
        details.append("学习达标(+3)")
    else: 
        points -= 3
        details.append("学习未达标(-3)")
        
    # 工位逻辑 (修改：明确晚于11点扣分)
    if 10 <= arrival_time.hour < 11: 
        points += 2
        details.append("准时到位(+2)")
    else: 
        points -= 2
        details.append("迟到/过早(-2)")
        
    # 体重逻辑
    if is_weight: 
        points += 1
        details.append("体重达标(+1)")
    else: 
        points -= 1
        details.append("体重未达标(-1)")

    # 存入文件
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
    st.success(f"提交成功！今日积分：{points}，罚金：{fine}")
    st.rerun()

# --- 5. 积分与兑换看板 ---
all_data = get_data()
st.divider()

col_l, col_r = st.columns(2)
for i, name in enumerate(["刘蓝溪", "曾润姿"]):
    user_data = all_data[all_data["打卡人"] == name]
    total_pts = user_data["积分"].sum()
    total_redeems = user_data["兑换次数"].sum()
    
    with (col_l if i == 0 else col_r):
        st.metric(label=f"👤 {name}", value=f"{total_pts} 分", delta=f"累计兑换 {total_redeems} 次")
        
        if total_pts >= 20:
            if st.button(f"🎁 {name} 兑换面包 (-20分)", key=f"redeem_{name}"):
                rid = int(all_data["ID"].max() + 1) if not all_data.empty else 1
                r_row = pd.DataFrame([[rid, datetime.now().strftime("%Y-%m-%d %H:%M"), name, -20, 0, "兑换奖励", 1]], 
                                     columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
                r_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
                st.success("兑换记录已添加！")
                st.rerun()

# --- 6. 记录明细与管理 ---
st.divider()
tab_history, tab_admin = st.tabs(["📊 历史明细", "🛠️ 管理后台"])

with tab_history:
    if not all_data.empty:
        st.dataframe(all_data.sort_values(by="ID", ascending=False), use_container_width=True)
    else:
        st.write("暂无记录")

with tab_admin:
    del_id = st.number_input("输入要删除的记录 ID", min_value=1, step=1)
    if st.button("确定删除记录", type="primary"):
        df_update = all_data[all_data["ID"] != del_id]
        df_update.to_csv(DATA_FILE, index=False)
        st.warning(f"ID {del_id} 已删除")
        st.rerun()
