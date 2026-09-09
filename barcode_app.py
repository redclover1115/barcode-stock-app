import streamlit as st
import streamlit.components.v1 as components
import requests
import json

st.title("🎰 工程在庫管理スロットアプリ")
st.write("7工程ジャンプ完全対応・新世代ドラムスロットUIモデル")

# 1. 共通GAS URL
GAS_URL = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec"

# リストの定義
users = ["吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"]
processes = ["棹カット", "枠組み", "スペーサー加工", "中身セット", "金具打ち", "仕上げ", "完成"]
counts_reg = [str(i) for i in range(1, 101)]     # 1〜100
counts_modify = [str(i) for i in range(0, 501)]  # 0〜500
counts_reason = [str(i) for i in range(0, 101)]  # 0〜100

# --- 🎰 超スムーズ＆絶対ズレない新世代ドラムスロットUI生成関数 ---
def create_smooth_slot(label, options, key, default_idx=0):
    st.write(f"**{label}**")
    options_json = json.dumps(options, ensure_ascii=False)
    
    if key not in st.session_state:
        st.session_state[key] = options[default_idx]
        
    # CSSのScroll Snapを使用し、スマホ本来の超滑らかな「くるくる回転＆ピタッと吸着」を実現
    html_code = f"""
    <div style="display:flex; justify-content:center; padding:2px 0; user-select:none; -webkit-user-select:none;">
        <div style="position:relative; width:90%; height:120px; overflow:hidden; border:2px solid #a6a6a6; border-radius:14px; background:linear-gradient(to bottom, #d9d9d9, #fff 25%, #fff 75%, #d9d9d9); box-shadow:inset 0 0 12px rgba(0,0,0,0.15);">
            <!-- 赤い中心判定線 -->
            <div style="position:absolute; top:42px; width:100%; height:36px; border-top:2px solid #ff4b4b; border-bottom:2px solid #ff4b4b; background:rgba(255,75,75,0.03); pointer-events:none; z-index:10;"></div>
            
            <!-- スムーズにくるくる回る独立ドラム -->
            <div id="drum-{key}" style="height:120px; overflow-y:scroll; scroll-snap-type: y mandatory; scroll-behavior: smooth; -webkit-overflow-scrolling: touch; padding-top:42px; padding-bottom:42px; box-sizing:border-box;">
                <div style="height:1px;"></div>
            </div>
        </div>
    </div>
    <style>
        /* スクロールバーを非表示にしてスロット感を出す */
        #drum-{key}::-webkit-scrollbar {{ display: none; }}
        #drum-{key} {{ -ms-overflow-style: none; scrollbar-width: none; }}
    </style>
    <script>
        const list = {options_json};
        const drum = document.getElementById("drum-{key}");
        
        // ドラムの要素（子アイテム）を生成
        list.forEach((item) => {{
            const el = document.createElement("div");
            el.style.height = "36px";
            el.style.lineHeight = "36px";
            el.style.fontSize = "18px";
            el.style.fontWeight = "bold";
            el.style.textAlign = "center";
            el.style.color = "#111";
            el.style.scrollSnapAlign = "center"; // 中心にピタッと吸い付かせる設定
            el.innerText = item;
            drum.appendChild(el);
        }});
        
        // 初期位置の設定
        drum.scrollTop = {default_idx} * 36;
        
        // 回転が止まったらStreamlitへ数値を100%確実に引き渡すイベント
        let timeout = null;
        drum.addEventListener('scroll', () => {{
            clearTimeout(timeout);
            timeout = setTimeout(() => {{
                let index = Math.round(drum.scrollTop / 36);
                if(index < 0) index = 0;
                if(index >= list.length) index = list.length - 1;
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: list[index], key: '{key}'}}, '*');
            }}, 80); // 止まってから80ミリ秒で確定
        }});
    </script>
    """
    components.html(html_code, height=135)
    
def display_stock_and_total(res_data, title="📊 現在の在庫状況"):
    st.write(f"### {title}")
    s = res_data.get("stockData", {})
    t = res_data.get("grandTotalData", {})
    
    st.write("**◆ 今回のアイテムの工程内訳**")
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("棹カット", f"{s.get('katto',0)}個")
    c2.metric("枠組み", f"{s.get('wakugumi',0)}個")
    c3.metric("スペーサー", f"{s.get('spacer',0)}個")
    c4.metric("中身セット", f"{s.get('nakami',0)}個")
    c5.metric("金具打ち", f"{s.get('kanagu',0)}個")
    c6.metric("仕上げ", f"{s.get('shiage',0)}個")
    c7.metric("完成", f"{s.get('kanryo',0)}個")
    
    st.write("**◆ 工場全体の総合計（7工程合計）**")
    col = st.columns(8)
    col.metric("棹カット計", f"{t.get('katto',0)}個")
    col.metric("枠組み計", f"{t.get('waku',0)}個")
    col.metric("スペーサー計", f"{t.get('spacer',0)}個")
    col.metric("中身計", f"{t.get('nakami',0)}個")
    col.metric("金具計", f"{t.get('kanagu',0)}個")
    col.metric("仕上げ計", f"{t.get('shiage',0)}個")
    col.metric("完成計", f"{t.get('kanryo',0)}個")
    col.metric("🧱 総合計", f"{t.get('grandTotal',0)}個")

