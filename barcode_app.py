# バーコード在庫登録システム 引き継ぎ情報（列の自動追従・エラー修正版）

スプレッドシートの列の並び替え（実際の工程順への変更）に対応し、かつ全角文字によるエラーを完全に除去した最新の完全版コードです。
このプログラムは、スプレッドシートの4行目の見出し名（「縦カット」「スペーサー加工」など）を自動で検索するため、今後スプレッドシート側で列を左右に自由に並び替えても絶対にデータがズレたり壊れたりしません。

## 💻 1. GitHub用：最新完全版コード (`barcode_app.py`)
※11行目の `gas_url` に本物のGASのURLを入れて使用します。

```python
import streamlit as st
import requests
import time

st.set_page_config(page_title="生産現場用 バーコード在庫登録システム", layout="centered")

st.title("🏭 生産現場用 バーコード在庫登録システム")
st.write("新レイアウト対応版（工程名自動検索・常時在庫表示・全体総合計仕様）")

# ★吉本さんの本物のGASウェブアプリURLをここに貼り付けます★
gas_url = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec" 

# 0. 担当者の選択（変えるまで維持）
if "selected_user" not in st.session_state:
    st.session_state.selected_user = "吉本"

user_list = [
    "吉本", "塚越", "岡本", "中島", "関口", "石森", "堀越", 
    "田代", "塩原", "吉田", "杉山", "南雲", "A", "B", "アルミ", "アクリル"
] 

user_name = st.selectbox("👤 本日の登録者を選択してください", user_list, index=user_list.index(st.session_state.selected_user))
st.session_state.selected_user = user_name

# 【上半分】通常の「新規加算 登録エリア」
st.subheader("📥 1. 通常の数量加算（新規登録）")

reg_category = st.radio(
    "👇 数量を加算したい項目を選択してください",
    ("縦カット", "横カット", "敷砂付", "スペーサー加工", "裏面貼付", "中座セット", "出来待ち", "出荷待ち", "仕上"),
    horizontal=True,
    key="reg_cat_radio"
)

if "trigger_clear_reg" not in st.session_state:
    st.session_state.trigger_clear_reg = False
if "reg_stock_data" not in st.session_state:
    st.session_state.reg_stock_data = None
if "reg_item_name" not in st.session_state:
    st.session_state.reg_item_name = ""
if "last_reg_jan" not in st.session_state:
    st.session_state.last_reg_jan = ""
if "grand_total_data" not in st.session_state:
    st.session_state.grand_total_data = None

reg_key = "jan_reg_active"
if st.session_state.trigger_clear_reg:
    reg_key = "jan_reg_reset"
    st.session_state.trigger_clear_reg = False

jan_reg = st.text_input("👉 加算するバーコード（JAN）をスキャン：", value="", key=reg_key)

if jan_reg and jan_reg.strip() != "" and jan_reg.strip() != st.session_state.last_reg_jan:
    current_reg_jan = jan_reg.strip()
    st.session_state.last_reg_jan = current_reg_jan
    try:
        res = requests.post(gas_url, json={"janCode": current_reg_jan, "status": "縦カット", "count": 0, "user": user_name, "action": "check"}, timeout=10).json()
        if res.get("status") == "success":
            st.session_state.reg_item_name = res.get("itemName", "商品名不明")
            st.session_state.reg_stock_data = res.get("stockData")
            st.session_state.grand_total_data = res.get("grandTotalData")
            st.session_state.mod_item_name = res.get("itemName", "商品名不明")
            st.session_state.mod_stock_data = res.get("stockData")
    except:
        pass

if st.session_state.reg_item_name and st.session_state.reg_stock_data:
    st.info(f"📦 対象商品: **{st.session_state.reg_item_name}**")
    st.write("📊 **現在のアイテム内 主要在庫数（加算前）**")
    col_reg1, col_reg2, col_reg3 = st.columns(3)
    col_reg1.metric("縦カット", f"{st.session_state.reg_stock_data.get('縦カット', 0)} 個")
    col_reg2.metric("スペーサー加工", f"{st.session_state.reg_stock_data.get('スペーサー加工', 0)} 個")
    col_reg3.metric("出来待ち", f"{st.session_state.reg_stock_data.get('出来待ち', 0)} 個")

count_reg = st.slider("👉 加算する数量をスクロールで入力：", min_value=1, max_value=100, value=1, key="count_reg_slider")

if st.button("🚀 上記の項目に数量を加算する", use_container_width=True):
    if st.session_state.last_reg_jan != "":
        with st.spinner("クラウドに数量を加算中..."):
            try:
                payload = {"janCode": st.session_state.last_reg_jan, "status": reg_category, "count": count_reg, "user": user_name, "action": "register"}
                res = requests.post(gas_url, json=payload, timeout=10).json()
                if res.get("status") == "success":
                    st.success(f"✅ 【{reg_category}】に数量 {count_reg} 個を加算登録しました！")
                    st.session_state.grand_total_data = res.get("grandTotalData")
                    time.sleep(2)
                    st.session_state.trigger_clear_reg = True
                    st.session_state.reg_stock_data = None
                    st.session_state.reg_item_name = ""
                    st.session_state.last_reg_jan = ""
                    st.rerun()
                else:
                    st.error(f"❌ エラー：{res.get('message')}")
            except Exception as e:
                st.error(f"🚨 通信エラー: {str(e)}")

st.write(" ")

# 【下半分】常時在庫状況 表示 ＆ 修正する 選択エリア
st.subheader("🔍 2. 現在の在庫状況 確認・直接修正")

if "trigger_clear_mod" not in st.session_state:
    st.session_state.trigger_clear_mod = False
if "mod_stock_data" not in st.session_state:
    st.session_state.mod_stock_data = None
if "mod_item_name" not in st.session_state:
    st.session_state.mod_item_name = ""
if "last_mod_jan" not in st.session_state:
    st.session_state.last_mod_jan = ""

mod_key = "jan_mod_active"
if st.session_state.trigger_clear_mod:
    mod_key = "jan_mod_reset"
    st.session_state.trigger_clear_mod = False

jan_mod = st.text_input("🔍 在庫を確認するバーコード（JAN）をスキャン：", value="", key=mod_key)

if jan_mod and jan_mod.strip() != "" and jan_mod.strip() != st.session_state.last_mod_jan:
    current_jan = jan_mod.strip()
    st.session_state.last_mod_jan = current_jan
    try:
        res = requests.post(gas_url, json={"janCode": current_jan, "status": "縦カット", "count": 0, "user": user_name, "action": "check"}, timeout=10).json()
        if res.get("status") == "success":
            st.session_state.mod_item_name = res.get("itemName", "商品名不明")
            st.session_state.mod_stock_data = res.get("stockData")
            st.session_state.grand_total_data = res.get("grandTotalData")
            st.session_state.reg_item_name = res.get("itemName", "商品名不明")
            st.session_state.reg_stock_data = res.get("stockData")
    except:
        pass

if st.session_state.mod_item_name and st.session_state.mod_stock_data:
    st.info(f"📦 対象商品: **{st.session_state.mod_item_name}**")
    st.write("📊 **現在のアイテム内 在庫数（常時確認用）**")
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("縦カット", f"{st.session_state.mod_stock_data.get('縦カット', 0)} 個")
    col_s2.metric("スペーサー加工", f"{st.session_state.mod_stock_data.get('スペーサー加工', 0)} 個")
    col_s3.metric("出来待ち", f"{st.session_state.mod_stock_data.get('出来待ち', 0)} 個")

    st.markdown("---")
    is_modify_mode = st.checkbox("✏️ 登録数量を直接上書き修正する", value=False)

    if is_modify_mode:
        st.write("🔧 **数量の直接上書き修正モード**")
        mod_category = st.radio(
            "👇 修正したい項目（コマンド）を選択してください", 
            ("縦カット", "横カット", "敷砂付", "スペーサー加工", "裏面貼付", "中座セット", "出来待ち", "出荷待ち", "仕上"), 
            horizontal=True, 
            key="mod_cat_radio"
        )

        default_mod_count = int(st.session_state.mod_stock_data.get(mod_category, 0))
        count_mod = st.slider(f"👉 【 {mod_category} 】の正しい数量を指定してください", min_value=0, max_value=200, value=default_mod_count, key="count_mod_slider")

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("🚀 この内容で数量を上書き（修正）する", use_container_width=True):
                with st.spinner("クラウド上の在庫データを直接書き換え中..."):
                    try:
                        payload = {"janCode": st.session_state.last_mod_jan, "status": mod_category, "count": count_mod, "user": user_name, "action": "modify"}
                        res = requests.post(gas_url, json=payload, timeout=10).json()
                        if res.get("status") == "success":
                            st.success(f"✅ 【{mod_category}】の数量を {count_mod} 個に直接上書き修正しました！")
                            st.session_state.grand_total_data = res.get("grandTotalData")
                            time.sleep(2)
                            st.session_state.trigger_clear_mod = True
                            st.session_state.mod_stock_data = None
                            st.session_state.mod_item_name = ""
                            st.session_state.last_mod_jan = ""
                            st.rerun()
                    except Exception as e:
                        st.error(f"🚨 通信エラー: {str(e)}")
        with btn_col2:
            if st.button("❌ 修正をキャンセルして閉じる", use_container_width=True):
                st.session_state.trigger_clear_mod = True
                st.session_state.mod_stock_data = None
                st.session_state.mod_item_name = ""
                st.session_state.last_mod_jan = ""
                st.rerun()

# 【最下部】3．全体の在庫状況（確認用）エリア（工場全体の総計）
st.markdown("---")
is_show_total = st.checkbox("📈 3．全体の在庫状況（確認用）を表示する", value=False)

if is_show_total and st.session_state.grand_total_data:
    st.subheader("📋 3．工場全体の在庫状況（全アイテムの総和）")
    
    g_t1, g_t2, g_t3, g_t4 = st.columns(4)
    g_t1.metric("縦カット総数", f"{st.session_state.grand_total_data.get('縦カット', 0):,} 個")
    g_t2.metric("スペーサー加工総数", f"{st.session_state.grand_total_data.get('スペーサー加工', 0):,} 個")
    g_t3.metric("出来待ち総数", f"{st.session_state.grand_total_data.get('出来待ち', 0):,} 個")
    g_t4.metric("出荷待ち総数", f"{st.session_state.grand_total_data.get('出荷待ち', 0):,} 個")
    
    st.info(f"📊 **全自動集計・シート全体の総在庫数: {st.session_state.grand_total_data.get('grandTotal', 0):,} 個**")
```

---

## 📊 2. GAS（Google Apps Script）用：最新完全版コード
※4行目の「列の名前（見出し）」を自動で検索してピンポイントで書き込むため、スプレッドシートの列を後から自由に移動させても一切壊れません。

```javascript
function doPost(e) {
  try {
    var params = JSON.parse(e.postData.contents);
    var janCode = String(params.janCode).trim();
    var category = params.status; // 「縦カット」「スペーサー加工」などの文字列が直接届きます
    var inputCount = Number(params.count);
    var userName = params.user || "未入力";
    var action = params.action || "register";
    
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var lastRow = sheet.getLastRow();
    var lastCol = sheet.getLastColumn();
    
    // 1万行高速 janコード 検索
    var janFinder = sheet.getRange(1, 3, lastRow, 1).createTextFinder(janCode).matchEntireCell(true).findNext();
    if (!janFinder) {
