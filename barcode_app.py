import streamlit as st
import requests
import time

st.set_page_config(page_title="生産現場用 バーコード在庫登録システム", layout="centered")

st.title("🏭 生産現場用 バーコード在庫登録システム")
st.write("新レイアウト対応版（担当リスト固定・JAN即時在庫表示・在庫直接修正仕様）")

# -------------------------------------------------------------
# 0. 担当者の選択（変えるまで維持）
# -------------------------------------------------------------
if "selected_user" not in st.session_state:
    st.session_state.selected_user = "吉本"

user_list = ["吉本", "担当A", "担当B", "担当C"] 
user_name = st.selectbox("👤 本日の登録者を選択してください", user_list, index=user_list.index(st.session_state.selected_user))
st.session_state.selected_user = user_name

st.markdown("---")

# -------------------------------------------------------------
# 1. 入力（スキャン）エリアとセッション状態の管理
# -------------------------------------------------------------
if "processed_jan" not in st.session_state:
    st.session_state.processed_jan = ""
if "last_item_name" not in st.session_state:
    st.session_state.last_item_name = ""
if "trigger_clear" not in st.session_state:
    st.session_state.trigger_clear = False
if "current_stock" not in st.session_state:
    st.session_state.current_stock = None
if "last_scanned_jan" not in st.session_state:
    st.session_state.last_scanned_jan = ""

input_key = "jan_field_active"
if st.session_state.trigger_clear:
    input_key = "jan_field_reset"
    st.session_state.trigger_clear = False

jan_code = st.text_input(
    "👉 バーコード（JANコード）をスキャンしてください：",
    value="",
    key=input_key
)

# ★吉本さんの本物のGASウェブアプリURLをここに貼り付けてください★
gas_url = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec" 

# JANコードがスキャンされたら、即座に現在の在庫を取得
if jan_code and jan_code.strip() != "" and jan_code.strip() != st.session_state.last_scanned_jan:
    current_jan = jan_code.strip()
    st.session_state.last_scanned_jan = current_jan
    try:
        check_payload = {"janCode": current_jan, "status": "生産途中", "count": 0, "user": user_name, "action": "check"}
        response = requests.post(gas_url, json=check_payload, timeout=10)
        result = response.json()
        if result.get("status") == "success":
            st.session_state.last_item_name = result.get("itemName", "商品名不明")
            st.session_state.current_stock = result.get("stockData")
    except Exception as e:
        pass

# -------------------------------------------------------------
# 2. 【新仕様】商品名と現在の在庫数メーター表示（JANが読み込まれたら即表示）
# -------------------------------------------------------------
if st.session_state.last_item_name:
    st.info(f"📦 スキャン中の商品: **{st.session_state.last_item_name}**")
    
    if st.session_state.current_stock:
        st.write("📊 **現在のシート内 在庫数（確認用）**")
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("スペーサー加工待ち", f"{st.session_state.current_stock['spacer']} 個")
        col_s2.metric("生産途中", f"{st.session_state.current_stock['seisan']} 個")
        col_s3.metric("半受注完成品", f"{st.session_state.current_stock['hanjyu']} 個")

    st.markdown("---")
    st.write("✏️ **修正・登録コマンドの実行**")

    # 修正する項目（コマンド）の選択
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = "生産途中"

    category = st.radio(
        "👇 数量を修正・登録したい項目を選択してください",
        ("スペーサー加工待ち", "生産途中", "半受注完成品", "在庫数量"),
        horizontal=True,
        index=("スペーサー加工待ち", "生産途中", "半受注完成品", "在庫数量").index(st.session_state.selected_category)
    )
    st.session_state.selected_category = category

    # スクロールバー（スライダー）の初期値を、現在のシートの在庫数に自動で合わせる親切設計
    default_count = 1
    if st.session_state.current_stock:
        if category == "スペーサー加工待ち":
            default_count = int(st.session_state.current_stock['spacer'])
        elif category == "生産途中":
            default_count = int(st.session_state.current_stock['seisan'])
        elif category == "半受注完成品":
            default_count = int(st.session_state.current_stock['hanjyu'])

    # 数量修正用のスクロール（初期値が現在の在庫数になります）
    count = st.slider(f"👉 【 {category} 】の正しい数量をスクロールで指定してください", min_value=0, max_value=200, value=default_count, step=1)

    # -------------------------------------------------------------
    # 3. 操作ボタン
    # -------------------------------------------------------------
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        submit_button = st.button("🚀 この内容で登録（修正）する", use_container_width=True)
    with btn_col2:
        clear_input_only = st.button("❌ 間違えたので入力を消す", use_container_width=True)

    if clear_input_only:
        st.session_state.trigger_clear = True
        st.session_state.current_stock = None
        st.session_state.last_item_name = ""
        st.session_state.last_scanned_jan = ""
        st.rerun()

    # -------------------------------------------------------------
    # 4. 登録・修正の実行処理
    # -------------------------------------------------------------
    if submit_button and st.session_state.last_scanned_jan:
        with st.spinner("クラウド上の在庫データを書き換え中..."):
            try:
                payload = {
                    "janCode": st.session_state.last_scanned_jan,
                    "status": category,
                    "count": count,
                    "user": user_name,
                    "action": "register"
                }
                
                response = requests.post(gas_url, json=payload, timeout=10)
                result = response.json()
                
                if result.get("status") == "success":
                    st.success(f"✅ 【{category}】の数量を {count} 個に書き換え修正しました！")
                    time.sleep(2)
                    st.session_state.trigger_clear = True
                    st.session_state.current_stock = None
                    st.session_state.last_item_name = ""
                    st.session_state.last_scanned_jan = ""
                    st.rerun()
                else:
                    st.error(f"⚠️ 登録失敗：{result.get('message', '不明なエラー')}")
            except Exception as e:
                st.error(f"🚨 通信エラーが発生しました: {str(e)}")