# メイン画面構築：担当者選択スロット
create_smooth_slot("👤 担当者選択スロット", users, "v_user", 0)

st.markdown("---")

# =========================================================
# 📥 1. 通常の数量加算（新規登録）
# =========================================================
st.subheader("📥 1. 通常の数量加算（新規登録）")

create_smooth_slot("🚩 移動先の工程スロット", processes, "v_status_reg", 0)
jan_code = st.text_input("📋 加算するバーコード（JAN）をスキャン：", key="jan_reg_input")
create_smooth_slot("➕ 登録数量スロット", counts_reg, "v_count_reg", 0) # 初期値は1個(index 0)

if st.button("🎰 上記の内容で通常加算登録をする", key="btn_register"):
    user_name = st.session_state.get("v_user", "未選択")
    status = st.session_state.get("v_status_reg", "棹カット")
    count_val = int(st.session_state.get("v_count_reg", "1")) # 新UIにより完璧に連動します
    
    if not jan_code:
        st.warning("⚠️ JANコードをスキャンしてください。")
    else:
        payload = { "janCode": jan_code, "status": status, "count": count_val, "user": user_name, "action": "register" }
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
                else:
                    st.error(f"エラー: {res.get('message')}")
            except Exception as e:
                st.error(f"通信エラー: {e}")

# 🚨 数量不一致エラー時のマイナス内訳
if st.session_state.get("mismatch_detected", False):
    d = st.session_state["prev_details"]
    st.error(f"⚠️ 前工程【{d['prevStatus']}】にあった数（{d['prevCount']}個）と、今回移動する数（{d['inputCount']}個）が合いません。")
    st.info("残りの差分について、出荷・不良・その他の内訳スロットを回して合計を合わせてください。")
    
    create_smooth_slot("📉 1. 出荷された数", counts_reason, "v_shikka", 0)
    create_smooth_slot("📉 2. 不良の数", counts_reason, "v_furyo", 0)
    create_smooth_slot("📉 3. その他の数", counts_reason, "v_sonota", 0)
    
    if st.button("内訳を確定して再送信"):
        shikka = int(st.session_state.get("v_shikka", "0"))
        furyo = int(st.session_state.get("v_furyo", "0"))
        sonota = int(st.session_state.get("v_sonota", "0"))
        
        if (d['inputCount'] + shikka + furyo + sonota) == d['prevCount']:
            retry = st.session_state["original_payload"]
            retry.update({ "forceHeader": True, "countShikka": shikka, "countFuryo": furyo, "countSonota": sonota })
            res = requests.post(GAS_URL, json=retry).json()
            if res.get("status") == "success":
                st.success("⭕ 理由内訳を確認し、前工程をクリアして移動しました！")
                st.session_state["mismatch_detected"] = False
                display_stock_and_total(res)
        else:
            st.warning("❌ 内訳の合計が前工程の残数と一致しません。スロットを合わせ直してください。")

st.markdown("---")

# =========================================================
# 🔍 2. 現在の在庫状況確認・直接修正
# =========================================================
st.subheader("🔍 2. 現在の在庫状況確認・直接修正")

create_smooth_slot("📝 直接修正したい工程スロット", processes, "v_status_modify", 0)
jan_code_modify = st.text_input("📋 在庫を確認・修正するバーコード（JAN）をスキャン：", key="jan_modify_input")
create_smooth_slot("📝 上書き修正する数量スロット", counts_modify, "v_count_modify", 0)

if st.button("数値を直接上書き修正（修正・削除用）", key="btn_modify"):
    user_name = st.session_state.get("v_user", "未選択")
    status_modify = st.session_state.get("v_status_modify", "棹カット")
    count_modify = int(st.session_state.get("v_count_modify", "0"))
    
    if not jan_code_modify:
        st.warning("⚠️ JANコードをスキャンしてください。")
    else:
        payload_modify = { "janCode": jan_code_modify, "status": status_modify, "count": count_modify, "user": user_name, "action": "modify" }
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
