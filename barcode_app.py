import streamlit as st
import requests

st.title("🎰 工程在庫管理スロットアプリ")
st.write("7工程ジャンプ完全対応・新世代ドラムスロットUIモデル")

# 1. 共通GAS URL
GAS_URL = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec"

# リストの定義
users = ["吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"]
processes = ["棹カット", "枠組み", "スペーサー加工", "中身セット", "金具打ち", "仕上げ", "完成"]
counts_reg = [i for i in range(1, 101)]     # 1〜100
counts_modify = [i for i in range(0, 501)]  # 0〜500
counts_reason = [i for i in range(0, 101)]  # 0〜100

# --- 🎰 純正風スクロール選択UI ---
def create_secure_drum(label, options, key, default_idx=0):
    st.markdown(
        """
        <style>
            div[data-testid="stSelectbox"] > div {
                border: 2px solid #a6a6a6 !important;
                border-radius: 12px !important;
                background: linear-gradient(to bottom, #f0f0f0, #fff 50%, #f0f0f0) !important;
                box-shadow: inset 0 0 10px rgba(0,0,0,0.1) !important;
                height: 45px !important;
            }
            div[data-testid="stSelectbox"] label p {
                font-weight: bold !important;
                color: #222 !important;
                font-size: 16px !important;
            }
        </style>
        """, 
        unsafe_allow_html=True
    )
    selected_value = st.selectbox(f"**{label}**", options, index=default_idx, key=key)
    return selected_value

# 📊 指定の仕様に合わせた新しい在庫表示関数
def display_stock_and_total(res_data, title="📊 現在の在庫状況"):
    st.write(f"### {title}")
    s = res_data.get("stockData", {})
    
    st.write("**◆ 今回のアイテムの工程内訳**")
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("棹カット", f"{s.get('katto',0)}個")
    c2.metric("枠組み", f"{s.get('wakugumi',0)}個")
    c3.metric("スペーサー", f"{s.get('spacer',0)}個")
    c4.metric("中身セット", f"{s.get('nakami',0)}個")
    c5.metric("金具打ち", f"{s.get('kanagu',0)}個")
    c6.metric("仕上げ", f"{s.get('shiage',0)}個")
    c7.metric("完成", f"{s.get('kanryo',0)}個")
    
    # 【仕様変更】生産棚在庫（受注生産品完成在庫の全体合計）を個別の目立つ大型カードで表示
    st.markdown("---")
    st.write("**◆ 工場全体の在庫集計**")
    tana_zaiko = res_data.get("seisanTanaZaiko", 0)
    st.metric("📦 生産棚在庫 (完成品合計)", f"{tana_zaiko} 個")

# メイン画面構築：担当者選択
user_name = create_secure_drum("👤 担当者選択（スクロール選択）", users, "v_user", 0)

st.markdown("---")

# =========================================================
# 📥 1. 通常の数量加算（新規登録）
# =========================================================
st.subheader("📥 1. 通常の数量加算（新規登録）")

status = create_secure_drum("🚩 移動先の工程を選択（スクロール）", processes, "v_status_reg", 0)
jan_code = st.text_input("📋 加算するバーコード（JAN）をスキャン：", key="jan_reg_input")
count_val = create_secure_drum("➕ 登録数量を選択（スクロール）", counts_reg, "v_count_reg", 0)

if st.button("🎰 上記の内容で通常加算登録をする", key="btn_register"):
    if not jan_code:
        st.warning("⚠️ JANコードをスキャンしてください。")
    else:
        payload = { "janCode": jan_code, "status": status, "count": int(count_val), "user": user_name, "action": "register" }
        st.session_state["mismatch_detected"] = False
        with st.spinner("スプレッドシートを更新中..."):
            try:
                res = requests.post(GAS_URL, json=payload).json()
                if res.get("status") == "success":
                    st.success(f"⭕ {status} への工程移動が通常完了しました！")
                    display_stock_and_total(res)
                elif res.get("status") == "qty_mismatch":
                    st.session_state["mismatch_detected"] = True
                    st.session_state["prev_details"] = res["details"]
                    st.session_state["original_payload"] = payload
                    st.rerun()
                else:
                    st.error(f"エラー: {res.get('message')}")
            except Exception as e:
                st.error(f"通信エラー: {e}")

