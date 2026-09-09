import streamlit as st
import requests

# アプリのタイトル
st.title("🖨️ バーコード在庫管理アプリ")
st.write("新レイアウト対応版（担当者更新・上下両方でリアルタイム在庫表示・全体総合計仕様）")

# 1. 担当者の選択
st.subheader("👤 本日の登録者を選択してください")
user_name = st.selectbox("担当者名", ["吉本", "山田", "田中", "佐藤"]) # 必要に応じてお名前を変更してください

st.markdown("---")

# 2. 通常の数量加算（新規登録）
st.subheader("📥 1. 通常の数量加算（新規登録）")

# 工程（ステータス）の選択
status = st.radio(
    "数量を加算したい項目を選択してください",
    ("生産途中", "スペーサー加工待ち", "半受注完成品", "製造指示依頼"),
    horizontal=True
)

# バーコードスキャン入力
jan_code = st.text_input("📋 加算するバーコード（JAN）をスキャン：", key="jan_input")

# 数量の入力
count = st.number_input("➕ 加算する数量を入力：", min_value=1, value=1, step=1)

# GASのウェブアプリURL（ご自身のURLに差し替えてください）
GAS_URL = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec" 

# 登録ボタン
if st.button("上記の項目に数量を加算する"):
    if not jan_code:
        st.warning("⚠️ JANコードを入力またはスキャンしてください。")
    else:
        # GASへ送信するデータ（ペイロード）の作成
        payload = {
            "janCode": jan_code,
            "status": status,
            "count": count,
            "user": user_name,
            "action": "register"
        }
        
        with st.spinner("スプレッドシートを更新中..."):
            try:
                # GASへPOSTリクエストを送信
                response = requests.post(GAS_URL, json=payload)
                res_data = response.json()
                
                # 結果の判定
                if res_data.get("status") == "success":
                    st.success(f"⭕ 登録完了しました！\n\n**商品名**: {res_data.get('itemName')}")
                    
                    # 最新の個別在庫データと全体総合計を表示
                    st.write("### 📊 現在の在庫・合計状況")
                    st.json({
                        "今回のアイテム在庫": res_data.get("stockData"),
                        "全1万行の総合計値": res_data.get("grandTotalData")
                    })
                elif res_data.get("status") == "not_found":
                    st.error(f"❌ エラー：{res_data.get('message')}")
                else:
                    st.error(f"❌ サーバーエラー：{res_data.get('message')}")
                    
            except Exception as e:
                st.error(f"🔌 通信エラーが発生しました: {str(e)}")
