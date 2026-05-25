import streamlit as st
import pandas as pd
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 🔄 မြန်မာဂဏန်းများကို အင်္ဂလိပ်ဂဏန်းသို့ ပြောင်းပေးသော Function ---
def parse_amount(val):
    if pd.isna(val) or val == "":
        return 0
    val = str(val)
    # မြန်မာဂဏန်းများကို အင်္ဂလိပ်သို့ ပြောင်းခြင်း
    mm_nums = "၀၁၂၃၄၅၆၇၈၉"
    en_nums = "0123456789"
    table = str.maketrans(mm_nums, en_nums)
    val = val.translate(table)
    # ကော်မာ နှင့် စာသားများ ပါနေလျှင် ဖယ်ရှားခြင်း
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
        st.title("🔒 မိမိဆိုင်၏ POS စနစ်သို့ ဝင်ရောက်ရန်")
        st.text_input("စကားဝှက် (Password) ရိုက်ထည့်ပါ", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 မိမိဆိုင်၏ POS စနစ်သို့ ဝင်ရောက်ရန်")
        st.text_input("စကားဝှက် (Password) ရိုက်ထည့်ပါ", type="password", on_change=password_entered, key="password")
        st.error("❌ စကားဝှက် မှားယွင်းနေပါသည်။ ပြန်လည်ကြိုးစားပါ။")
        return False
    return True

# Password မှန်ကန်မှသာ အောက်ပါ POS စနစ်ကို အလုပ်လုပ်စေမည်
if check_password():
    st.title("📊 နေ့စဉ် အသုံးစရိတ် POS စနစ်")

    # --- ☁️ အပိုင်း (၂) : Google Sheets ဖြင့် ချိတ်ဆက်ခြင်း ---
    @st.cache_resource
    def get_gspread_client():
        credentials_dict = dict(st.secrets["gcp_service_account"])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        return gspread.authorize(creds)
        
    client = get_gspread_client()
    
    SHEET_NAME = "My_POS_Data" 
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
            # အထက်ပါ parse_amount စနစ်ဖြင့် ဂဏန်းများကို ရှင်းလင်းခြင်း
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
    col1.metric("💰 ဝင်ငွေ စုစုပေါင်း", f"{int(total_income):,} Ks")
    col2.metric("📉 ထွက်ငွေ စုစုပေါင်း", f"{int(total_expense):,} Ks")
    col3.metric("🏦 လက်ကျန်ငွေ", f"{int(balance):,} Ks")
    st.markdown("---")

    # --- 📝 အပိုင်း (၄) : စာရင်းအသစ် သွင်းခြင်း ---
    st.subheader("📝 စာရင်းအသစ် ထည့်သွင်းရန်")
    with st.form("transaction_form", clear_on_submit=True):
        t_date = st.date_input("ရက်စွဲ", date.today())
        t_type = st.selectbox("အမျိုးအစား ရွေးချယ်ပါ", ["ဝင်ငွေ", "ထွက်ငွေ"])
        desc = st.text_input("အကြောင်းအရာ (ဥပမာ - ကုန်ကြမ်းဝယ် / ပစ္စည်းရောင်းရငွေ)")
        
        # မြန်မာဂဏန်းရော အင်္ဂလိပ်ဂဏန်းပါ ရိုက်ထည့်နိုင်ရန် Text Input အသုံးပြုထားပါသည်
        amount_input = st.text_input("ပမာဏ (ကျပ်) - ဥပမာ: 1000 သို့မဟုတ် ၁၀၀၀")
        
        submitted = st.form_submit_button("စာရင်းသွင်းမည်")
        if submitted:
            amount = parse_amount(amount_input)
            if desc == "" or amount <= 0:
                st.warning("အကြောင်းအရာနှင့် ပမာဏကို ပြည့်စုံစွာ ထည့်ပါ။ (ပမာဏသည် ဂဏန်းဖြစ်ရပါမည်)")
            else:
                new_row = [str(t_date), t_type, desc, amount]
                sheet.append_row(new_row)
                st.success("✅ စာရင်းကို Google Sheets သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 ယခင်စာရင်း မှတ်တမ်းများ")
    if not df.empty:
        # ဇယားတွင်ပြသမည့် ဂဏန်းများကို ကော်မာ (,) ဖြင့် ကြည့်ကောင်းအောင် ပြင်ဆင်ခြင်း
        display_df = df.copy()
        display_df["ပမာဏ"] = display_df["ပမာဏ"].apply(lambda x: f"{int(x):,} Ks")
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("မှတ်တမ်းများ မရှိသေးပါ။")
