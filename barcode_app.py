import streamlit as st
import requests

# 💡 さきほど取得したGoogleの「ウェブアプリのURL」をここに貼り付けます
# ※次のステップでここをご自身の本物のURL（https://google.com...）に書き換えます
GAS_URL = "ここにコピーしたURLを貼り付けます"

# --- 🔒 新アプリ専用のパスワード認証機能 ---
def check_password():
    if "barcode_password_correct" not in st.session_state:
        st.session_state["barcode_password_correct"] = False
    if st.session_state["barcode_password_correct"]:
        return True

    st.title("🔒 社内在庫システム：認証画面")
    st.write("このアプリは生産現場・在庫管理メンバー専用です。")
    
    # 💡 新しい在庫アプリ用のパスワードです（自由に変更してください）
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
st.write("iPhoneに接続したBluetoothハンディでバーコードをスキャンしてください。")

# 入力フォームの作成
with st.form(key="stock_form", clear_on_submit=True):
    # ハンディでスキャンすると、ここに自動で13桁の数字が入ります
    jan_code = st.text_input("📦 JANコード（バーコードをスキャン）", max_chars=13, placeholder="ここにカーソルを合わせてピッとしてください")
    
    # 追加・登録する個数
    count = st.number_input("🔢 追加する在庫数", min_value=1, value=1, step=1)
    
    # 送信ボタン
    submit_button = st.form_submit_button(label="🚀 在庫データを更新する")

if submit_button:
    if not jan_code:
        st.warning("JANコードが空欄です。バーコードをスキャンしてください。")
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
                st.error(f"通信エラーが発生しました。URLが正しいか確認してください。")
