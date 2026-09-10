import streamlit as st
import requests

# 画面をワイドモードに設定（横並びの数字を見やすくするため）
st.set_page_config(layout="wide")

st.title("🎰 工程在庫管理スロットアプリ")
st.write("7工程ジャンプ完全対応・高速サクサク軽量化モデル（出庫＆2列同時減算対応）")

# ⚠️ ご自身の新しいGASデプロイURLに書き換えてください
GAS_URL = "https://script.google.com/macros/s/AKfycbwNTMZAQ5edee04wb3zMtWPnMqjN8guEJQCG-zYOBQdvpyxvc7K5VoRmGiO6bZxImJy/exec"

# 選択肢データの定義（「出庫」を正式追加）
users = ["吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"]
processes = ["棹カット", "枠組み", "スペーサー加工", "中身セット", "金具打ち", "仕上げ", "完成", "出庫"]
counts_reg = [i for i in range(1, 101)]

# セッション状態（一時保存データ）の初期化
if "last_scanned_jan" not in st.session_state:
    st.session_state["last_scanned_jan"] = ""
if "cached_res" not in st.session_state:
    st.session_state["cached_res"] = None

# カスタムドラムUIコンポーネント（見た目をスマートに調整）
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

# 在庫状況を画面にメトリック表示する関数
def display_stock_only(res_data, title="📊 現在の在庫状況"):
    st.write(f"#### {title}")
    s = res_data.get("stockData", {})
    st.write("**◆ 今回のスキャンアイテムの工程内訳**")
    
    # 8つの列を作って各工程の在庫数を横並びで表示
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
    c1.metric("棹カット", f"{s.get('katto',0)}個")
    c2.metric("枠組み", f"{s.get('wakugumi',0)}個")
    c3.metric("スペーサー", f"{s.get('spacer',0)}個")
    c4.metric("中身セット", f"{s.get('nakami',0)}個")
    c5.metric("金具打ち", f"{s.get('kanagu',0)}個")
    c6.metric("仕上げ", f"{s.get('shiage',0)}個")
    c7.metric("完成 (S列)", f"{s.get('kanryo',0)}個")
    c8.metric("出庫ログ数", f"{s.get('shukko',0)}個")
    
    st.markdown("---")
    
    # 連動して引かれるV列の在庫数を強調表示
    st.info(f"💡 **受注生産品完成在庫 (V列): {res_data.get('mikomiStock', '0')} 個**")

# ==========================================
# 3. アプリメイン画面レイアウト
# ==========================================
col_user, col_proc, col_cnt = st.columns(3)

with col_user:
    selected_user = create_secure_drum("① 作業者名を選択", users, "user_select")
with col_proc:
    selected_proc = create_secure_drum("② 移動先の工程を選択", processes, "proc_select")
with col_cnt:
    selected_count = create_secure_drum("③ 数量を選択", counts_reg, "count_select", default_idx=0)

st.markdown("### 📦 バーコードスキャン位置")
# ハンディスキャナーから連続でアップロードできるように入力欄をクリアする仕組み
jan_input = st.text_input("スキャナーのカーソルをここに合わせてスキャンしてください", key="jan_barcode")

# JANコードが入力された（またはスキャナーから送信された）時の処理
if jan_input:
    payload = {
        "janCode": jan_input,
        "status": selected_proc,
        "count": selected_count,
        "user": selected_user,
        "action": "register"
    }
    
    try:
        with st.spinner("スプレッドシートを更新中..."):
            res = requests.post(GAS_URL, json=payload)
            res_data = res.json()
            
            if res_data.get("status") == "success":
                if selected_proc == "出庫":
                    st.success(f"🚚 出庫完了: 【{res_data.get('itemName')}】を {selected_count} 個出庫しました。（完成S列・受注V列から差し引きました）")
                else:
                    st.success(f"✅ 登録完了: 【{res_data.get('itemName')}】を「{selected_proc}」に {selected_count} 個登録しました。")
                
                # キャッシュを更新して画面下の表示を変える
                st.session_state["cached_res"] = res_data
                st.session_state["last_scanned_jan"] = jan_input
            elif res_data.get("status") == "qty_mismatch":
                st.warning(f"⚠️ 警告: {res_data.get('message')}")
                st.write(res_data.get("details"))
            else:
                st.error(f"❌ エラーが発生しました: {res_data.get('message')}")
    except Exception as e:
        st.error(f"📡 GASへの通信に失敗しました: {e}")
    
    # 連続スキャンのため、テキストボックスの値を消去して画面を強制リロード（再起動）
    st.session_state["jan_barcode"] = ""
    st.rerun()

# スキャン直後、または過去のスキャン結果が残っている場合に画面下部に在庫数を表示
if st.session_state["cached_res"]:
    display_stock_only(st.session_state["cached_res"])
