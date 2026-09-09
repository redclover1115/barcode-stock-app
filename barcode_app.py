import streamlit as st
import streamlit.components.v1 as components
import requests
import json

st.title("🎰 工程在庫管理スロットアプリ")
st.write("7工程ジャンプ完全対応・独立型3DくるくるスロットUIモデル")

# 1. 共通GAS URL
GAS_URL = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec"

# リストの定義
users = ["吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"]
processes = ["棹カット", "枠組み", "スペーサー加工", "中身セット", "金具打ち", "仕上げ", "完成"]
counts = [str(i) for i in range(0, 501)] # 直接修正を見据えて500まで拡張

# --- 🚀 画面を巻き込まない・独立3DくるくるスロットUI生成関数 ---
def create_slot_picker(label, options, key, default_idx=0):
    st.write(f"**{label}**")
    options_json = json.dumps(options, ensure_ascii=False)
    
    # セッションの初期化
    if key not in st.session_state:
        st.session_state[key] = options[default_idx]
        
    # 【改良】親画面のスクロールを100%防止（touch-action: none と preventDefault の併用）
    html_code = f"""
    <div style="display:flex; justify-content:center; padding:5px 0; user-select:none; -webkit-user-select:none;">
        <div id="wrapper-{key}" style="position:relative; width:85%; height:110px; overflow:hidden; border:2px solid #b3b3b3; border-radius:12px; background:linear-gradient(to bottom, #e6e6e6, #fff 20%, #fff 80%, #e6e6e6); box-shadow:inset 0 0 15px rgba(0,0,0,0.15); touch-action:none;">
            <div style="position:absolute; top:40px; width:100%; height:30px; border-top:2px solid #ff4b4b; border-bottom:2px solid #ff4b4b; background:rgba(255,75,75,0.04); pointer-events:none; z-index:10;"></div>
            <div id="scroll-wheel-{key}" style="display:flex; flex-direction:column; align-items:center; transition: transform 0.15s ease-out; cursor:grab; padding-top:40px; touch-action:none;">
            </div>
        </div>
    </div>
    <script>
        const list = {options_json};
        const container = document.getElementById("scroll-wheel-{key}");
        const wrapper = document.getElementById("wrapper-{key}");
        
        // 要素生成
        list.forEach((item) => {{
            const div = document.createElement("div");
            div.style.height = "30px";
            div.style.lineHeight = "30px";
            div.style.fontSize = "16px";
            div.style.fontWeight = "bold";
            div.style.color = "#222";
            div.innerText = item;
            container.appendChild(div);
        }});
        
        let activeIdx = {default_idx};
        
        function updateTransform() {{
            container.style.transform = `translateY(${{-activeIdx * 30}}px)`;
            window.parent.postMessage({{type: 'streamlit:setComponentValue', value: list[activeIdx], key: '{key}'}}, '*');
        }}
        updateTransform();
        
        let isDragging = false; let startY = 0;
        
        // マウスドラッグ
        wrapper.addEventListener('mousedown', (e) => {{ isDragging = true; startY = e.clientY; e.preventDefault(); }});
        window.addEventListener('mousemove', (e) => {{
            if(!isDragging) return;
            let diff = e.clientY - startY;
            if(Math.abs(diff) > 10) {{
                if(diff > 0 && activeIdx > 0) {{ activeIdx--; startY = e.clientY; }}
                if(diff < 0 && activeIdx < list.length - 1) {{ activeIdx++; startY = e.clientY; }}
                updateTransform();
            }}
        }});
        window.addEventListener('mouseup', () => isDragging = false);
        
        // 【最重要】スマホスワイプ時にアプリ全体の上下スクロールを完全に殺す（独立回転）
        wrapper.addEventListener('touchstart', (e) => {{ 
            startY = e.touches[0].clientY; 
            isDragging = true;
        }}, {{passive: false}});
        
        wrapper.addEventListener('touchmove', (e) => {{
            if(!isDragging) return;
            // 画面全体のスクロールを強制ブロック
            if (e.cancelable) e.preventDefault(); 
            
            let diff = e.touches[0].clientY - startY;
            if(Math.abs(diff) > 8) {{
                if(diff > 0 && activeIdx > 0) {{ activeIdx--; startY = e.touches[0].clientY; }}
                if(diff < 0 && activeIdx < list.length - 1) {{ activeIdx++; startY = e.touches[0].clientY; }}
                updateTransform();
            }}
        }}, {{passive: false}});
        
        wrapper.addEventListener('touchend', () => {{ isDragging = false; }});
    </script>
    """
    components.html(html_code, height=125)
    
