import streamlit as st
import requests

st.title("🎰 工程在庫管理スロットアプリ")
st.write("7工程ジャンプ完全対応・自動在庫先読みUIモデル")

# 1. 共通GAS URL
GAS_URL = "https://script.google.com/macros/s/AKfycbwNTMZAQ5edee04wb3zMtWPnMqjN8guEJQCG-zYOBQdvpyxvc7K5VoRmGiO6bZxImJy/exec"

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

# 📊 登録したJANコードのみの数量（7工程内訳）を表示する関数
def display_stock_only(res_data, title="📊 現在の在庫状況"):
    st.write(f"#### {title}")
    s = res_data.get("stockData", {})
    
    st.write("**◆ 今回のスキャンアイテムの工程内訳**")
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("棹カット", f"{s.get('katto',0)}個")
    c2.metric("枠組み", f"{s.get('wakugumi',0)}個")
    c3.metric("スペーサー", f"{s.get('spacer',0)}個")
    c4.metric("中身セット", f"{s.get('nakami',0)}個")
    c5.metric("金具打ち", f"{s.get('kanagu',0)}個")
    c6.metric("仕上げ", f"{s.get('shiage',0)}個")
    c7.metric("完成", f"{s.get('kanryo',0)}個")

# メイン画面：担当者選択
user_name = create_secure_drum("👤 担当者選択（スクロール選択）", users, "v_user", 0)

st.markdown("---")

# =========================================================
# 📥 1. 通常の数量加算（新規登録）
# =========================================================
st.subheader("📥 1. 通常の数量加算（新規登録）")

status = create_secure_drum("🚩 移動先の工程を選択（スクロール）", processes, "v_status_reg", 0)
jan_code = st.text_input("📋 加算するバーコード（JAN）をスキャン：", key="jan_reg_input")

# JANコードが入力されたら、自動でそのアイテムのみの在庫状況を読み込む
if jan_code:
    with st.spinner("スプレッドシートから現在の進捗を先読み中..."):
        try:
            check_payload_reg = { "janCode": jan_code, "action": "check" }
            auto_res_reg = requests.post(GAS_URL, json=check_payload_reg).json()
            if auto_res_reg.get("status") == "success":
                st.info(f"📦 **現在の対象アイテム**: {auto_res_reg.get('itemName')}")
                # 三連カード(完成品、V、W)は排除し、純粋なスキャンしたJANの7工程内訳のみを先読み表示
                display_stock_only(auto_res_reg, title="🔍 登録前のリアルタイム現在状況（先読み）")
            else:
                st.error(f"⚠️ {auto_res_reg.get('message')}")
        except Exception as e:
            st.error(f"データ自動取得エラー: {e}")

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
                    # 登録結果も工場全体合計は出さず、登録したJANのみの最新数量をパッと表示
                    display_stock_only(res, title="📊 登録完了後の最新在庫状況")
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
                    display_stock_only(res, title="📊 内訳確定後の最新在庫状況")
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

if jan_code_modify:
    with st.spinner("スプレッドシートから現在の在庫データを先読み中..."):
        try:
            check_payload = { "janCode": jan_code_modify, "action": "check" }
            auto_res = requests.post(GAS_URL, json=check_payload).json()
            if auto_res.get("status") == "success":
                st.info(f"📦 **現在の登録アイテム**: {auto_res.get('itemName')}")
                display_stock_only(auto_res, title="🔍 先読みされた現在のリアルタイム在庫状況")
            else:
                st.error(f"⚠️ {auto_res.get('message')}")
        except Exception as e:
            st.error(f"データ自動取得エラー: {e}")

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
                    display_stock_only(res, "📊 修正反映後の在庫・棚状況")
                else:
                    st.error(f"エラー: {res.get('message')}")
            except Exception as e:
                st.error(f"通信エラー: {e}")

st.markdown("---")

# =========================================================
# 📋 3. 生産ライン上の各工程合計数
# =========================================================
st.subheader("📋 3. 生産ライン上の各工程合計数")
st.write("ボタンを押すと、工場全データ（1万行）の各工程ごとの縦一列の純粋な合計値をリアルタイム集計します。")

if st.button("📊 工場全体の各工程合計数を集計する", key="btn_check_total"):
    payload_total = { "janCode": "", "action": "check_total" }
    with st.spinner("工場全体の全1万行データを一括集計中..."):
        try:
            res = requests.post(GAS_URL, json=payload_total).json()
            if res.get("status") == "success":
                t = res.get("grandTotalData", {})
                st.success("📊 工場全体の純粋な各工程合計数の集計が完了しました！")
                
                cols = st.columns(7)
                cols.metric("棹カット 合計", f"{t.get('katto', 0)} 個")
                cols.metric("枠組み 合計", f"{t.get('waku', 0)} 個")
                cols.metric("スペーサー 合計", f"{t.get('spacer', 0)} 個")
                cols.metric("中身セット 合計", f"{t.get('nakami', 0)} 個")
                cols.metric("金具打ち 合計", f"{t.get('kanagu', 0)} 個")
                cols.metric("仕上げ 合計", f"{t.get('shiage', 0)} 個")
                cols.metric("完成 合計", f"{t.get('kanryo', 0)} 個")
                
                st.markdown("---")
                
                total_cols = st.columns(3)
                total_cols.metric("🏭 各工程合計数(A)", f"{t.get('totalA', 0)} 個")
                total_cols.metric("📦 生産課管理棚合計数(B)", f"{t.get('totalB', 0)} 個")
                total_cols.metric("🧱 総合計(A+B)", f"{t.get('totalAB', 0)} 個")
                
            else:
                st.error(f"エラー: {res.get('message')}")
        except Exception as e:
            st.error(f"集計通信エラー: {e}")
