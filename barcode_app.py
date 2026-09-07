import streamlit as st
import requests

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

# スキャン方法の選択肢
scan_method = st.radio(
    "🔍 スキャン方法を選択してください",
    ("🔌 Bluetoothハンディ（キーコード入力）", "📷 携帯のカメラで読み取る"),
    horizontal=True
)

st.markdown("---")

# 一時的な記憶領域（セッション）の初期化
if "step" not in st.session_state:
    st.session_state.step = 1
if "jan_code" not in st.session_state:
    st.session_state.jan_code = ""

# --- 🔄 【ステップ1】バーコード読み取り画面 ---
if st.session_state.step == 1:
    
    if scan_method == "📷 携帯のカメラで読み取る":
        st.write("👇 スマホのカメラ機能をお使いください")
        img_file = st.camera_input("バーコードを撮影", label_visibility="collapsed")
        
        if img_file is not None:
            from PIL import Image
            from pyzbar.pyzbar import decode
            image = Image.open(img_file)
            barcodes = decode(image)
            if barcodes:
                st.session_state.jan_code = barcodes.data.decode('utf-8').strip()
                st.session_state.step = 2
                st.rerun()
            else:
                st.warning("⚠️ バーコードがうまく認識できませんでした。")
                
    else:
        # 💡ハンディで「ピッ」とやって自動Enterが押されると、自動的にstep=2へ画面が切り替わります
        input_jan = st.text_input("📦 JANコード（バーコードをスキャン）", max_chars=13, placeholder="ここにカーソルを合わせてピッしてください")
        if input_jan:
            st.session_state.jan_code = str(input_jan).strip()
            st.session_state.step = 2
            st.rerun()

# --- 🔢 【ステップ2】項目振り分けと数量の入力画面 ---
elif st.session_state.step == 2:
    st.info(f"📋 読み込み完了 ｜ JANコード: **{st.session_state.jan_code}**")
    
    with st.form(key='count_form'):
        category = st.radio(
            "登録する項目を選択してください",
            (
                "生産途中",
                "枠在庫",
                "受注生産",
                "在庫数量"
            ),
            horizontal=True
        )
        
        count = st.number_input(f"[{category}] の現在数量（実数を入力）", min_value=0, value=0, step=1)
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button(label="在庫データを更新する")
        with col2:
            cancel_button = st.form_submit_button(label="スキャンをやり直す")

            
    if submit_button:
        with st.spinner("クラウド上の在庫データを書き換え中..."):
            try:
                # 項目名（category）も一緒にGoogleスプレッドシートへ送信
                payload = {"jan": st.session_state.jan_code, "count": int(count), "category": category}
                response = requests.post(GAS_URL, json=payload, timeout=10)
                result = response.json()
                
                if result.get("status") == "success":
                    st.success(f"🎉 成功: 【{category}】の在庫を {count} 個 に修正しました！")
                    st.balloons()
                    # 登録が終わったら、自動でステップ1（スキャン待ち）に戻る
                    st.session_state.step = 1
                    st.session_state.jan_code = ""
                else:
                    st.error(f"❌ エラー: {result.get('message')}")
            except Exception as e:
                st.error("通信エラーが発生しました。")
                
    if cancel_button:
        st.session_state.step = 1
        st.session_state.jan_code = ""
        st.rerun()