# 📊 日本語カード形式での共通在庫表示関数
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


# 固定の最上部共通配置：担当者選択スロット
create_slot_picker("👤 担当者選択スロット", users, "v_user", 0)
user_name = st.session_state.get("v_user", users[0])

st.markdown("---")

# =========================================================
# 📥 1. 通常の数量加算（新規登録）
# =========================================================
st.subheader("📥 1. 通常の数量加算（新規登録）")

create_slot_picker("🚩 移動先の工程スロット", processes, "v_status", 0)
jan_code = st.text_input("📋 加算するバーコード（JAN）をスキャン：", key="jan_reg_input")
create_slot_picker("➕ 登録数量スロット", counts[1:101], "v_count", 0) # 1〜100

status = st.session_state.get("v_status", processes[0])
count = int(st.session_state.get("v_count", "1"))

if st.button("🎰 上記の内容で通常加算登録をする", key="btn_register"):
    if not jan_code:
        st.warning("⚠️ JANコードをスキャンしてください。")
    else:
        payload = { "janCode": jan_code, "status": status, "count": count, "user": user_name, "action": "register" }
        st.session_state["mismatch_detected"] = False
        with st.spinner("通信中..."):
            try:
                res = requests.post(GAS_URL, json=payload).json()
                if res.get("status") == "success":
                    st.success(f"⭕ {status} への工程移動が通常完了しました！【{res.get('itemName')}】")
                    display_stock_and_total(res)
                elif res.get("status") == "qty_mismatch":
                    st.session_state["mismatch_detected"] = True
                    st.session_state["prev_details"] = res["details"]
                    st.session_state["original_payload"] = payload
                    st.session_state["item_name_temp"] = res.get("itemName")
            except Exception as e:
                st.error(f"通信エラー: {e}")

# 🚨 数量不一致エラー時のマイナス内訳
if st.session_state.get("mismatch_detected", False):
    d = st.session_state["prev_details"]
    st.error(f"⚠️ 前工程【{d['prevStatus']}】にあった数（{d['prevCount']}個）と、今回移動する数（{d['inputCount']}個）が合いません。")
    st.info("残りの差分について、出荷・不良・その他の内訳スロットを回して合計を合わせてください。")
    
    create_slot_picker("📉 1. 出荷された数", counts[0:101], "v_shikka", 0)
    create_slot_picker("📉 2. 不良の数", counts[0:101], "v_furyo", 0)
    create_slot_picker("📉 3. その他の数", counts[0:101], "v_sonota", 0)
    
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
# 🔍 2. 現在の在庫状況確認・直接修正（復活）
# =========================================================
st.subheader("🔍 2. 現在の在庫状況確認・直接修正")

create_slot_picker("📝 直接修正したい工程スロット", processes, "v_status_modify", 0)
jan_code_modify = st.text_input("📋 在庫を確認・修正するバーコード（JAN）をスキャン：", key="jan_modify_input")
create_slot_picker("📝 上書き修正する数量スロット", counts[0:501], "v_count_modify", 0) # 0〜500

status_modify = st.session_state.get("v_status_modify", processes[0])
count_modify = int(st.session_state.get("v_count_modify", "0"))

if st.button("数値を直接上書き修正（修正・削除用）", key="btn_modify"):
    if not jan_code_modify:
        st.warning("⚠️ JANコードをスキャンしてください。")
    else:
        payload_modify = { "janCode": jan_code_modify, "status": status_modify, "count": count_modify, "user": user_name, "action": "modify" }
        with st.spinner("スプレッドシートの数値を直接上書き中..."):
            try:
                res = requests.post(GAS_URL, json=payload_modify).json()
                if res.get("status") == "success":
                    st.success(f"⭕ 上書き修正が完了しました！【{res.get('itemName')}】")
                    display_stock_and_total(res, "📊 最新の在庫・合計状況")
                else:
                    st.error(f"エラー: {res.get('message')}")
            except Exception as e:
                st.error(f"通信エラー: {e}")

st.markdown("---")

# =========================================================
# 📋 3. 単品コードでの現在在庫確認（復活）
