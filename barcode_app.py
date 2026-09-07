import streamlit as st
import requests

st.set_page_config(page_title="生産現場用 バーコード在庫登録システム", layout="centered")

st.title("🏭 生産現場用 バーコード在庫登録システム")
st.write("新レイアウト対応版（項目固定・全項目数量入力仕様）")

# -------------------------------------------------------------
# 1. 登録する項目の選択（手動で変えない限り維持されます）
# -------------------------------------------------------------
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "生産途中"

category = st.radio(
    "【一括設定】登録する項目を先に選択してください",
    ("生産途中", "枠在庫", "受注生産", "在庫数量"),
    horizontal=True,
    index=("生産途中", "枠在庫", "受注生産", "在庫数量").index(st.session_state.selected_category)
)
st.session_state.selected_category = category

st.markdown("---")

# -------------------------------------------------------------
# 2. 入力（スキャン）エリア
# -------------------------------------------------------------
# ループ防止用フラグ
if "processed_jan" not in st.session_state:
    st.session_state.processed_jan = ""

# バーコードスキャン入力欄
jan_code = st.text_input(
    f"👉 現在の登録モード: 【 {category} 】\nバーコード（JANコード）をスキャンしてください：",
    value="",
    key="jan_code_field"
)

# 【修正】すべての項目で数量入力欄を常に表示します
count = st.number_input(f"👉 【 {category} 】の登録数量を入力してください", min_value=1, value=1, step=1)

# -------------------------------------------------------------
# 3. 送信処理
# -------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    submit_button = st.button("手動で送信・登録する")
with col2:
    if st.button("クリア / スキャンやり直し"):
        st.session_state.processed_jan = ""
        st.rerun()

# 送信判定（JANが新しく入力された、またはボタンが押された場合）
if (jan_code and jan_code != st.session_state.processed_jan) or submit_button:
    current_jan = jan_code.strip() if jan_code else ""
    
    if current_jan != "":
        st.session_state.processed_jan = jan_code
        
        with st.spinner("クラウド上の在庫データを更新中..."):
            try:
                payload = {
                    "janCode": current_jan,
                    "status": category,
                    "count": count  # 入力された数量をGASへ送信
                }
                
                # ★吉本さんの本物のGASウェブアプリURLをここに貼り付けてください★
                gas_url = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec" 
                
                response = requests.post(gas_url, json=payload, timeout=10)
                result = response.json()
                
                if result.get("status") == "success":
                    st.success(f"✅ 【{category}】に数量 {count} 個で登録完了しました！ (JAN: {current_jan})")
                    st.rerun()
                elif result.get("status") == "not_found":
                    st.error("❌ エラー：該当するJANコードがスプレッドシートに見つかりません。")
                else:
                    st.error(f"⚠️ 登録失敗：{result.get('message', '不明なエラー')}")
                    
            except Exception as e:
                st.error(f"🚨 通信エラーが発生しました: {str(e)}")
