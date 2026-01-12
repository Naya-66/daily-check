import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. 基础配置与强制重置 ---
st.set_page_config(page_title="蓝溪&润姿自律契约 V4.0", page_icon="🍞", layout="wide")

# 【关键点】改名为 v4，系统会自动创建一个全新的正确文件，解决报错
DATA_FILE = "checkin_data_v4.csv"

# 初始化数据文件的函数
def init_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
        df.to_csv(DATA_FILE, index=False)

def get_data():
    init_data()
    try:
        df = pd.read_csv(DATA_FILE)
        return df
    except:
        return pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])

st.title("🍞 蓝溪 & 润姿自律打卡系统 V4.0")
st.markdown("---")

# --- 2. 打卡区域 ---
with st.sidebar:
    st.header("👤 个人中心")
    user = st.radio("当前打卡人：", ["刘蓝溪", "曾润姿"])
    st.divider()
    st.info("规则：\n- 学习>=3h: +3 / <3h: -3\n- 准时到位: +2 / 否则: -2\n- 体重达标: +1 / 否则: -1\n- 1:00前睡觉: 做到不罚 / 否则罚2元")

with st.expander("➕ 点击展开今日打卡表单", expanded=True):
    with st.form("checkin_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**基础生活**")
            is_early = st.checkbox("昨晚 1:00 前睡觉 (未做到罚2元 💸)")
            is_weight = st.checkbox("今日体重管理达标 (+1 / -1 ⚖️)")
            arrival_time = st.time_input("到工位时间 (10:00-11:00 为准时 ⏰)")
        with col2:
            st.markdown("**学习表现**")
            study_hours = st.number_input("有效学习时长 (>=3h为达标 📚)", min_value=0.0, step=0.5)
        
        submit = st.form_submit_button("确认提交今日数据")

# --- 3. 提交处理逻辑 ---
if submit:
    points, fine = 0, 0
    details = []

    # 1. 早睡逻辑
    if not is_early: fine = 2; details.append("熬夜(罚2)")
    else: details.append("早睡")
    
    # 2. 学习逻辑 (+3/-3)
    if study_hours >= 3: points += 3; details.append("学习达标(+3)")
    else: points -= 3; details.append("学习未达标(-3)")
        
    # 3. 工位逻辑 (+2/-2)
    if 10 <= arrival_time.hour < 11: points += 2; details.append("准时到位(+2)")
    else: points -= 2; details.append("到位不准时(-2)")
        
    # 4. 体重逻辑 (+1/-1)
    if is_weight: points += 1; details.append("体重达标(+1)")
    else: points -= 1; details.append("体重未达标(-1)")

    # 写入文件
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
    st.success(f"提交成功！{user} 今日获得：{points} 分，罚金：{fine} 元")
    st.rerun()

# --- 4. 累计统计与面包兑换 ---
all_data = get_data()
st.divider()

col_l, col_r = st.columns(2)
for i, name in enumerate(["刘蓝溪", "曾润姿"]):
    user_data = all_data[all_data["打卡人"] == name]
    total_pts = user_data["积分"].sum()
    total_breads = user_data["兑换次数"].sum()
    
    with (col_l if i == 0 else col_r):
        # 修改点：累计兑换次数
        st.metric(label=f"👤 {name}", value=f"{total_pts} 分", delta=f"累计兑换 {total_breads} 次")
        
        if total_pts >= 20:
            if st.button(f"🎁 {name} 兑换面包 (-20分)", key=f"btn_{name}"):
                rid = int(all_data["ID"].max() + 1) if not all_data.empty else 1
                r_row = pd.DataFrame([[rid, datetime.now().strftime("%Y-%m-%d %H:%M"), name, -20, 0, "兑换面包", 1]], 
                                     columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数"])
                r_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
                st.success("兑换成功！积分已扣除。")
                st.rerun()

# --- 5. 数据明细与管理 ---
st.divider()
tab_rec, tab_del = st.tabs(["📊 历史记录明细", "🛠️ 管理员操作"])

with tab_rec:
    if not all_data.empty:
        # 按照 ID 倒序排列，解决 Key 错误
        display_df = all_data.sort_values(by="ID", ascending=False)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.write("暂无记录")

with tab_del:
    del_id = st.number_input("输入要删除的记录 ID", min_value=1, step=1)
    if st.button("确定删除", type="primary"):
        df_update = all_data[all_data["ID"] != del_id]
        df_update.to_csv(DATA_FILE, index=False)
        st.warning(f"ID {del_id} 已从数据库移除")
        st.rerun()
