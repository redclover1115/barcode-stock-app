import streamlit as st
import requests
import time

st.set_page_config(page_title="生産現場用 バーコード在庫登録システム", layout="centered")

st.title("🏭 生産現場用 バーコード在庫登録システム")
st.write("新レイアウト対応版（項目固定・商品名表示・数量スクロール・現在在庫表示仕様）")

# -------------------------------------------------------------
# 0. 登録者の手入力エリア
# -------------------------------------------------------------
if "selected_user" not in st.session_state:
    st.session_state.selected_user = ""

user_name = st.text_input(
    "👤 本日の登録者名を手入力してください（例：吉本）", 
    value=st.session_state.selected_user
)
st.session_state.selected_user = user_name

st.markdown("---")

# -------------------------------------------------------------
# 1. 登録する項目の選択
# -------------------------------------------------------------
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "生産途中"

category = st.radio(
    "【一括設定】登録する項目を先に選択してください",
    ("生産途中", "スペーサー加工待ち", "半受注完成品", "在庫数量"),
    horizontal=True,
    index=("生産途中", "スペーサー加工待ち", "半受注完成品", "在庫数量").index(st.session_state.selected_category)
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
if "trigger_clear" not in st.session_state:
    st.session_state.trigger_clear = False
if "current_stock" not in st.session_state:
    st.session_state.current_stock = None

input_key = "jan_field_active"
if st.session_state.trigger_clear:
    input_key = "jan_field_reset"
    st.session_state.trigger_clear = False

jan_code = st.text_input(
    f"👉 現在の登録モード: 【 {category} 】 (登録者: {user_name if user_name else '未入力'})\nバーコード（JANコード）をスキャンしてください：",
    value="",
    key=input_key
)

# 【修正】数量入力をスクロール（スライダー）形式に戻しました（1〜100個まで指でスライドして選べます）
count = st.slider(f"👉 【 {category} 】の登録数量をスクロールで入力してください", min_value=1, max_value=100, value=1, step=1)

# -------------------------------------------------------------
# 3. 操作ボタン
# -------------------------------------------------------------
btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    submit_button = st.button("🚀 この内容で登録する", use_container_width=True)
with btn_col2:
    clear_input_only = st.button("❌ 間違えたので入力を消す", use_container_width=True)

if clear_input_only:
    st.session_state.trigger_clear = True
    st.rerun()

st.markdown("---")

# 【新機能】直前に読み込んだ商品の「スプレッドシートの現在在庫数」を分かりやすく表示
if st.session_state.last_item_name:
    st.info(f"📦 直前にスキャンした商品: **{st.session_state.last_item_name}**")
    
    if st.session_state.current_stock:
        st.write("📊 **現在のシート内 在庫数一覧**")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("生産途中", f"{st.session_state.current_stock['seisan']} 個")
        col_s2.metric("ｽﾍﾟｰｻｰ待ち", f"{st.session_state.current_stock['spacer']} 個")
        col_s3.metric("半受注完成", f"{st.session_state.current_stock['hanjyu']} 個")
        col_s4.metric("在庫数量", f"{st.session_state.current_stock['zaiko']} 個")

# -------------------------------------------------------------
# 4. 送信処理
# -------------------------------------------------------------
is_scanned = jan_code and jan_code.strip() != "" and jan_code.strip() != st.session_state.processed_jan

if is_scanned or submit_button:
    current_jan = jan_code.strip() if jan_code else ""
    
    if current_jan != "":
        st.session_state.processed_jan = current_jan
        
        with st.spinner("クラウド上の在庫データを更新中..."):
            try:
                payload = {
                    "janCode": current_jan,
                    "status": category,
                    "count": count,
                    "user": user_name if user_name else "未入力"
                }
                
                # ★吉本さんの本物のGASウェブアプリURLをここに貼り付けてください★
                gas_url = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec" 
                
                response = requests.post(gas_url, json=payload, timeout=10)
                result = response.json()
                
                if result.get("status") == "success":
                    st.session_state.last_item_name = result.get("itemName", "商品名不明")
                    # GASから届いた最新在庫データを記憶
                    st.session_state.current_stock = result.get("stockData")
                    
                    st.success(f"✅ 【{category}】に数量 {count} 個で登録完了しました！ (登録者: {user_name})")
                    
                    time.sleep(2)
                    st.session_state.trigger_clear = True
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
