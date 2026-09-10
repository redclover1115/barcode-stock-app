import streamlit as st
import requests

st.title("🎰 工程在庫管理スロットアプリ")
st.write("7工程ジャンプ完全対応・高速サクサク軽量化モデル")

GAS_URL = "https://script.google.com/macros/s/AKfycbwNTMZAQ5edee04wb3zMtWPnMqjN8guEJQCG-zYOBQdvpyxvc7K5VoRmGiO6bZxImJy/exec"

users = ["吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"]
processes = ["棹カット", "枠組み", "スペーサー加工", "中身セット", "金具打ち", "仕上げ", "完成", "出庫"]
counts_reg = [i for i in range(1, 101)]
counts_modify = [i for i in range(0, 501)]
counts_reason = [i for i in range(0, 101)]

# セッション状態の初期化
if "last_scanned_jan" not in st.session_state:
    st.session_state["last_scanned_jan"] = ""
if "cached_res" not in st.session_state:
    st.session_state["cached_res"] = None
if "current_item_name" not in st.session_state:
    st.session_state["current_item_name"] = ""

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
    st.write(f"💡 受注生産品完成在庫 (V列): **{res_data.get('mikomiStock', '0')}** 個  /  🚚 出庫数累計 (X列): **{s.get('shukko',0)}** 個")

# ーーー ① 通常の登録用メイン3連ドラム ーーー
col_user, col_proc, col_cnt = st.columns(3)
with col_user:
    selected_user = create_secure_drum("① 作業者名を選択", users, "user_select_main")
with col_proc:
    selected_proc = create_secure_drum("② 移動先の工程を選択", processes, "proc_select_main")
with col_cnt:
    selected_count = create_secure_drum("③ 数量を選択", counts_reg, "count_select_main", default_idx=0)

st.markdown("### 📦 バーコードスキャン位置")

# スキャナー連動フォーム（確定ボタンなしでEnter自動送信）
with st.form(key="scan_form", clear_on_submit=True):
    jan_input = st.text_input("スキャナーのカーソルをここに合わせてスキャンしてください（読み込むと自動送信されます）", value="")
    st.form_submit_button(label="送信", disabled=True, type="primary")

# スキャナーが読み込んだ瞬間に実行
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
            st.session_state["cached_res"] = res_data
            st.session_state["last_scanned_jan"] = jan_input
            st.session_state["current_item_name"] = res_data.get("itemName", "商品名未設定")
        elif res_data.get("status") == "qty_mismatch":
            st.warning(f"警告: {res_data.get('message')}")
        else:
            st.error(f"エラー: {res_data.get('message')}")
    except Exception as e:
        st.error(f"通信失敗: {e}")

# ーーー 💡 【ご要望①】JANを読み込んだ時点で即座に商品名が最優先で出るボックス ーーー
if st.session_state["current_item_name"]:
    st.markdown(
        f"""
        <div style="background-color: #eaf2ff; padding: 15px; border-left: 5px solid #2b6cb0; border-radius: 4px; margin-top: 10px; margin-bottom: 10px;">
            <p style="margin: 0; font-size: 14px; color: #4a5568; font-weight: bold;">🔍 読み込み中のアイテム（JAN: {st.session_state['last_scanned_jan']}）</p>
            <h2 style="margin: 5px 0 0 0; color: #2b6cb0; font-weight: bold;">{st.session_state['current_item_name']}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

# ーーー 💡 【ご要望②】「在庫状況を表示」ボタンに名称変更 ーーー
if st.button("📊 在庫状況を表示（最新データに更新）", key="btn_show_and_reload_stock"):
    if st.session_state["last_scanned_jan"]:
        try:
            res = requests.post(GAS_URL, json={"janCode": st.session_state["last_scanned_jan"], "action": "check"})
            res_data = res.json()
            if res_data.get("status") == "success":
                st.session_state["cached_res"] = res_data
                st.session_state["current_item_name"] = res_data.get("itemName", "商品名未設定")
                st.success("最新の在庫状況を表示しました。")
        except Exception as e:
            st.error(f"在庫状況の取得に失敗しました: {e}")
    else:
        st.warning("まだバーコードがスキャンされていません。先に上の入力位置でスキャンを行ってください。")

# ボタン押下時、またはキャッシュ保持時にメーターを表示
if st.session_state["cached_res"]:
    display_stock_only(st.session_state["cached_res"])

# =========================================================
# ⚙️ ２．手動数量修正エリア
# =========================================================
st.markdown("---")
st.markdown("### 🔧 ２．手動での在庫数量修正・変更")

col_reason, col_modify = st.columns(2)
with col_reason:
    selected_reason = create_secure_drum("移動修正理由を選択 (予備カウント)", counts_reason, "reason_modify_select")
with col_modify:
    selected_modify_count = create_secure_drum("修正後の数量を選択 (0〜500)", counts_modify, "count_modify_select", default_idx=0)

if st.button("🚨 選択中の工程の数量をこの値に上書き修正する", key="execute_modify_action_btn"):
    if not st.session_state["last_scanned_jan"]:
        st.error("先に上の欄でバーコードをスキャンして、対象の商品を特定してください。")
    else:
        payload = {
            "janCode": st.session_state["last_scanned_jan"],
            "status": selected_proc, 
            "count": selected_modify_count,
            "user": selected_user,
            "action": "modify"
        }
        try:
            res = requests.post(GAS_URL, json=payload)
            res_data = res.json()
            if res_data.get("status") == "success":
                st.success(f"修正成功: 【{res_data.get('itemName')}】の「{selected_proc}」の在庫数を {selected_modify_count} 個に変更しました。")
                st.session_state["cached_res"] = res_data
                st.session_state["current_item_name"] = res_data.get("itemName", "商品名未設定")
        except Exception as e:
            st.error(f"通信失敗: {e}")

# =========================================================
# 📊 ３．全工程の合計値算出（全体集計）
# =========================================================
st.markdown("---")
st.markdown("### 📊 ３．全工程の合計値算出（全体集計）")

if st.button("📈 全商品の在庫合計値を集計して算出する", key="calculate_grand_total_btn"):
    try:
        with st.spinner("スプレッドシート全体のデータを集計中..."):
            res = requests.post(GAS_URL, json={"action": "check_total"})
            res_data = res.json()
            
            if res_data.get("status") == "success" and res_data.get("grandTotalData"):
                g = res_data["grandTotalData"]
                st.markdown("#### 🧮 算出された各工程の現在合計数")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("棹カット 合計", f"{g.get('katto', 0)} 個")
                m2.metric("枠組み 合計", f"{g.get('waku', 0)} 個")
                m3.metric("スペーサー 合計", f"{g.get('spacer', 0)} 個")
                m4.metric("中身セット 合計", f"{g.get('nakami', 0)} 個")
                
                m5, m6, m7, m8 = st.columns(4)
                m5.metric("金具打ち 合計", f"{g.get('kanagu', 0)} 個")
                m6.metric("仕上げ 合計", f"{g.get('shiage', 0)} 個")
                m7.metric("完成(S列) 合計", f"{g.get('kanryo', 0)} 個")
                m8.metric("管理棚総数", f"{res_data.get('seisanTanaZaiko', 0)} 個")
                
                st.success("全体の集計算出が完了しました！")
            else:
                st.error("GAS側からの集計データの取得に失敗しました。")
    except Exception as e:
        st.error(f"合計値の算出通信に失敗しました: {e}")
