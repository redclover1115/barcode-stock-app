import streamlit as st
import requests
import time

st.set_page_config(page_title="生産現場用 バーコード在庫登録システム", layout="centered")

st.title("🏭 生産現場用 バーコード在庫登録システム")
st.write("新レイアウト対応版（担当者更新・常時在庫表示・修正選択仕様）")

# ★吉本さんの本物のGASウェブアプリURLをここに貼り付けてください★
gas_url = "https://google.com" 

# -------------------------------------------------------------
# 0. 担当者の選択（ご指定の16名を追加、手動で変えるまで維持）
# -------------------------------------------------------------
if "selected_user" not in st.session_state:
    st.session_state.selected_user = "吉本"

user_list = [
    "吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", 
    "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"
] 

user_name = st.selectbox("👤 本日の登録者を選択してください", user_list, index=user_list.index(st.session_state.selected_user))
st.session_state.selected_user = user_name

st.markdown("### =======================================")

# =============================================================
# 【上半分】いままで通りの「新規加算 登録エリア」
# =============================================================
st.subheader("📥 1. 通常の数量加算（新規登録）")

if "reg_category" not in st.session_state:
    st.session_state.reg_category = "生産途中"

reg_category = st.radio(
    "👇 数量を加算したい項目を選択してください",
    ("生産途中", "スペーサー加工待ち", "半受注完成品", "在庫数量"),
    horizontal=True,
    key="reg_cat_radio"
)

if "trigger_clear_reg" not in st.session_state:
    st.session_state.trigger_clear_reg = False

reg_key = "jan_reg_active"
if st.session_state.trigger_clear_reg:
    reg_key = "jan_reg_reset"
    st.session_state.trigger_clear_reg = False

jan_reg = st.text_input("👉 加算するバーコード（JAN）をスキャン：", value="", key=reg_key)
count_reg = st.slider("👉 加算する数量をスクロールで入力：", min_value=1, max_value=100, value=1, key="count_reg_slider")

if st.button("🚀 上記の項目に数量を加算する", use_container_width=True):
    if jan_reg.strip() != "":
        with st.spinner("クラウドに数量を加算中..."):
            try:
                payload = {"janCode": jan_reg.strip(), "status": reg_category, "count": count_reg, "user": user_name, "action": "register"}
                res = requests.post(gas_url, json=payload, timeout=10).json()
                if res.get("status") == "success":
                    st.success(f"✅ 【{reg_category}】に数量 {count_reg} 個を加算登録しました！")
                    time.sleep(2)
                    st.session_state.trigger_clear_reg = True
                    st.rerun()
                else:
                    st.error(f"❌ エラー：{res.get('message')}")
            except Exception as e:
                st.error(f"🚨 通信エラー: {str(e)}")

st.markdown("### =======================================")

# =============================================================
# 【下半分】常時在庫状況 表示 ＆ 修正する 選択エリア
# =============================================================
st.subheader("🔍 2. 現在の在庫状況 確認・直接修正")

if "trigger_clear_mod" not in st.session_state:
    st.session_state.trigger_clear_mod = False
if "mod_stock_data" not in st.session_state:
    st.session_state.mod_stock_data = None
if "mod_item_name" not in st.session_state:
    st.session_state.mod_item_name = ""
if "last_mod_jan" not in st.session_state:
    st.session_state.last_mod_jan = ""

mod_key = "jan_mod_active"
if st.session_state.trigger_clear_mod:
    mod_key = "jan_mod_reset"
    st.session_state.trigger_clear_mod = False

jan_mod = st.text_input("🔍 在庫を確認するバーコード（JAN）をスキャン：", value="", key=mod_key)

if jan_mod and jan_mod.strip() != "" and jan_mod.strip() != st.session_state.last_mod_jan:
    current_jan = jan_mod.strip()
    st.session_state.last_mod_jan = current_jan
    try:
        res = requests.post(gas_url, json={"janCode": current_jan, "status": "生産途中", "count": 0, "user": user_name, "action": "check"}, timeout=10).json()
        if res.get("status") == "success":
            st.session_state.mod_item_name = res.get("itemName", "商品名不明")
            st.session_state.mod_stock_data = res.get("stockData")
    except:
        pass

if st.session_state.mod_item_name:
    st.info(f"📦 対象商品: **{st.session_state.mod_item_name}**")
    if st.session_state.mod_stock_data:
        st.write("📊 **現在のシート内 在庫数（常時確認用）**")
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("スペーサー加工待ち", f"{st.session_state.mod_stock_data['spacer']} 個")
        col_s2.metric("生産途中", f"{st.session_state.mod_stock_data['seisan']} 個")
        col_s3.metric("半受注完成品", f"{st.session_state.mod_stock_data['hanjyu']} 個")

    st.markdown("---")
    
    is_modify_mode = st.checkbox("✏️ 登録数量を直接上書き修正する", value=False)

    if is_modify_mode:
        st.write("🔧 **数量の直接上書き修正モード**")
        mod_category = st.radio("👇 修正したい項目（コマンド）を選択してください", ("スペーサー加工待ち", "生産途中", "半受注完成品", "在庫数量"), horizontal=True, key="mod_cat_radio")

        default_mod_count = 0
        if st.session_state.mod_stock_data:
            if mod_category == "スペーサー加工待ち": default_mod_count = int(st.session_state.mod_stock_data['spacer'])
            elif mod_category == "生産途中": default_mod_count = int(st.session_state.mod_stock_data['seisan'])
            elif mod_category == "半受注完成品": default_mod_count = int(st.session_state.mod_stock_data['hanjyu'])

        count_mod = st.slider(f"👉 【 {mod_category} 】の正しい数量を指定してください", min_value=0, max_value=200, value=default_mod_count, key="count_mod_slider")

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("🚀 この内容で数量を上書き（修正）する", use_container_width=True):
                with st.spinner("クラウド上の在庫データを直接書き換え中..."):
                    try:
                        payload = {"janCode": st.session_state.last_mod_jan, "status": mod_category, "count": count_mod, "user": user_name, "action": "modify"}
                        res = requests.post(gas_url, json=payload, timeout=10).json()
                        if res.get("status") == "success":
                            st.success(f"✅ 【{mod_category}】の数量を {count_mod} 個に直接上書き修正しました！")
                            time.sleep(2)
                            st.session_state.trigger_clear_mod = True
                            st.session_state.mod_stock_data = None
                            st.session_state.mod_item_name = ""
                            st.session_state.last_mod_jan = ""
                            st.rerun()
                    except Exception as e:
                        st.error(f"🚨 通信エラー: {str(e)}")
        with btn_col2:
            if st.button("❌ 修正をキャンセルして閉じる", use_container_width=True):
                st.session_state.trigger_clear_mod = True
                st.session_state.mod_stock_data = None
                st.session_state.mod_item_name = ""
                st.session_state.last_mod_jan = ""
                st.rerun()
