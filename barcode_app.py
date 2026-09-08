import streamlit as st
import requests
import time

st.set_page_config(page_title="生産現場用 バーコード在庫登録システム", layout="centered")

st.title("🏭 生産現場用 バーコード在庫登録システム")
st.write("現場DX版（担当者プルダウン選択・全項目数量・自動更新防止仕様）")

# -------------------------------------------------------------
# 0. 登録者の選択エリア（ご指定のメンバーリストを反映）
# -------------------------------------------------------------
user_list = [
    "選択してください", 
    "吉本", "塚越", "岡本", "中島", "関口", "中島（２）", 
    "A", "B", "C", "D", "E", 
    "その他（未入力）"
]

if "selected_user" not in st.session_state:
    st.session_state.selected_user = "選択してください"

# スマホでも押しやすいプルダウン（セレクトボックス）
user_name = st.selectbox(
    "👤 本日の登録者名を選択してください：", 
    options=user_list,
    index=user_list.index(st.session_state.selected_user) if st.session_state.selected_user in user_list else 0,
    key="user_name_select"
)
st.session_state.selected_user = user_name

# 「選択してください」や「その他」の場合はシステム側に「未入力」として送信
final_user_name = user_name
if user_name == "選択してください" or user_name == "その他（未入力）":
    final_user_name = "未入力"

st.markdown("---")

# -------------------------------------------------------------
# 1. 登録する項目の選択
# -------------------------------------------------------------
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "生産途中"

category = st.radio(
    "【一括設定】登録する項目を先に選択してください",
    ("生産途中", "枠在庫", "半受注完成品", "在庫数量"),
    horizontal=True,
    index=("生産途中", "枠在庫", "半受注完成品", "在庫数量").index(st.session_state.selected_category)
)
st.session_state.selected_category = category

st.markdown("---")

# -------------------------------------------------------------
# 2. 入力（スキャン）エリアとセッション状態の管理
# -------------------------------------------------------------
if "processed_jan" not in st.session_state:
    st.session_state.processed_jan = ""
if "last_item_name" not in st.session_state:
    st.session_state.last_item_name = ""

# スマホでも手入力・スキャンがいつでも動く固定キー仕様
jan_code = st.text_input(
    f"👉 現在の登録モード: 【 {category} 】 (登録者: {final_user_name})\nバーコード（JANコード）をスキャンまたは手入力してください：",
    value="",
    key="jan_code_input"
)

count = st.number_input(f"👉 【 {category} 】の登録数量を入力してください", min_value=1, value=1, step=1, key="count_input")

# -------------------------------------------------------------
# 3. 操作ボタン
# -------------------------------------------------------------
btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    submit_button = st.button("🚀 この内容で登録する", use_container_width=True)
with btn_col2:
    clear_input_only = st.button("❌ 間違えたので入力を消す", use_container_width=True)

if clear_input_only:
    st.session_state["jan_code_input"] = ""
    st.session_state["count_input"] = 1
    st.rerun()

st.markdown("---")

if st.session_state.last_item_name:
    st.info(f"📦 直前にスキャンした商品: **{st.session_state.last_item_name}**")

# -------------------------------------------------------------
# 4. 送信処理（登録ボタン押下時のみ実行）
# -------------------------------------------------------------
if submit_button:
    current_jan = jan_code.strip() if jan_code else ""
    
    if current_jan == "":
        st.error("❌ エラー：バーコード（JANコード）が入力されていません。")
    else:
        st.session_state.processed_jan = current_jan
        
        with st.spinner("クラウド上の在庫データを更新中..."):
            try:
                payload = {
                    "janCode": current_jan,
                    "status": category,
                    "count": count,
                    "user": final_user_name
                }
                
                # 吉本さんのGASウェブアプリURL
                gas_url = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec" 
                
                response = requests.post(gas_url, json=payload, timeout=10)
                result = response.json()
                
                if result.get("status") == "success":
                    st.session_state.last_item_name = result.get("itemName", "商品名不明")
                    
                    st.success(f"✅ 【{category}】に数量 {count} 個で登録完了しました！ (登録者: {final_user_name})\n📦 商品名: {st.session_state.last_item_name} (JAN: {current_jan})")
                    
                    time.sleep(2)
                    
                    st.session_state["jan_code_input"] = ""
                    st.session_state["count_input"] = 1
                    st.rerun()
                    
                elif result.get("status") == "not_found":
                    st.error("❌ エラー：該当するJANコードがスプレッドシートに見つかりません。")
                    st.session_state.processed_jan = ""
                else:
                    st.error(f"⚠️ 登録失敗：{result.get('message', '不明なエラー')}")
                    st.session_state.processed_jan = ""
                    
            except Exception as e:
                st.error(f"🚨 通信エラーが発生しました: {str(e)}")
                st.session_state.processed_jan = ""
