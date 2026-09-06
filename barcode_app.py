import streamlit as st
import requests
import cv2
import numpy as np

# 💡 吉本さんのGoogleウェブアプリのURL
GAS_URL = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxREaCe64GI-1uthsF7qzn89fh36J0FH1/exec"

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

# スキャン方法の選択肢（切り替えスイッチ）を設置
scan_method = st.radio(
    "🔍 スキャン方法を選択してください",
    ("🔌 Bluetoothハンディ（キーボード入力）", "📷 携帯のカメラで読み取る"),
    horizontal=True
)

st.markdown("---")

# スキャンされたJANコードを保持する変数
scanned_jan = ""

# --- 選択肢①：携帯カメラで読み取る場合（超安定版：st.camera_input方式） ---
if scan_method == "📷 携帯のカメラで読み取る":
    st.write("👇 「写真を撮る」を押してバーコードをパシャッと撮影してください")
    
    # Streamlit標準の、最もエラーが起きない超安定カメラ機能を起動
    img_file = st.camera_input("バーコードを撮影", label_visibility="collapsed")
    
    if img_file is not None:
        # 撮影された画像をシステムが読み解く処理
        file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
        opencv_img = cv2.imdecode(file_bytes, 1)
        
        # OpenCVのバーコード検出器を起動
        barcode_detector = cv2.barcode.BarcodeDetector()
        retval, decoded_info, decoded_type, points = barcode_detector.detectAndDecode(opencv_img)
        
        if retval and decoded_info[0]:
            scanned_jan = str(decoded_info[0]).strip()
            st.success(f"🤖 カメラでバーコードを検出しました: 【{scanned_jan}】")
        else:
            st.warning("⚠️ バーコードがうまく認識できませんでした。もう少し近づけるか、明るい場所で正面からもう一度撮影してください。")

# --- 在庫登録フォーム ---
with st.form(key="stock_form", clear_on_submit=True):
    
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
        st.warning("JANコードが空欄です。バーコードをスキャンまたはカメラで撮影してください。")
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
