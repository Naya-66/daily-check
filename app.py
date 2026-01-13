import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import os
import altair as alt

# --- 1. 基础配置 ---
st.set_page_config(page_title="干啥啥都行组打卡", page_icon="🍞", layout="wide")

# 升级到 v11 版本，确保数据一致性
DATA_FILE = "checkin_data_v11.csv"

def init_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])
        df.to_csv(DATA_FILE, index=False)

def get_data():
    init_data()
    try:
        df = pd.read_csv(DATA_FILE)
        # 确保日期格式正确
        df["日期"] = pd.to_datetime(df["日期"]).dt.date
        return df
    except:
        return pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])

st.title("🍞 干啥啥都行组自律系统 V11.0")
st.markdown("---")

# --- 2. 第一步：身份选择 ---
st.subheader("👤 第一步：请选择身份")
user = st.radio("选择操作人：", ["刘蓝溪", "曾润姿"], horizontal=True, label_visibility="collapsed")
st.markdown("---")

# --- 3. 第二步：录入表单 ---
st.subheader("📝 第二步：打卡录入")
with st.form("checkin_form", clear_on_submit=True):
    checkin_date = st.date_input("📅 打卡日期", value=date.today())
    
    col_f, col_s, col_d = st.columns([1, 1.2, 1])
    
    with col_f:
        st.markdown("### 💸 罚款类")
        is_early = st.checkbox("昨晚 1:00 前睡觉 (未做到罚 2 元)")

    with col_s:
        st.markdown("### ⭐ 积分类")
        arrival_time = st.time_input("1. 到工位时间 (11:00前+2 / 之后-2)", value=time(10, 0))
        study_hours = st.number_input("2. 有效学习时长 (满3h+3 / 否则-3)", min_value=0.0, step=0.5)
        is_weight_ok = st.checkbox("3. 体重管理达标 (做到+1 / 否则-1)")
        weight_kg = st.number_input("当前具体体重 (kg)", min_value=0.0, max_value=200.0, step=0.1)

    with col_daily:
        st.markdown("### 💧 日常类")
        water_cups = st.number_input("今日喝水杯数", min_value=0, step=1)
        st.caption("提示：体重和喝水不计入积分。")

    submit = st.form_submit_button("提交数据", use_container_width=True)

# --- 4. 提交逻辑 ---
if submit:
    points, fine, details = 0, 0, []
    if not is_early: fine = 2; details.append("熬夜(罚2)")
    else: details.append("早睡")
    
    if arrival_time <= time(11, 0): points += 2; details.append("准时到位")
    else: points -= 2; details.append("晚到")
        
    if study_hours >= 3: points += 3; details.append("学习达标")
    else: points -= 3; details.append("时长不足")
        
    if is_weight_ok: points += 1; details.append("体重达标")
    else: points -= 1; details.append("体重未达标")

    all_data = get_data()
    new_id = int(all_data["ID"].max() + 1) if not all_data.empty else 1
    new_row = pd.DataFrame([[
        new_id, checkin_date, user, points, fine, " | ".join(details), 0, water_cups, weight_kg
    ]], columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])
    
    new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
    st.balloons()
    st.rerun()

# --- 5. 累计榜单 ---
all_data = get_data()
st.markdown("---")
st.subheader("🏆 累计成就榜")
c1, c2 = st.columns(2)
for i, name in enumerate(["刘蓝溪", "曾润姿"]):
    u_df = all_data[all_data["打卡人"] == name]
    with (c1 if i == 0 else c2):
        st.metric(label=f"👤 {name}", value=f"{u_df['积分'].sum()} 分", delta=f"已兑换 {int(u_df['兑换次数'].sum())} 次")
        if u_df['积分'].sum() >= 20:
            if st.button(f"🎁 {name} 兑换面包", key=f"rd_{name}", use_container_width=True):
                rid = int(all_data["ID"].max() + 1) if not all_data.empty else 1
                r_row = pd.DataFrame([[rid, date.today(), name, -20, 0, "兑换奖励", 1, 0, 0]], 
                                     columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])
                r_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
                st.rerun()

# --- 6. 📈 体重变化曲线 (核心新增) ---
st.markdown("---")
st.subheader("📈 身体健康趋势")

# 准备绘图数据：过滤掉体重为0的记录
chart_data = all_data[all_data["具体体重"] > 0].copy()

if not chart_data.empty:
    # 使用 Altair 绘制曲线图
    chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x=alt.X('日期:T', title='日期'),
        y=alt.Y('具体体重:Q', title='体重 (kg)', scale=alt.Scale(zero=False)),
        color='打卡人:N',
        tooltip=['日期', '打卡人', '具体体重']
    ).properties(height=400).interactive()
    
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("还没有输入具体的体重数值，暂无法生成曲线哦。")

# --- 7. 数据明细 ---
st.markdown("---")
tab_list, tab_admin = st.tabs(["📊 历史明细", "🛠️ 管理"])
with tab_list:
    st.dataframe(all_data.sort_values(by=["日期", "ID"], ascending=[False, False]), use_container_width=True)
with tab_admin:
    target_id = st.number_input("输入删除 ID", min_value=1, step=1)
    if st.button("确定删除", type="primary"):
        all_data[all_data["ID"] != target_id].to_csv(DATA_FILE, index=False)
        st.rerun()
