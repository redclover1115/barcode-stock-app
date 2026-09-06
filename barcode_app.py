import streamlit as st
import requests
from streamlit_barcode_reader import streamlit_barcode_reader

# 💡 吉本さんのGoogleウェブアプリのURLをここに自動セットしています
GAS_URL = "https://google.com"

# --- 🔒 パスワード認証機能 ---
def check_password():
    if "barcode_password_correct" not in st.session_state:
        st.session_state["barcode_password_correct"] = False
    if st.session_state["barcode_password_correct"]:
        return True

    st.title("🔒 社内在庫システム：認証画面")
    st.write("このアプリは生産現場・在庫管理メンバー専用です。")
    
    COMPANY_PASSWORD = "APJ_STOCK_2026" 

    user_password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if user_password == COMPANY_PASSWORD:
            st.session_state["barcode_password_correct"] = True
            st.rerun()
        else:
            st.error("パスワードが違います。")
    return False

if not check_password():
    st.stop()

# --- ここから下はアプリの本編 ---
st.set_page_config(page_title="バーコード在庫管理", layout="centered")
st.title("📱 生産現場用 バーコード在庫登録システム")

# 💡【機能追加】スキャン方法の選択肢（切り替えスイッチ）を設置
scan_method = st.radio(
    "🔍 スキャン方法を選択してください",
    ("🔌 Bluetoothハンディ（キーボード入力）", "📷 携帯のカメラで読み取る"),
    horizontal=True
)

st.markdown("---")

# スキャンされたJANコードを保持する変数
scanned_jan = ""

# --- 選択肢①：携帯カメラで読み取る場合 ---
if scan_method == "📷 携帯のカメラで読み取る":
    st.write("👇 枠の中にバーコードをかざしてください（ピントが合うと自動で読み取ります）")
    # スマホのカメラを起動する無料パーツ
    camera_result = streamlit_barcode_reader(key="barcode_reader")
    if camera_result:
        scanned_jan = str(camera_result).strip()
        st.success(f"🤖 カメラで読み取りました: 【{scanned_jan}】")

# --- 在庫登録フォーム ---
with st.form(key="stock_form", clear_on_submit=True):
    
    # 選択肢②（ハンディ）の場合は手入力枠に、カメラの場合は自動で数字が入るように設定
    if scan_method == "🔌 Bluetoothハンディ（キーボード入力）":
        jan_code = st.text_input("📦 JANコード（バーコードをスキャン）", max_chars=13, placeholder="ここにカーソルを合わせてピッとしてください")
    else:
        # カメラで読み取った値を自動で枠にセット
        jan_code = st.text_input("📦 JANコード（カメラ読取値）", value=scanned_jan, max_chars=13)
    
    # 追加・登録する個数
    count = st.number_input("🔢 追加する在庫数", min_value=1, value=1, step=1)
    
    # 送信ボタン
    submit_button = st.form_submit_button(label="🚀 在庫データを更新する")

if submit_button:
    if not jan_code:
        st.warning("JANコードが空欄です。バーコードをスキャンまたはカメラで読み取ってください。")
    else:
        with st.spinner("クラウド上の在庫データを書き換え中..."):
            try:
                # Googleスプレッドシート（GAS）へデータを送信
                payload = {"jan": str(jan_code).strip(), "count": int(count)}
                response = requests.post(GAS_URL, json=payload, timeout=10)
                result = response.json()
                
                if result.get("status") == "success":
                    st.success(f"🎉 成功: JANコード【{jan_code}】の商品在庫を {count} 個 追加しました！")
                    st.balloons() # 成功のお祝い風船
                else:
                    st.error(f"❌ エラー: {result.get('message')}")
                    
            except Exception as e:
                st.error(f"通信エラーが発生しました。URLやネットワーク環境を確認してください。")