# 🚨 数量不一致エラー時のマイナス内訳
if st.session_state.get("mismatch_detected", False):
    d = st.session_state["prev_details"]
    st.error(f"⚠️ 前工程【{d['prevStatus']}】にあった数（{d['prevCount']}個）と、今回移動する数（{d['inputCount']}個）が合いません。")
    st.info("残りの差分について、出荷・不良・その他の内訳を回して合計を合わせてください。")
    
    shikka = create_secure_drum("📉 1. 出荷された数", counts_reason, "v_shikka", 0)
    furyo = create_secure_drum("📉 2. 不良の数", counts_reason, "v_furyo", 0)
    sonota = create_secure_drum("📉 3. その他の数", counts_reason, "v_sonota", 0)
    
    if st.button("内訳を確定して再送信"):
        if (d['inputCount'] + int(shikka) + int(furyo) + int(sonota)) == d['prevCount']:
            retry = st.session_state["original_payload"]
            retry.update({ "forceHeader": True, "countShikka": int(shikka), "countFuryo": int(furyo), "countSonota": int(sonota) })
            try:
                res = requests.post(GAS_URL, json=retry).json()
                if res.get("status") == "success":
                    st.success("⭕ 理由内訳を確認し、前工程をクリアして移動しました！")
                    st.session_state["mismatch_detected"] = False
                    display_stock_and_total(res)
            except Exception as e:
                st.error(f"再送信エラー: {e}")
        else:
            st.warning("❌ 内訳の合計が前工程の残数と一致しません。数値を合わせ直してください。")

st.markdown("---")

# =========================================================
# 🔍 2. 現在の在庫状況確認・直接修正
# =========================================================
st.subheader("🔍 2. 現在の在庫状況確認・直接修正")

status_modify = create_secure_drum("📝 直接修正したい工程を選択（スクロール）", processes, "v_status_modify", 0)
jan_code_modify = st.text_input("📋 在庫を確認・修正するバーコード（JAN）をスキャン：", key="jan_modify_input")
count_modify = create_secure_drum("📝 上書き修正する数量を選択（スクロール）", counts_modify, "v_count_modify", 0)

if st.button("数値を直接上書き修正（修正・削除用）", key="btn_modify"):
    if not jan_code_modify:
        st.warning("⚠️ JANコードをスキャンしてください。")
    else:
        payload_modify = { "janCode": jan_code_modify, "status": status_modify, "count": int(count_modify), "user": user_name, "action": "modify" }
        with st.spinner("スプレッドシートの数値を直接上書き中..."):
            try:
                res = requests.post(GAS_URL, json=payload_modify).json()
                if res.get("status") == "success":
                    st.success("⭕ 上書き修正が完了しました！")
                    display_stock_and_total(res, "📊 最新の在庫・合計状況")
                else:
                    st.error(f"エラー: {res.get('message')}")
            except Exception as e:
                st.error(f"通信エラー: {e}")

st.markdown("---")

# =========================================================
# 📋 3. 単品コードでの現在在庫確認
# =========================================================
st.subheader("📋 3. 単品コードでの現在在庫確認")

jan_code_check = st.text_input("🔍 在庫のみを確認するバーコード（JAN）をスキャン：", key="jan_check_input")

if st.button("現在の在庫状況を確認する", key="btn_check"):
    if not jan_code_check:
        st.warning("⚠️ JANコードをスキャンしてください。")
    else:
        payload_check = { "janCode": jan_code_check, "action": "check" }
        with st.spinner("スプレッドシートから現在の在庫を取得中..."):
            try:
                res = requests.post(GAS_URL, json=payload_check).json()
                if res.get("status") == "success":
                    st.info(f"📦 **商品名**: {res.get('itemName')}")
                    display_stock_and_total(res)
                else:
                    st.error(f"エラー: {res.get('message')}")
            except Exception as e:
                st.error(f"通信エラー: {e}")
