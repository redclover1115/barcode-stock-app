import streamlit as st
import requests

# アプリのタイトル
st.title("🖨️ バーコード在庫管理アプリ")
st.write("新レイアウト対応版（担当者更新・工程移動チェック・マイナス理由入力機能付き）")

# 1. 担当者の選択
st.subheader("👤 本日の登録者を選択してください")
user_name = st.selectbox("担当者名", [ "吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", 
    "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"]) 

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

# =========================================================
# ⚠️ ご自身のGASのウェブアプリURLに差し替えてください
# =========================================================
GAS_URL = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec" 

# 通常の登録ボタン
if st.button("上記の項目に数量を加算する"):
    if not jan_code:
        st.warning("⚠️ JANコードを入力またはスキャンしてください。")
    else:
        # 初回送信用のデータ（ペイロード）作成
        payload = {
            "janCode": jan_code,
            "status": status,
            "count": count,
            "user": user_name,
            "action": "register"
        }
        
        # 次回以降使えるようセッションを初期化
        st.session_state["mismatch_detected"] = False
        
        with st.spinner("スプレッドシートの在庫を確認中..."):
            try:
                response = requests.post(GAS_URL, json=payload)
                res_data = response.json()
                
                # パターン①：通常完了（数が一致、または最初の工程など）
                if res_data.get("status") == "success":
                    st.success(f"⭕ 登録および工程移動が通常完了しました！\n\n**商品名**: {res_data.get('itemName')}")
                    st.write("### 📊 現在の在庫・合計状況")
                    st.json({
                        "今回のアイテム在庫": res_data.get("stockData"),
                        "全1万行の総合計値": res_data.get("grandTotalData")
                    })
                    
                # パターン②：前工程と数量が合わないエラーを検知した場合
                elif res_data.get("status") == "qty_mismatch":
                    st.session_state["mismatch_detected"] = True
                    st.session_state["prev_details"] = res_data["details"]
                    st.session_state["original_payload"] = payload
                    st.session_state["item_name_temp"] = res_data.get("itemName", "商品名未設定")
                    
                elif res_data.get("status") == "not_found":
                    st.error(f"❌ エラー：{res_data.get('message')}")
                else:
                    st.error(f"❌ サーバーエラー：{res_data.get('message')}")
                    
            except Exception as e:
                st.error(f"🔌 通信エラーが発生しました: {str(e)}")


# =========================================================
# 🚨 数量不一致エラーが発生した時だけ「動的」に出現するフォーム
# =========================================================
if st.session_state.get("mismatch_detected", False):
    details = st.session_state["prev_details"]
    
    st.markdown("---")
    st.error("⚠️ ※前工程からの数が合いません。")
    st.info(
        f"**【対象商品】: {st.session_state['item_name_temp']}**\n\n"
        f"・前工程（{details['prevStatus']}）にあった数: **{details['prevCount']}** 個\n\n"
        f"・今回移動させようとした数: **{details['inputCount']}** 個\n\n"
        f"➡️ 差分の **{details['prevCount'] - details['inputCount']}** 個について、以下のマイナス理由の内訳を入力してください。"
    )
    
    # 理由入力フォーム
    with st.form("reason_input_form"):
        st.write("### 📉 マイナス理由の内訳入力")
        col1, col2, col3 = st.columns(3)
        with col1:
            count_shikka = st.number_input("1. 出荷された", min_value=0, value=0, step=1)
        with col2:
            count_furyo = st.number_input("2. 不良", min_value=0, value=0, step=1)
        with col3:
            count_sonota = st.number_input("3. その他", min_value=0, value=0, step=1)
            
        submit_reason = st.form_submit_button("内訳を確定して再送信する")
        
        if submit_reason:
            # 「今回移動する数」＋「各マイナス理由」の合計を計算
            total_calculated = details['inputCount'] + count_shikka + count_furyo + count_sonota
            
            # 前工程の総数とピッタリ一致するかチェック
            if total_calculated == details['prevCount']:
                retry_payload = st.session_state["original_payload"]
                retry_payload["forceHeader"] = True # GAS側にチェックをパスさせるフラグ
                retry_payload["countShikka"] = count_shikka
                retry_payload["countFuryo"] = count_furyo
                retry_payload["countSonota"] = count_sonota
                
                with st.spinner("内訳を送信し、前工程をクリア中..."):
                    try:
                        retry_response = requests.post(GAS_URL, json=retry_payload)
                        retry_res_data = retry_response.json()
                        
                        if retry_res_data.get("status") == "success":
                            st.success("⭕ 理由を確認しました。前工程を0にして移動が完了しました！")
                            # 完了したのでセッションをリセット
                            st.session_state["mismatch_detected"] = False
                            st.write("### 📊 最新の在庫・合計状況")
                            st.json({
                                "今回のアイテム在庫": retry_res_data.get("stockData"),
                                "全1万行の総合計値": retry_res_data.get("grandTotalData")
                            })
                        else:
                            st.error(f"❌ エラーが発生しました: {retry_res_data.get('message')}")
                    except Exception as e:
                        st.error(f"🔌 再通信エラーが発生しました: {str(e)}")
            else:
                # 合計が合わない場合の警告
                gap = details['prevCount'] - total_calculated
                if gap > 0:
                    st.warning(f"❌ 数量がまだ **{gap}個** 足りません。理由の内訳を正しく増やしてください。")
                else:
                    st.warning(f"❌ 内訳の合計が前工程の数を **{abs(gap)}個** 超えています。減らしてください。")
