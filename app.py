import streamlit as st
import pandas as pd
from datetime import date
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 🎨 ဒီဇိုင်းပိုလှစေရန် CSS ထည့်သွင်းခြင်း ---
def local_css():
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        border-left: 5px solid #1e88e5;
    }
    .income-card { border-left-color: #2e7d32; }
    .expense-card { border-left-color: #d32f2f; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔄 မြန်မာဂဏန်းများကို အင်္ဂလိပ်ဂဏန်းသို့ ပြောင်းပေးသော Function ---
def parse_amount(val):
    if pd.isna(val) or val == "":
        return 0
    val = str(val)
    mm_nums = "၀၁၂၃၄၅၆၇၈၉"
    en_nums = "0123456789"
    table = str.maketrans(mm_nums, en_nums)
    val = val.translate(table)
    val = val.replace(",", "").replace("Ks", "").replace("ကျပ်", "").strip()
    try:
        return float(val)
    except:
        return 0

# --- 🔒 အပိုင်း (၁) : Login နှင့် Password စနစ် ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center; color: #1e88e5;'>🔒 မိမိဆိုင်၏ POS စနစ်သို့ ဝင်ရောက်ရန်</h2>", unsafe_allow_html=True)
        st.text_input("စကားဝှက် (Password) ရိုက်ထည့်ပါ", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center; color: #1e88e5;'>🔒 မိမိဆိုင်၏ POS စနစ်သို့ ဝင်ရောက်ရန်</h2>", unsafe_allow_html=True)
        st.text_input("စကားဝှက် (Password) ရိုက်ထည့်ပါ", type="password", on_change=password_entered, key="password")
        st.error("❌ စကားဝှက် မှားယွင်းနေပါသည်။ ပြန်လည်ကြိုးစားပါ။")
        return False
    return True

# Password မှန်ကန်မှသာ အောက်ပါ POS စနစ်ကို အလုပ်လုပ်စေမည်
if check_password():
    local_css() 
    st.markdown("<h1 style='text-align: center; color: #1565c0;'>📊 နေ့စဉ် အသုံးစရိတ် POS စနစ်</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 2px solid #e0e0e0;'>", unsafe_allow_html=True)

    # --- ☁️ အပိုင်း (၂) : Google Sheets ဖြင့် ချိတ်ဆက်ခြင်း ---
    @st.cache_resource
    def get_gspread_client():
        credentials_dict = dict(st.secrets["gcp_service_account"])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        return gspread.authorize(creds)

    SHEET_NAME = "My_POS_Data" 
    
    # --- ⚡ ချက်ချင်း Update ဖြစ်စေရန် Form Data ကို ကြိုတင်သိမ်းဆည်းမည့် Function ---
    def handle_submit():
        client = get_gspread_client()
        try:
            sheet = client.open(SHEET_NAME).sheet1
        except:
            st.session_state.form_msg = ("error", f"'{SHEET_NAME}' အမည်ရှိ Google Sheet ကို ရှာမတွေ့ပါ။")
            return

        t_date = st.session_state.t_date
        t_type = st.session_state.t_type
        desc = st.session_state.t_desc
        amount_input = st.session_state.t_amount

        amount = parse_amount(amount_input)
        if desc == "" or amount <= 0:
            st.session_state.form_msg = ("warning", "⚠️ အကြောင်းအရာနှင့် ပမာဏကို ပြည့်စုံစွာ ထည့်ပါ။ (ပမာဏသည် ဂဏန်းဖြစ်ရပါမည်)")
        else:
            formatted_date = t_date.strftime("%d-%m-%Y")
            new_row = [formatted_date, t_type, desc, amount]
            sheet.append_row(new_row)
            
            # Google API မှ Data ချက်ချင်း Update ဖြစ်ရန် ၁.၅ စက္ကန့်ခန့် စောင့်ဆိုင်းခြင်း
            time.sleep(1.5)
            st.session_state.form_msg = ("success", "✅ စာရင်းကို Google Sheets သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!")

    # Google Sheet ချိတ်ဆက်ခြင်း
    client = get_gspread_client()
    try:
        sheet = client.open(SHEET_NAME).sheet1
    except:
        st.error(f"'{SHEET_NAME}' အမည်ရှိ Google Sheet ကို ရှာမတွေ့ပါ။")
        st.stop()

    # --- 📈 အပိုင်း (၃) : တွက်ချက်ခြင်း နှင့် Dashboard ပြသခြင်း ---
    def load_data():
        records = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
        return pd.DataFrame(records)

    df = load_data()

    if not df.empty:
        if "အမျိုးအစား" in df.columns and "ပမာဏ" in df.columns:
            df["အမျိုးအစား"] = df["အမျိုးအစား"].astype(str).str.strip()
            df["ပမာဏ"] = df["ပမာဏ"].apply(parse_amount)
            
            total_income = df[df["အမျိုးအစား"] == "ဝင်ငွေ"]["ပမာဏ"].sum()
            total_expense = df[df["အမျိုးအစား"] == "ထွက်ငွေ"]["ပမာဏ"].sum()
        else:
            st.error("⚠️ Google Sheet တွင် 'အမျိုးအစား' နှင့် 'ပမာဏ' ကော်လံများ မတွေ့ပါ။ ခေါင်းစဉ်များ မှန်ကန်မှုရှိမရှိ စစ်ဆေးပါ။")
            st.stop()
    else:
        total_income = 0
        total_expense = 0
        
    balance = total_income - total_expense

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='metric-card income-card'><h3 style='color: #2e7d32; margin-bottom: 0;'>💰 ဝင်ငွေ</h3><h2 style='color: #333;'>{int(total_income):,} Ks</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card expense-card'><h3 style='color: #d32f2f; margin-bottom: 0;'>📉 ထွက်ငွေ</h3><h2 style='color: #333;'>{int(total_expense):,} Ks</h2></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='metric-card'><h3 style='color: #1e88e5; margin-bottom: 0;'>🏦 လက်ကျန်</h3><h2 style='color: #333;'>{int(balance):,} Ks</h2></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 📝 အပိုင်း (၄) : စာရင်းအသစ် သွင်းခြင်း ---
    st.markdown("<h3 style='color: #e65100;'>📝 စာရင်းအသစ် ထည့်သွင်းရန်</h3>", unsafe_allow_html=True)

    # သိမ်းဆည်းပြီးကြောင်း မက်ဆေ့ချ်ပြသရန်
    if "form_msg" in st.session_state:
        msg_type, msg_text = st.session_state.form_msg
        if msg_type == "success":
            st.success(msg_text)
        elif msg_type == "error":
            st.error(msg_text)
        else:
            st.warning(msg_text)
        del st.session_state.form_msg # ပြပြီးရင် ပြန်ဖျက်မည်

    with st.form("transaction_form", clear_on_submit=True):
        st.date_input("ရက်စွဲ (နေ့-လ-နှစ်)", date.today(), format="DD/MM/YYYY", key="t_date")
        st.selectbox("အမျိုးအစား ရွေးချယ်ပါ", ["ဝင်ငွေ", "ထွက်ငွေ"], key="t_type")
        st.text_input("အကြောင်းအရာ (ဥပမာ - ကုန်ကြမ်းဝယ် / ပစ္စည်းရောင်းရငွေ)", key="t_desc")
        st.text_input("ပမာဏ (ကျပ်) - ဥပမာ: 1000 သို့မဟုတ် ၁၀၀၀", key="t_amount")
        
        # ခလုတ်နှိပ်သည်နှင့် on_click ဖြင့် handle_submit ကို ချက်ချင်း အလုပ်လုပ်စေမည်
        st.form_submit_button("စာရင်းသွင်းမည်", on_click=handle_submit)

    st.markdown("---")
    
    # --- 📋 အပိုင်း (၅) : စာရင်းမှတ်တမ်း ဇယား (အရောင်များဖြင့်) ---
    st.markdown("<h3 style='color: #6a1b9a;'>📋 ယခင်စာရင်း မှတ်တမ်းများ</h3>", unsafe_allow_html=True)
    if not df.empty:
        display_df = df.copy()
        display_df["ပမာဏ"] = display_df["ပမာဏ"].apply(lambda x: f"{int(x):,} Ks")
        
        def highlight_type(val):
            if val == 'ဝင်ငွေ':
                return 'color: #2e7d32; font-weight: bold; background-color: #e8f5e9;' 
            elif val == 'ထွက်ငွေ':
                return 'color: #d32f2f; font-weight: bold; background-color: #ffebee;' 
            return ''
            
        styled_df = display_df.style.map(highlight_type, subset=['အမျိုးအစား'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("မှတ်တမ်းများ မရှိသေးပါ။")
