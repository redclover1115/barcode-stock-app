import streamlit as st
import requests

st.title("🎰 工程在庫管理スロットアプリ")
st.write("7工程ジャンプ完全対応・高速サクサク軽量化モデル")

GAS_URL = "https://script.google.com/macros/s/AKfycbwNTMZAQ5edee04wb3zMtWPnMqjN8guEJQCG-zYOBQdvpyxvc7K5VoRmGiO6bZxImJy/exec"

users = ["吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"]
processes = ["棹カット", "枠組み", "スペーサー加工", "中身セット", "金具打ち", "仕上げ", "完成"]
counts_reg = [i for i in range(1, 101)]
counts_modify = [i for i in range(0, 501)]
counts_reason = [i for i in range(0, 101)]

if "last_scanned_jan" not in st.session_state:
    st.session_state["last_scanned_jan"] = ""
if "cached_res" not in st.session_state:
    st.session_state["cached_res"] = None

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
            div[data-testid="stSelectbox"] label p { font-weight: bold !important; color: #222 !important; font-size: 16px !important; }
        </style>
        """, 
        unsafe_allow_html=True
    )
    return st.selectbox(f"**{label}**", options, index=default_idx, key=key)

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
    
    st.markdown("---")
    st.write("**◆ 今回のアイテムの見込生産・棚在庫の連動状況**")
    t1, t2, t3 = st.columns(3)
    
    def format_disp_value(val):
        val_str = str(val).strip()
        return "無し" if val_str in ["0", "", "0.0"] else ("受注品" if "受注品" in val_str else f"{val_str} 個")
            
    t1.metric("📦 生産棚在庫 (完成品)", f"{s.get('kanryo', 0)} 個")
    t2.metric("📈 見込生産在庫数 (V列)", format_disp_value(res_data.get("mikomiStock", "0")))
    t3.metric("⏳ 見込生産引当可能数 (W列)", format_disp_value(res_data.get("mikomiHikiate", "0")))

user_name = create_secure_drum("👤 担当者選択（スクロール選択）", users, "v_user", 0)
st.markdown("---")

# =========================================================
# 📥 1. 通常の数量加算（新規登録）
# =========================================================
st.subheader("📥 1. 通常の数量加算（新規登録）")
status = create_secure_drum("🚩 移動先の工程を選択（スクロール）", processes, "v_status_reg", 0)
jan_code = st.text_input("📋 加算するバーコード（JAN）をスキャン：", key="jan_reg_input")

if jan_code and jan_code != st.session_state["last_scanned_jan"]:
    with st.spinner("スプレッドシートから現在の進捗を先読み中..."):
        try:
            res = requests.post(GAS_URL, json={ "janCode": jan_code, "action": "check" }).json()
            if res.get("status") == "success":
                st.session_state["cached_res"] = res
                st.session_state["last_scanned_jan"] = jan_code
            else:
                st.error(f"⚠️ {res.get('message')}")
        except Exception as e:
            st.error(f"データ自動取得エラー: {e}")

if st.session_state["cached_res"] and jan_code == st.session_state["last_scanned_jan"]:
    st.info(f"📦 **現在の対象アイテム**: {st.session_state['cached_res'].get('itemName')}")
    display_stock_only(st.session_state["cached_res"], title="🔍 登録前のリアルタイム現在状況（先読み）")

count_val = create_secure_drum("➕ 登録数量を選択（スクロール）", counts_reg, "v_count_reg", 0)

if st.button("🎰 上記の内容で通常加算登録をする", key="btn_register"):
    if not jan_code:
        st.warning("⚠️ JANコードをスキャンしてください。")
    else:
        with st.spinner("スプレッドシートを更新中..."):
            try:
                res = requests.post(GAS_URL, json={ "janCode": jan_code, "status": status, "count": int(count_val), "user": user_name, "action": "register" }).json()
                if res.get("status") == "success":
                    st.success(f"⭕ {status} への工程移動が通常完了しました！")
                    st.session_state["cached_res"] = res
                    display_stock_only(res, title="📊 登録完了後の最新在庫状況")
                elif res.get("status") == "qty_mismatch":
                    st.session_state["mismatch_detected"] = True
                    st.session_state["prev_details"] = res["details"]
                    st.session_state["original_payload"] = { "janCode": jan_code, "status": status, "count": int(count_val), "user": user_name, "action": "register" }
                    st.rerun()
            except Exception as e:
                st.error(f"通信エラー: {e}")

if st.session_state.get("mismatch_detected", False):
    d = st.session_state["prev_details"]
    st.error(f"⚠️ 前工程【{d['prevStatus']}】にあった数（{d['prevCount']}個）と合計が合いません。")
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
                    st.success("⭕ スキップ移動が完了しました！")
                    st.session_state["mismatch_detected"] = False
                    st.session_state["cached_res"] = res
                    display_stock_only(res, title="📊 最新在庫状況")
            except Exception as e:
                st.error(f"再送信エラー: {e}")

st.markdown("---")

# =========================================================
# 🔍 2. 現在の在庫状況確認・直接修正
# =========================================================
st.subheader("🔍 2. 現在の在庫状況確認・直接修正")
status_modify = create_secure_drum("📝 直接修正したい工程を選択（スクロール）", processes, "v_status_modify", 0)
jan_code_modify = st.text_input("📋 在庫を確認・修正するバーコード（JAN）をスキャン：", key="jan_modify_input")

if jan_code_modify:
    with st.spinner("データ取得中..."):
        try:
            res = requests.post(GAS_URL, json={ "janCode": jan_code_modify, "action": "check" }).json()
            if res.get("status") == "success":
                st.info(f"📦 **現在の登録アイテム**: {res.get('itemName')}")
                display_stock_only(res, title="🔍 修正前のリアルタイム在庫状況")
        except Exception as e:
            st.error(f"エラー: {e}")

count_modify = create_secure_drum("📝 上書き修正する数量を選択（スクロール）", counts_modify, "v_count_modify", 0)

if st.button("数値を直接上書き修正（修正・削除用）", key="btn_modify"):
    if not jan_code_modify:
        st.warning("⚠️ JANコードをスキャンしてください。")
    else:
        with st.spinner("修正中..."):
            try:
                res = requests.post(GAS_URL, json={ "janCode": jan_code_modify, "status": status_modify, "count": int(count_modify), "user": user_name, "action": "modify" }).json()
                if res.get("status") == "success":
                    st.success("⭕ 上書き修正が完了しました！")
                    display_stock_only(res, "📊 修正反映後の在庫状況")
            except Exception as e:
                st.error(f"通信エラー: {e}")

st.markdown("---")

# =========================================================
# 📋 3. 生産ライン上の各工程合計数（★関数独立型・エラー絶対ゼロ仕様）
# =========================================================
st.subheader("📋 3. 生産ライン上の各工程合計数")
st.write("ボタンを押すと、工場全データ（1万行）の各工程ごとの縦一列の純粋な合計値をリアルタイム集計します。")

if st.button("📊 工場全体の各工程合計数を集計する", key="btn_check_total"):
    with st.spinner("一括集計中..."):
        try:
            r_total = requests.post(GAS_URL, json={"action": "check_total"}).json()
            if r_total.get("status") == "success":
                t = r_total.get("grandTotalData", {})
                st.success("📊 集計が完了しました！")
                st.write(f"・棹カット 合計: **{t.get('katto', 0)}** 個 | ・枠組み 合計: **{t.get('waku', 0)}** 個")
                st.write(f"・スペーサー 合計: **{t.get('spacer', 0)}** 個 | ・中身セット 合計: **{t.get('nakami', 0)}** 個")
                st.write(f"・金具打ち 合計: **{t.get('kanagu', 0)}** 個 | ・仕上げ 合計: **{t.get('shiage', 0)}** 個")
                st.write(f"・完成 合計: **{t.get('kanryo', 0)}** 個")
                st.markdown("---")
                st.write(f"🏭 **各工程合計数(A)**: **{t.get('totalA', 0)}** 個")
                st.write(f"📦 **生産課管理棚合計数(B)**: **{t.get('totalB', 0)}** 個")
                st.write(f"🧱 **総合計(A+B)**: **{t.get('totalAB', 0)}** 個")
            else:
                st.error(f"エラー: {r_total.get('message')}")
        except Exception as e:
            st.error(f"集計通信エラー: {e}")
