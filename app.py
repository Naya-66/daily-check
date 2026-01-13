import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import os
import altair as alt

# --- 1. 基础配置 ---
st.set_page_config(page_title="干啥啥都行组打卡", page_icon="🍞", layout="wide")

# 升级到 v12 版本，移除图证字段，确保环境干净
DATA_FILE = "checkin_data_v12.csv"

def init_data():
    if not os.path.exists(DATA_FILE):
        # 字段包含：ID, 日期, 打卡人, 积分, 罚金, 详情, 兑换次数, 喝水杯数, 具体体重
        df = pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])
        df.to_csv(DATA_FILE, index=False)

def get_data():
    init_data()
    try:
        df = pd.read_csv(DATA_FILE)
        df["日期"] = pd.to_datetime(df["日期"]).dt.date
        return df
    except:
        return pd.DataFrame(columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])

# --- 2. 界面头部 ---
st.title("🍞 干啥啥都行组自律系统 V12.0")
st.markdown("---")

# 选择打卡人
st.subheader("👤 第一步：请选择身份")
user = st.radio("选择操作人：", ["刘蓝溪", "曾润姿"], horizontal=True, label_visibility="collapsed")
st.markdown("---")

# --- 3. 结构化打卡表单 ---
st.subheader("📝 第二步：分类打卡录入")
with st.form("checkin_form", clear_on_submit=True):
    checkin_date = st.date_input("📅 打卡日期", value=date.today())
    
    col_fine, col_score, col_daily = st.columns([1, 1.2, 1])
    
    with col_fine:
        st.markdown("### 💸 罚款类")
        is_early = st.checkbox("昨晚 1:00 前睡觉 (未做到罚 2 元)")
        st.caption("注：早睡不计入积分")

    with col_score:
        st.markdown("### ⭐ 积分类")
        # 1. 到工位时间
        arrival_time = st.time_input("1. 到工位时间 (11:00前+2 / 之后-2)", value=time(10, 0))
        # 2. 学习时长
        study_hours = st.number_input("2. 有效学习时长 (满3h+3 / 否则-3)", min_value=0.0, step=0.5)
        # 3. 体重管理达标判定
        is_weight_ok = st.checkbox("3. 体重管理达标 (做到+1 / 否则-1)")
        # 具体体重数值记录
        weight_kg = st.number_input("当前具体体重 (kg)", min_value=0.0, step=0.1)

    with col_daily:
        st.markdown("### 💧 日常类 (不计分)")
        water_cups = st.number_input("今日喝水杯数", min_value=0, step=1)
        st.write("")
        st.write("✨ 保持水分，健康生活")

    submit = st.form_submit_button("确认提交并计算", use_container_width=True)

# --- 4. 提交逻辑 ---
if submit:
    points, fine, details = 0, 0, []

    # 1. 罚款类逻辑
    if not is_early: 
        fine = 2; details.append("熬夜(罚2)")
    else:
        details.append("早睡")
    
    # 2. 积分类逻辑
    if arrival_time <= time(11, 0): 
        points += 2; details.append(f"{arrival_time.strftime('%H:%M')}到位(+2)")
    else: 
        points -= 2; details.append(f"{arrival_time.strftime('%H:%M')}迟到(-2)")
        
    if study_hours >= 3: 
        points += 3; details.append("学习≥3h(+3)")
    else: 
        points -= 3; details.append("学习不足(-3)")
        
    if is_weight_ok: 
        points += 1; details.append("体重达标(+1)")
    else: 
        points -= 1; details.append("体重未达标(-1)")

    # 保存数据
    all_data = get_data()
    new_id = int(all_data["ID"].max() + 1) if not all_data.empty else 1
    
    new_row = pd.DataFrame([[
        new_id, checkin_date, user, points, fine, 
        " | ".join(details), 0, water_cups, weight_kg
    ]], columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])
    
    new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
    
    st.balloons()
    st.success(f"打卡成功！积分：{points}，罚金：{fine}")
    st.rerun()

# --- 5. 累计榜单 ---
all_data = get_data()
st.markdown("---")
st.subheader("🏆 累计成就与面包进度")

c1, c2 = st.columns(2)
for i, name in enumerate(["刘蓝溪", "曾润姿"]):
    u_df = all_data[all_data["打卡人"] == name]
    pts, reds = u_df["积分"].sum(), u_df["兑换次数"].sum()
    
    with (c1 if i == 0 else c2):
        st.metric(label=f"👤 {name}", value=f"{pts} 分", delta=f"累计兑换 {int(reds)} 次")
        st.write(f"🥤 累计喝水：{int(u_df['喝水杯数'].sum())} 杯")
        
        if pts >= 20:
            if st.button(f"🎁 {name} 兑换面包 (-20分)", key=f"rd_{name}", use_container_width=True):
                rid = int(all_data["ID"].max() + 1) if not all_data.empty else 1
                r_row = pd.DataFrame([[rid, date.today(), name, -20, 0, "兑换奖励", 1, 0, 0]], 
                                     columns=["ID", "日期", "打卡人", "积分", "罚金", "详情", "兑换次数", "喝水杯数", "具体体重"])
                r_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
                st.rerun()

# --- 6. 📈 体重变化曲线 ---
st.markdown("---")
st.subheader("📈 体重趋势看板 (kg)")
chart_data = all_data[all_data["具体体重"] > 0].copy()
if not chart_data.empty:
    chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x=alt.X('日期:T', title='日期'),
        y=alt.Y('具体体重:Q', title='体重 (kg)', scale=alt.Scale(zero=False)),
        color='打卡人:N',
        tooltip=['日期', '打卡人', '具体体重']
    ).properties(height=400).interactive()
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("暂无体重数据，请在打卡时输入具体体重以生成曲线。")

# --- 7. 历史记录与管理 ---
st.markdown("---")
tab_list, tab_admin = st.tabs(["📊 历史所有记录", "🛠️ 管理"])
with tab_list:
    if not all_data.empty:
        st.dataframe(all_data.sort_values(by=["日期", "ID"], ascending=[False, False]), use_container_width=True)
    else:
        st.write("暂无记录。")

with tab_admin:
    target_id = st.number_input("输入删除记录 ID", min_value=1, step=1)
    if st.button("确认删除", type="primary"):
        updated_df = all_data[all_data["ID"] != target_id]
        updated_df.to_csv(DATA_FILE, index=False)
        st.rerun()
