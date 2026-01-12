st.subheader("🗑️ 管理记录")
    if not all_data.empty:
        # 创建一个下拉框或者数字输入框来选择 ID
        delete_id = st.number_input("输入要删除的记录 ID", min_value=1, step=1)
        
        if st.button("确认删除记录", type="primary"): # 改为 primary 颜色更醒目
            # 读取最新数据
            df_to_delete = pd.read_csv(DATA_FILE)
            
            # 检查 ID 是否存在
            if delete_id in df_to_delete["ID"].values:
                # 过滤掉要删除的行
                df_to_delete = df_to_delete[df_to_delete["ID"] != delete_id]
                # 保存回文件
                df_to_delete.to_csv(DATA_FILE, index=False)
                st.success(f"ID 为 {delete_id} 的记录已成功删除！")
                
                # --- 关键步骤：强制刷新页面 ---
                st.rerun() 
            else:
                st.error(f"找不到 ID 为 {delete_id} 的记录，请检查后再试。")
