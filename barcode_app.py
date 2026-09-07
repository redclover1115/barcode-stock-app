import streamlit as st
import requests

st.set_page_config(page_title="生産現場用 バーコード在庫登録システム", layout="centered")

st.title("🏭 生産現場用 バーコード在庫登録システム")
st.write("新レイアウト対応版（項目固定・連続スキャン仕様）")

# -------------------------------------------------------------
# 【機能変更】1. 最初に登録する項目を選択（手動で変えない限り維持されます）
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
# 2. JANコードの入力（スキャン）エリア
# -------------------------------------------------------------
# 入力後の自動リセット用セッション状態
if "jan_input" not in st.session_state:
    st.session_state.jan_input = ""

# バーコードスキャン入力欄
jan_code = st.text_input(
    f"👉 現在の登録モード: 【 {category} 】\nバーコード（JANコード）をスキャンしてください：",
    value=st.session_state.jan_input,
    key="jan_code_field"
)

# 数量入力（在庫数量モードの時だけ表示）
count = 1
if category == "在庫数量":
    count = st.number_input("登録する数量を入力してください", min_value=1, value=1, step=1)

# -------------------------------------------------------------
# 3. 送信処理（JANコードが入力されたら自動、またはボタンで送信）
# -------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    submit_button = st.button("手動で送信・登録する")
with col2:
    if st.button("クリア / スキャンやり直し"):
        st.session_state.jan_input = ""
        st.rerun()

# JANコードが入力された、または送信ボタンが押された場合の処理
if jan_code or submit_button:
    if jan_code.strip() != "":
        with st.spinner("クラウド上の在庫データを更新中..."):
            try:
                # 引き継ぎURL（GAS）への送信データ作成
                payload = {
                    "janCode": jan_code.strip(),
                    "status": category,  # 選択された項目（生産途中、枠在庫、受注生産、在庫数量）
                    "count": count
                }
                
                # GASの最新URL（※吉本さんの環境に合わせて環境変数等から読み込むか、ここに直接URLを記述してください）
                # ここでは一般的なGAS連携の構成を想定しています
                gas_url = "https://google.com" # ※実際のGASのWebアプリURLに書き換えてください
                
                response = requests.post(gas_url, json=payload, timeout=10)
                result = response.json()
                
                if result.get("status") == "success":
                    st.success(f"✅ 【{category}】に登録完了しました！ (JAN: {jan_code})")
                    # 次のスキャンのためにJAN入力欄だけをクリア（選択項目は維持）
                    st.session_state.jan_input = ""
                    st.rerun()
                elif result.get("status") == "not_found":
                    st.error("❌ エラー：該当するJANコードがスプレッドシートに見つかりません。")
                else:
                    st.error(f"⚠️ 登録失敗：{result.get('message', '不明なエラー')}")
                    
            except Exception as e:
                st.error(f"🚨 通信エラーが発生しました: {str(e)}")
