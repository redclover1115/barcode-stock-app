import streamlit as st
import requests

# --- [既存のコード] ボタンが押されたり、初期データを用意する部分 ---
# ※ payload には janCode, status, count, user, action が入っている想定です

# GASのWebアプリURL（お使いのURLに差し替えてください）
GAS_URL = "https://script.google.com/macros/s/AKfycbzqCJKbh31A1MD19mhbLyAhQa2LxN34zs2XxrEaCe64Gl-1uthsF7qzn89fh36J0FH1/exec" 

# 初回送信ボタンが押されたときの処理（例）
if st.button("上記の項目に数量を加算する"):
    # 状態をクリアするためのセッション初期化
    st.session_state["mismatch_detected"] = False
    
    # GASへ一回目のリクエスト
    response = requests.post(GAS_URL, json=payload)
    res_data = response.json()
    
    if res_data.get("status") == "success":
        st.success(f"【{res_data['itemName']}】の工程移動が通常完了しました！")
        st.rerun()
        
    elif res_data.get("status") == "qty_mismatch":
        # 数量不一致エラーを検知した場合、セッションに状態を保存して画面を切り替える
        st.session_state["mismatch_detected"] = True
        st.session_state["prev_details"] = res_data["details"]
        st.session_state["original_payload"] = payload

# --- 数量不一致エラーが発生した時だけ出現する「理由入力フォーム」 ---
if st.session_state.get("mismatch_detected", False):
    details = st.session_state["prev_details"]
    
    st.error(f"⚠️ {res_data.get('message')}")
    st.info(
        f"**現在の不一致状況**\n\n"
        f"・前工程（{details['prevStatus']}）の残数: **{details['prevCount']}** 個\n\n"
        f"・今回移動させようとした数: **{details['inputCount']}** 個\n\n"
        f"➡️ 差分の **{details['prevCount'] - details['inputCount']}** 個について、以下のマイナス理由の内訳を入力してください。"
    )
    
    # 理由入力用のフォーム
    with st.form("reason_input_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            count_shikka = st.number_input("1. 出荷された", min_value=0, value=0, step=1)
        with col2:
            count_furyo = st.number_input("2. 不良", min_value=0, value=0, step=1)
        with col3:
            count_sonota = st.number_input("3. その他", min_value=0, value=0, step=1)
            
        submit_reason = st.form_submit_button("内訳を確定して再送信する")
        
        if submit_reason:
            # 「今回の入力数」＋「マイナス理由の合計」を計算
            total_calculated = details['inputCount'] + count_shikka + count_furyo + count_sonota
            
            # 前工程の総数と一致するか厳密にチェック
            if total_calculated == details['prevCount']:
                # 元のデータに強制処理フラグと内訳を上乗せする
                retry_payload = st.session_state["original_payload"]
                retry_payload["forceHeader"] = True
                retry_payload["countShikka"] = count_shikka
                retry_payload["countFuryo"] = count_furyo
                retry_payload["countSonota"] = count_sonota
                
                # GASへ二回目のリクエスト（強制上書き処理）
                retry_response = requests.post(GAS_URL, json=retry_payload)
                retry_res_data = retry_response.json()
                
                if retry_res_data.get("status") == "success":
                    st.success("理由を確認し、前工程をクリアして無事に移動が完了しました！")
                    # セッションをクリアして画面を元に戻す
                    st.session_state["mismatch_detected"] = False
                    st.rerun()
                else:
                    st.error(f"エラーが発生しました: {retry_res_data.get('message')}")
            else:
                # 合計数が合わない場合は、処理をブロックして警告を出す
                gap = details['prevCount'] - total_calculated
                if gap > 0:
                    st.warning(f"❌ 数量がまだ **{gap}個** 足りません。内訳を正しく修正してください。")
                else:
                    st.warning(f"❌ 内訳の合計が前工程の数を **{abs(gap)}個** 超えています。修正してください。")
