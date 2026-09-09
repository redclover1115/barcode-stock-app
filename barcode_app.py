import streamlit as st
import requests

# アプリのタイトル
st.title("🖨️ バーコード在庫管理アプリ")
st.write("新レイアウト対応版（担当者更新・工程移動チェック・マイナス理由入力機能付き）")

# 1. 担当者の選択（指定のリストに更新完了）
st.subheader("👤 本日の登録者を選択してください")
user_name = st.selectbox(
    "担当者名", 
    ["吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"]
) 

st.markdown("---")

# =========================================================
# ⚠️ ご自身のGASのウェブアプリURLに差し替えてください
# =========================================================
GAS_URL = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec" 


# =========================================================
# 📥 1. 通常の数量加算（新規登録）
# =========================================================
st.subheader("📥 1. 通常の数量加算（新規登録）")

# 工程（ステータス）の選択
status = st.radio(
    "数量を加算したい項目を選択してください",
    ("生産途中", "スペーサー加工待ち", "半受注完成品", "製造指示依頼"),
    horizontal=True,
    key="reg_status"
)

# バーコードスキャン入力
jan_code = st.text_input("📋 加算するバーコード（JAN）をスキャン：", key="jan_input")

# 数量の入力
count = st.number_input("➕ 加算する数量を入力：", min_value=1, value=1, step=1, key="reg_count")

# 通常の登録ボタン
if st.button("上記の項目に数量を加算する", key="btn_register"):
    if not jan_code:
        st.warning("⚠️ JANコードを入力またはスキャンしてください。")
    else:
        payload = {
            "janCode": jan_code,
            "status": status,
            "count": count,
            "user": user_name,
            "action": "register"
        }
        
        # 数量不一致のセッション状態をリセット
        st.session_state["mismatch_detected"] = False
        
        with st.spinner("スプレッドシートの在庫を確認中..."):
            try:
                response = requests.post(GAS_URL, json=payload)
                res_data = response.json()
                
                if res_data.get("status") == "success":
                    st.success(f"⭕ 登録および工程移動が通常完了しました！\n\n**商品名**: {res_data.get('itemName')}")
                    st.write("### 📊 現在の在庫・合計状況")
                    st.json({
                        "今回のアイテム在庫": res_data.get("stockData"),
                        "全1万行の総合計値": res_data.get("grandTotalData")
                    })
                    
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


# 🚨 数量不一致エラーが発生した時だけ「動的」に出現するフォーム
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
    
    with st.form("reason_input_form"):
        st.write("### 📉 マイナス理由の内訳入力")
        col1, col2, col3 = st.columns(3)
        with col1:
            count_shikka = st.number_input("1. 出荷された", min_value=0, value=0, step=1, key="count_shikka")
        with col2:
            count_furyo = st.number_input("2. 不良", min_value=0, value=0, step=1, key="count_furyo")
        with col3:
            count_sonota = st.number_input("3. その他", min_value=0, value=0, step=1, key="count_sonota")
            
        submit_reason = st.form_submit_button("内訳を確定して再送信する")
        
        if submit_reason:
            total_calculated = details['inputCount'] + count_shikka + count_furyo + count_sonota
            
            if total_calculated == details['prevCount']:
                retry_payload = st.session_state["original_payload"]
                retry_payload["forceHeader"] = True
                retry_payload["countShikka"] = count_shikka
                retry_payload["countFuryo"] = count_furyo
                retry_payload["countSonota"] = count_sonota
                
                with st.spinner("内訳を送信し、前工程をクリア中..."):
                    try:
                        retry_response = requests.post(GAS_URL, json=retry_payload)
                        retry_res_data = retry_response.json()
                        
                        if retry_res_data.get("status") == "success":
                            st.success("⭕ 理由を確認しました。前工程を0にして移動が完了しました！")
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
                gap = details['prevCount'] - total_calculated
                if gap > 0:
                    st.warning(f"❌ 数量がまだ **{gap}個** 足りません。理由の内訳を正しく増やしてください。")
                else:
                    st.warning(f"❌ 内訳の合計が前工程の数を **{abs(gap)}個** 超えています。減らしてください。")

st.markdown("---")

# =========================================================
# 🔍 2. 現在の在庫状況確認・直接修正
# =========================================================
st.subheader("🔍 2. 現在の在庫状況確認・直接修正")

status_modify = st.radio(
    "直接修正したい項目を選択してください",
    ("生産途中", "スペーサー加工待ち", "半受注完成品", "製造指示依頼"),
    horizontal=True,
    key="modify_status"
)

jan_code_modify = st.text_input("📋 在庫を確認・修正するバーコード（JAN）をスキャン：", key="jan_modify")
count_modify = st.number_input("📝 上書き修正する数量を入力：", min_value=0, value=0, step=1, key="modify_count")

if st.button("数値を直接上書き修正（修正・削除用）", key="btn_modify"):
    if not jan_code_modify:
        st.warning("⚠️ JANコードを入力またはスキャンしてください。")
    else:
        payload_modify = {
            "janCode": jan_code_modify,
            "status": status_modify,
            "count": count_modify,
            "user": user_name,
            "action": "modify"
        }
        with st.spinner("スプレッドシートの数値を直接上書き中..."):
            try:
                response = requests.post(GAS_URL, json=payload_modify)
                res_data = response.json()
                
                if res_data.get("status") == "success":
                    st.success(f"⭕ 上書き修正が完了しました！\n\n**商品名**: {res_data.get('itemName')}")
                    st.write("### 📊 最新の在庫・合計状況")
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

st.markdown("---")

# =========================================================
# 📋 3. 単品コードでの現在在庫確認
# =========================================================
st.subheader("📋 3. 単品コードでの現在在庫確認")

jan_code_check = st.text_input("🔍 在庫のみを確認するバーコード（JAN）をスキャン：", key="jan_check")

if st.button("現在の在庫状況を確認する", key="btn_check"):
    if not jan_code_check:
        st.warning("⚠️ JANコードを入力またはスキャンしてください。")
    else:
        payload_check = {
            "janCode": jan_code_check,
            "action": "check"
        }
        with st.spinner("スプレッドシートから現在の在庫を取得中..."):
            try:
                response = requests.post(GAS_URL, json=payload_check)
                res_data = response.json()
                
                if res_data.get("status") == "success":
                    st.info(f"📦 **商品名**: {res_data.get('itemName')}")
                    st.write("### 📊 現在の在庫・合計状況")
                    st.json({
                        "現在のアイテム在庫": res_data.get("stockData"),
                        "全1万行の総合計値": res_data.get("grandTotalData")
                    })
                elif res_data.get("status") == "not_found":
                    st.error(f"❌ エラー：{res_data.get('message')}")
                else:
                    st.error(f"❌ サーバーエラー：{res_data.get('message')}")
            except Exception as e:
                st.error(f"🔌 通信エラーが発生しました: {str(e)}")
