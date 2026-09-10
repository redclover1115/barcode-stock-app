import streamlit as st
import requests

st.title("🎰 工程在庫管理スロットアプリ")
st.write("7工程ジャンプ完全対応・高速サクサク軽量化モデル")

GAS_URL = "https://script.google.com/macros/s/AKfycbwNTMZAQ5edee04wb3zMtWPnMqjN8guEJQCG-zYOBQdvpyxvc7K5VoRmGiO6bZxImJy/exec"

users = ["吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"]
# 「出庫」を工程の選択肢に正式追加
processes = ["棹カット", "枠組み", "スペーサー加工", "中身セット", "金具打ち", "仕上げ", "完成", "出庫"]
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
    # 下部に追加の数字情報をシンプルに一行で添える
    st.write(f"💡 受注生産品完成在庫 (V列): **{res_data.get('mikomiStock', '0')}** 個  /  🚚 出庫数累計 (X列): **{s.get('shukko',0)}** 個")

# ーーー 画面上部のメイン3連ドラム ーーー
col_user, col_proc, col_cnt = st.columns(3)
with col_user:
    selected_user = create_secure_drum("① 作業者名を選択", users, "user_select_main")
with col_proc:
    selected_proc = create_secure_drum("② 移動先の工程を選択", processes, "proc_select_main")
with col_cnt:
    selected_count = create_secure_drum("③ 数量を選択", counts_reg, "count_select_main", default_idx=0)

st.markdown("### 📦 バーコードスキャン位置")
jan_input = st.text_input("スキャナーのカーソルをここに合わせてスキャンしてください", key="jan_scan_main")

# バーコードスキャン時の送信処理
if jan_input:
    payload = {
        "janCode": jan_input,
        "status": selected_proc,
        "count": selected_count,
        "user": selected_user,
        "action": "register"
    }
    try:
        res = requests.post(GAS_URL, json=payload)
        res_data = res.json()
        if res_data.get("status") == "success":
            st.success(f"処理成功: 【{res_data.get('itemName')}】を処理しました。")
            st.session_state["cached_res"] = res_data
            st.session_state["last_scanned_jan"] = jan_input
        elif res_data.get("status") == "qty_mismatch":
            st.warning(f"警告: {res_data.get('message')}")
        else:
            st.error(f"エラー: {res_data.get('message')}")
    except Exception as e:
        st.error(f"通信失敗: {e}")
    st.rerun()

# ーーー 💡 【ここから復元】最初のコードの続き（ st.wri 以降の全プログラム） ーーー
if st.session_state["cached_res"]:
    display_stock_only(st.session_state["cached_res"])

# アプリの下部に配置されていた、補助ボタンや集計エリア
st.markdown("### 🔍 各種機能")
c_btn1, c_btn2 = st.columns(2)

with c_btn1:
    if st.button("📊 全体在庫の集計を確認する", key="btn_check_total"):
        try:
            res = requests.post(GAS_URL, json={"action": "check_total"})
            res_data = res.json()
            if res_data.get("status") == "success" and res_data.get("grandTotalData"):
                g = res_data["grandTotalData"]
                st.write("### 📈 全体集計データ")
                st.write(f"- 棹カット総数: {g.get('katto', 0)} 個")
                st.write(f"- 枠組み総数: {g.get('waku', 0)} 個")
                st.write(f"- スペーサー総数: {g.get('spacer', 0)} 個")
                st.write(f"- 中身セット総数: {g.get('nakami', 0)} 個")
                st.write(f"- 金具打ち総数: {g.get('kanagu', 0)} 個")
                st.write(f"- 仕上げ総数: {g.get('shiage', 0)} 個")
                st.write(f"- 完成総数: {g.get('kanryo', 0)} 個")
            else:
                st.error("集計データの取得に失敗しました。")
        except Exception as e:
            st.error(f"通信失敗: {e}")

with c_btn2:
    if st.button("🔄 直近のスキャンデータを再読込", key="btn_reload_last"):
        if st.session_state["last_scanned_jan"]:
            try:
                res = requests.post(GAS_URL, json={"janCode": st.session_state["last_scanned_jan"], "action": "check"})
                res_data = res.json()
                if res_data.get("status") == "success":
                    st.session_state["cached_res"] = res_data
                    st.rerun()
            except Exception as e:
                st.error(f"再読込失敗: {e}")
        else:
            st.warning("まだバーコードがスキャンされていません。")
