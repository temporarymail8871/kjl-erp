import streamlit as st
import datetime
import pandas as pd
import altair as alt
import base64
import os
import requests
import json
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="KJL Poultries Pvt Ltd", page_icon="Logo png.png", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
    [data-testid="stSidebar"] * { color: #374151 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    [data-testid="stSidebar"] h1 { color: #1B5E20 !important; font-weight: 800; font-size: 24px; padding-bottom: 10px; margin-top: 10px;}
    
    [data-testid="stMetric"] { background-color: #FFFFFF; border: 1px solid #F3F4F6; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #111827; }
    [data-testid="stMetricLabel"] { font-size: 13px; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px;}
    [data-testid="stMetricDelta"] svg { display: none; }
    
    .custom-table-container { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E5E7EB; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px;}
    .custom-table { width: 100%; border-collapse: collapse; font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #374151; }
    .custom-table th { background-color: #FFFFFF; color: #6B7280; padding: 16px 24px; text-align: left; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #E5E7EB;}
    .custom-table td { padding: 16px 24px; border-bottom: 1px solid #F3F4F6; vertical-align: middle; }
    .custom-table tr:last-child td { border-bottom: none; }
    .custom-table tr:hover { background-color: #F9FAFB; }
    
    .status-blue { color: #2563EB; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; }
    .status-blue::before { content: ''; width: 8px; height: 8px; background-color: #2563EB; border-radius: 50%; }
    .status-green { color: #16A34A; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; }
    .status-green::before { content: ''; width: 8px; height: 8px; background-color: #16A34A; border-radius: 50%; }
    .status-red { color: #DC2626; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; }
    .status-red::before { content: ''; width: 8px; height: 8px; background-color: #DC2626; border-radius: 50%; }
    .status-orange { color: #F59E0B; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; }
    .status-orange::before { content: ''; width: 8px; height: 8px; background-color: #F59E0B; border-radius: 50%; }
    .status-dark { color: #4B5563; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; }
    .status-dark::before { content: ''; width: 8px; height: 8px; background-color: #4B5563; border-radius: 50%; }
    
    .blue-header { background-color: #1B5E20; color: white; text-align: center; font-weight: bold; padding: 8px; font-size: 14px; margin-top: 15px; margin-bottom: 10px; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# --- CLOUD DATABASE ENGINE (REQUESTS API) ---
DB_URL = "https://ejbgjfhdotsgpivkvics.supabase.co/rest/v1"
STORAGE_URL = "https://ejbgjfhdotsgpivkvics.supabase.co/storage/v1/object/dispatch_photos"
DB_KEY = "sb_publishable_YtTVgVdC4vn7qEOCDyrUeA_1rFwzHkt"
DB_HEADERS = {
    "apikey": DB_KEY,
    "Authorization": f"Bearer {DB_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def _db_call(method, endpoint, payload=None):
    url = f"{DB_URL}/{endpoint}"
    try:
        if method == "GET": response = requests.get(url, headers=DB_HEADERS)
        elif method == "POST": response = requests.post(url, headers=DB_HEADERS, json=payload)
        elif method == "PATCH": response = requests.patch(url, headers=DB_HEADERS, json=payload)
        if response.status_code >= 400:
            st.error(f"Database Error {response.status_code}: {response.text}")
            return None
        return response.json()
    except Exception as e:
        st.error(f"Network Connection Failed: {str(e)}")
        return None

def fetch_table(table_name): 
    data = _db_call("GET", f"{table_name}?select=*")
    return data if isinstance(data, list) else []

def insert_table(table_name, payload): return _db_call("POST", table_name, payload) is not None
def update_table(table_name, pk_col, pk_val, payload): return _db_call("PATCH", f"{table_name}?{pk_col}=eq.{pk_val}", payload) is not None

def upload_file_to_supabase(file_bytes, filename, content_type):
    url = f"{STORAGE_URL}/{filename}"
    headers = {"apikey": DB_KEY, "Authorization": f"Bearer {DB_KEY}", "Content-Type": content_type}
    res = requests.post(url, headers=headers, data=file_bytes)
    if res.status_code == 200:
        return f"https://ejbgjfhdotsgpivkvics.supabase.co/storage/v1/object/public/dispatch_photos/{filename}"
    return None

# --- INITIALIZE APP STATE & SYNC DATABASE ---
if "db_synced" not in st.session_state:
    st.session_state["transactions"] = fetch_table("transactions")
    st.session_state["production"] = fetch_table("production")
    st.session_state["adjustments"] = fetch_table("adjustments")
    
    mats_db = fetch_table("materials")
    st.session_state["materials"] = [m["Name"] for m in mats_db] if mats_db else []
    st.session_state["material_costs"] = {m["Name"]: float(m["Cost"]) for m in mats_db} if mats_db else {}
    
    vendors_db = fetch_table("vendors")
    st.session_state["vendors"] = [v["Name"] for v in vendors_db] if vendors_db else []
    
    loc_db = fetch_table("locations")
    st.session_state["locations"] = [l["Name"] for l in loc_db] if loc_db else []
    
    feeds_db = fetch_table("feed_names")
    st.session_state["feed_names"] = [f["Name"] for f in feeds_db] if feeds_db else []
    
    bom_db = fetch_table("bom")
    st.session_state["bom"] = {b["Formula_Name"]: b["Recipe"] for b in bom_db} if bom_db else {}
    
    if "formula_reset_key" not in st.session_state: st.session_state["formula_reset_key"] = 1
    st.session_state["db_synced"] = True

if "users" not in st.session_state:
    st.session_state["users"] = {
        "admin": {"password": "123", "role": "Admin", "name": "Durga Prasad P.", "emp_id": "KJL-001"},
        "sec": {"password": "123", "role": "Security", "name": "Gate Guard", "emp_id": "KJL-002"},
        "lab": {"password": "123", "role": "QC_Lab", "name": "Lab Tech", "emp_id": "KJL-003"},
        "wb": {"password": "123", "role": "Weighbridge", "name": "Scale Operator", "emp_id": "KJL-004"},
        "loading": {"password": "123", "role": "Loading_Supervisor", "name": "Loading Team", "emp_id": "KJL-005"}
    }

LOGO_FILE = "Logo png.png"

# --- HELPER FUNCTIONS ---
def get_ist_now():
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    return datetime.datetime.now(ist)

def get_next_id(data_list, id_key):
    max_id = 1000
    for item in data_list:
        val = item.get(id_key, "")
        try:
            num = int(val.split("-")[-1])
            if num > max_id: max_id = num
        except: pass
    return max_id + 1

def format_vehicle_label(t):
    if t.get("Transaction_Type", "Inbound") == "Inbound":
        return f"{t.get('Gate_Pass_ID')} - {t.get('Vehicle_No')} ({t.get('Material', '')} from {t.get('Vendor', '')})"
    else:
        return f"{t.get('Gate_Pass_ID')} - {t.get('Vehicle_No')} ({t.get('Material', 'FEED')} for {t.get('Vendor', 'KJL')})"

def get_photo_links_html(photo_url_string):
    if not photo_url_string: return "-"
    urls = photo_url_string.split(",")
    if len(urls) == 1:
        return f"<a href='{urls[0]}' target='_blank'>📷 View</a>"
    else:
        links = [f"<a href='{u}' target='_blank'>[{i+1}]</a>" for i, u in enumerate(urls)]
        return f"📷 {' '.join(links)}"

def calculate_inventory():
    inventory = {mat: 50000.0 for mat in st.session_state["materials"]} 
    finished_goods = {feed: 0.0 for feed in st.session_state["feed_names"]}
    for t in st.session_state["transactions"]:
        if t.get("Status") == "Completed" and "Net_Weight" in t:
            if t.get("Transaction_Type", "Inbound") == "Inbound" and t.get("Material") in inventory: 
                inventory[t["Material"]] += t.get("Net_Weight", 0)
            elif t.get("Transaction_Type") == "Outbound" and t.get("Feed_Name") in finished_goods:
                finished_goods[t["Feed_Name"]] -= (t.get("Net_Weight", 0) / 1000.0) 
    for p in st.session_state["production"]:
        form = p.get("Formula", "")
        if form in st.session_state["bom"]:
            recipe = st.session_state["bom"][form]
            in_qty = p.get("In_Qty_kg", 0)
            for mat, pct in recipe.items():
                if mat in inventory: inventory[mat] -= (in_qty * pct)
            feed_n = p.get("Feed_Name", "")
            if feed_n in finished_goods: finished_goods[feed_n] += (p.get("Out_Qty_kg", 0) / 1000)
    for adj in st.session_state["adjustments"]:
        qty = adj["Quantity"] if adj["Type"] == "Addition (+)" else -adj["Quantity"]
        if adj["Item"] in inventory: inventory[adj["Item"]] += qty
        elif adj["Item"] in finished_goods: finished_goods[adj["Item"]] += qty 
    return inventory, finished_goods

def get_print_link(data_dict, doc_type="PROD"):
    logo_img_tag = ""
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, "rb") as img_file:
            b64_logo = base64.b64encode(img_file.read()).decode()
            logo_img_tag = f'<img src="data:image/png;base64,{b64_logo}" style="display:block; margin: 0 auto; width: 80px; margin-bottom: 10px;">'

    if doc_type == "PROD":
        html = f"""<!DOCTYPE html><html><body onload="window.print()" style="font-family: monospace; padding: 20px;"><div style="border: 2px dashed #333; padding: 30px; max-width: 400px; margin: 0 auto;">{logo_img_tag}<h2 style="text-align: center; margin-top: 0;">KJL POULTRIES PVT LTD</h2><h3 style="text-align: center;">Production Receipt: {data_dict.get('Invoice', '')}</h3><hr><p><b>Date:</b> {data_dict.get('Date', '')} | <b>Loc:</b> {data_dict.get('Location', '')}</p><p><b>Feed:</b> {data_dict.get('Feed_Name', '')} ({data_dict.get('Formula', '')})</p><hr><p><b>Output:</b> {data_dict.get('Out_Qty_kg', 0):,.0f} kg ({data_dict.get('Bags', 0)} Bags)</p><p><b>Total Cost:</b> Rs. {data_dict.get('Total_Amount', 0):.2f}</p></div></body></html>"""
    elif doc_type == "INWARD":
        html = f"""<!DOCTYPE html><html><body onload="window.print()" style="font-family: monospace; padding: 20px;"><div style="border: 2px dashed #333; padding: 30px; max-width: 400px; margin: 0 auto;">{logo_img_tag}<h2 style="text-align: center; margin-top: 0;">KJL POULTRIES PVT LTD</h2><h3 style="text-align: center;">INWARD SLIP</h3><hr><p><b>Pass:</b> {data_dict.get('Gate_Pass_ID', '')} | <b>Date:</b> {data_dict.get('Date', '')}</p><p><b>Vehicle:</b> {data_dict.get('Vehicle_No', '')} | <b>Vendor:</b> {data_dict.get('Vendor', '')}</p><p><b>Material:</b> {data_dict.get('Material', '')}</p><hr><p style="font-size: 18px;"><b>NET WT: {data_dict.get('Net_Weight', 0)} kg</b></p></div></body></html>"""
    else:
        html = f"""<!DOCTYPE html><html><body onload="window.print()" style="font-family: monospace; padding: 20px;"><div style="border: 2px dashed #333; padding: 30px; max-width: 400px; margin: 0 auto;">{logo_img_tag}<h2 style="text-align: center; margin-top: 0;">KJL POULTRIES PVT LTD</h2><h3 style="text-align: center;">DELIVERY CHALLAN</h3><hr><p><b>ID:</b> {data_dict.get('Gate_Pass_ID', '')} | <b>Date:</b> {data_dict.get('Date', '')}</p><p><b>Vehicle:</b> {data_dict.get('Vehicle_No', '')} | <b>Dest:</b> {data_dict.get('Vendor', '')}</p><hr><p><b>Feed:</b> {data_dict.get('Feed_Name', '')}</p><p style="font-size: 18px;"><b>BAGS: {data_dict.get('Bags', 0)}</b></p><p style="font-size: 18px;"><b>NET WT: {data_dict.get('Net_Weight', 0)} kg</b></p></div></body></html>"""
    b64 = base64.b64encode(html.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" target="_blank" style="text-decoration: none; font-size: 18px; filter: grayscale(100%);" title="Print in New Tab">🖨️</a>'

def render_table(headers, rows_html):
    st.markdown(f"<div class='custom-table-container'><table class='custom-table'><thead><tr>{''.join([f'<th>{h}</th>' for h in headers])}</tr></thead><tbody>{rows_html}</tbody></table></div>", unsafe_allow_html=True)

def format_status(status_text):
    if status_text in ["Pending QC", "Pending Tare"]: return f"<span class='status-blue'>{status_text}</span>"
    elif status_text in ["QC Passed", "QC Passed with Rebate", "Loading"]: return f"<span class='status-green'>{status_text}</span>"
    elif status_text == "QC Rejected": return f"<span class='status-red'>{status_text}</span>"
    elif status_text in ["Unloading", "Pending Gross"]: return f"<span class='status-orange'>{status_text}</span>"
    elif status_text == "Completed": return f"<span class='status-dark'>{status_text}</span>"
    else: return f"<span>{status_text}</span>"

# =====================================================================
# DRILL-DOWN POP-UP DIALOGS
# =====================================================================
@st.dialog("📥 Daily Gate Details & Audit Trail", width="large")
def view_daily_inbound_dialog(date_str):
    records = [t for t in st.session_state["transactions"] if t.get("Date") == date_str and t.get("Status") == "Completed"]
    if not records: st.info("No records for today.")
    else:
        rows = "".join([f"<tr><td>{t.get('Transaction_Type', 'Inbound')}</td><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Vehicle_No','')}</td><td>{t.get('QC_Time','-')}</td><td>{t.get('Tare_Time','-')}</td><td>{t.get('Gross_Time','-')}</td><td style='font-weight:600;'>{t.get('Net_Weight', 0):,.0f} kg</td></tr>" for t in reversed(records)])
        render_table(["Type", "Gate Pass", "Vehicle", "QC Check", "Tare Wt", "Gross Wt", "Net Wt"], rows)

@st.dialog("🚛 Active Vehicles in Plant", width="large")
def view_active_vehicles_dialog(date_str):
    records = [t for t in st.session_state["transactions"] if t.get("Date") == date_str and t.get("Status") not in ["Completed", "QC Rejected"]]
    if not records: st.info("No active vehicles right now.")
    else:
        rows = "".join([f"<tr><td>{t.get('Transaction_Type', 'Inbound')}</td><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Vehicle_No','')}</td><td>{t.get('Material', t.get('Feed_Name','-'))}</td><td>{format_status(t.get('Status',''))}</td></tr>" for t in reversed(records)])
        render_table(["Type", "Gate Pass", "Vehicle No", "Item", "Current Status"], rows)

@st.dialog("✏️ Edit Production Record", width="large")
def edit_production_dialog(invoice_id):
    curr_rec = next((item for item in st.session_state["production"] if item["Invoice"] == invoice_id), None)
    if not curr_rec: return
    c1, c2 = st.columns(2)
    new_out_qty = c1.number_input("Final Output Qty (kg)", value=float(curr_rec.get("Out_Qty_kg", 0)))
    new_bags = c2.number_input("Total Bags Packed", value=int(curr_rec.get("Bags", 0)))
    
    if st.button("Save Corrections", type="primary", use_container_width=True):
        update_payload = {"Out_Qty_kg": new_out_qty, "Bags": new_bags}
        if update_table("production", "Invoice", invoice_id, update_payload):
            curr_rec.update(update_payload); st.rerun()

# --- LOGIN ---
def login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(LOGO_FILE):
            with open(LOGO_FILE, "rb") as img_file:
                b64_logo = base64.b64encode(img_file.read()).decode()
            st.markdown(f"""<div style="display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 25px; margin-top: 50px;"><img src="data:image/png;base64,{b64_logo}" width="65"><h1 style="margin: 0; font-size: 32px; color: #111827;">KJL Poultries Pvt Ltd</h1></div>""", unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='text-align: center; margin-bottom: 25px; margin-top: 50px; color: #111827;'>KJL Poultries Pvt Ltd</h1>", unsafe_allow_html=True)
        with st.form("login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Login") and user in st.session_state["users"] and st.session_state["users"][user]["password"] == pwd:
                st.session_state["logged_in"] = True
                st.session_state["role"] = st.session_state["users"][user]["role"]
                st.session_state["username"] = user
                st.rerun()

# --- DASHBOARD ROUTER ---
def dashboard():
    role = st.session_state["role"]
    inventory, finished_goods = calculate_inventory()
    
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, "rb") as img_file:
            b64_logo = base64.b64encode(img_file.read()).decode()
        st.sidebar.markdown(f"""<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px; margin-top: 10px;"><img src="data:image/png;base64,{b64_logo}" width="45"><h1 style="margin: 0; font-size: 22px; color: #1B5E20 !important;">KJL Poultries</h1></div>""", unsafe_allow_html=True)
        
    st.sidebar.markdown(f"**👤 {st.session_state['users'][st.session_state['username']]['name']}**")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state["logged_in"] = False; st.rerun()

    if role == "Admin":
        st.sidebar.markdown("<br><p style='color:#6B7280; font-size:12px; font-weight:bold; margin-bottom:5px; text-transform:uppercase;'>General Menu</p>", unsafe_allow_html=True)
        admin_nav = st.sidebar.radio("Navigation", ["📊 Dashboard Overview", "🏭 Feed Production", "🚚 Feed Dispatch & Loading", "📦 Warehouse & Stock", "📜 Transaction Records", "👥 User Management", "🗂️ Master Data"], label_visibility="collapsed")

        if admin_nav == "📊 Dashboard Overview":
            st.markdown("<h2 style='color:#111827;'>Operations Dashboard</h2>", unsafe_allow_html=True)
            tab_ops, tab_sc = st.tabs(["1️⃣ Executive Operations Pulse", "2️⃣ Supply Chain Logistics"])
            today_str = get_ist_now().strftime("%d-%m-%Y")
            today_tx = [t for t in st.session_state["transactions"] if t.get("Date") == today_str]
            today_prod = [p for p in st.session_state["production"] if p.get("Date") == today_str]
            
            total_qty_in = sum([t.get("Net_Weight", 0) for t in today_tx if t.get("Status") == "Completed" and t.get("Transaction_Type") == "Inbound"])
            total_qty_out = sum([t.get("Net_Weight", 0) for t in today_tx if t.get("Status") == "Completed" and t.get("Transaction_Type") == "Outbound"])
            total_prod = sum([p.get("Out_Qty_kg", 0)/1000 for p in today_prod])
            active_tx = [t for t in today_tx if t.get("Status") not in ["Completed", "QC Rejected"]]

            with tab_ops:
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Daily Inbound (kg)", f"{total_qty_in:,.0f}")
                    if st.button("🔍 View Details", key="btn_in", use_container_width=True): view_daily_inbound_dialog(today_str)
                with c2:
                    st.metric("Daily Production (Tons)", f"{total_prod:,.1f}")
                with c3:
                    st.metric("Daily Outbound (Tons)", f"{total_qty_out/1000:,.1f}")
                with c4:
                    st.metric("Active Vehicles", len(active_tx))
                    if st.button("🔍 View Details", key="btn_act", use_container_width=True): view_active_vehicles_dialog(today_str)
                st.divider()

            with tab_sc:
                st.markdown("**Live Warehouse Capacity Indicators (Max 100,000 kg)**")
                c1, c2, c3, c4 = st.columns(4)
                mats = list(inventory.keys())[:4]
                cols = [c1, c2, c3, c4]
                for i, mat in enumerate(mats):
                    with cols[i]:
                        qty = inventory[mat]; pct = min(qty / 100000.0, 1.0)
                        st.markdown(f"**{mat} Stock**"); st.progress(pct)
                        if pct < 0.15: st.markdown(f"<span style='color:#DC2626; font-weight:600;'>⚠️ {qty:,.0f} kg (Reorder!)</span>", unsafe_allow_html=True)
                        else: st.markdown(f"<span style='color:#6B7280;'>{qty:,.0f} / 100,000 kg</span>", unsafe_allow_html=True)

        elif admin_nav == "🏭 Feed Production":
            st.markdown("<h2 style='color:#111827;'>Feed Production & Costing</h2>", unsafe_allow_html=True)
            tab_list, tab_form = st.tabs(["Feed Production List", "Add New Production"])
            
            with tab_list:
                if not st.session_state["production"]: st.info("No records found.")
                else:
                    c1, c2, c3 = st.columns([3, 2, 5])
                    with c1: sel_inv = st.selectbox("Select Invoice:", [p["Invoice"] for p in reversed(st.session_state["production"])], label_visibility="collapsed")
                    with c2: 
                        if st.button("✏️ Quick Edit", use_container_width=True) and sel_inv: edit_production_dialog(sel_inv)
                    rows = "".join([f"<tr><td>{p.get('Date','')}</td><td style='font-weight:600;'>{p.get('Invoice','')}</td><td>{p.get('Formula','')}</td><td>{p.get('Feed_Name','')}</td><td>{p.get('In_Qty_kg',0):,.0f}</td><td>{p.get('Out_Qty_kg',0):,.0f}</td><td>{p.get('Bags',0)}</td><td style='text-align:center;'>{get_print_link(p, 'PROD')}</td></tr>" for p in reversed(st.session_state["production"])])
                    render_table(["Date", "Invoice", "Formula", "Item", "In Qty", "Out Qty", "Bags", "Print"], rows)

            with tab_form:
                c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1.5, 1.5, 1.5])
                with c1: p_date = st.date_input(f"Date *", get_ist_now().date())
                with c2: p_dc = st.text_input("Dc No.")
                with c3: p_loc = st.selectbox("Feed Mill *", st.session_state["locations"])
                with c4: p_feed = st.selectbox("Feed Name *", st.session_state["feed_names"])
                with c5: p_form = st.selectbox("Formula *", list(st.session_state["bom"].keys()))
                p_tons = st.number_input("Tons *", min_value=0.1, step=1.0, value=1.0)
                
                prod_kg = p_tons * 1000
                if st.button("✔️ Save Production Record", type="primary"):
                    next_inv_num = get_next_id(st.session_state["production"], "Invoice")
                    new_data = {
                        "Date": p_date.strftime("%d.%m.%Y"),
                        "Invoice": f"FMP-{get_ist_now().strftime('%m%y')}-{next_inv_num}",
                        "Formula": p_form, "Feed_Name": p_feed, "Location": p_loc,
                        "In_Qty_kg": prod_kg, "Out_Qty_kg": prod_kg, "Bags": int(prod_kg/50)
                    }
                    if insert_table("production", new_data):
                        st.session_state["production"].append(new_data)
                        st.success("✅ Recorded Successfully!"); time.sleep(1); st.rerun()

        elif admin_nav == "🚚 Feed Dispatch & Loading":
            st.markdown("<h2 style='color:#111827;'>Loading Supervisor Desk</h2>", unsafe_allow_html=True)
            
            st.markdown("<p style='font-weight:600; color:#374151;'>Current Finished Feed Inventory (Tons)</p>", unsafe_allow_html=True)
            if not finished_goods: st.info("No finished goods in inventory.")
            else:
                fg_cols = st.columns(max(1, len(finished_goods)))
                for idx, (feed, qty) in enumerate(finished_goods.items()):
                    fg_cols[idx % len(fg_cols)].metric(label=f"{feed}", value=f"{qty:,.2f} Tons")
            st.divider()

            pending_load = [t for t in st.session_state["transactions"] if t.get("Status") == "Loading" and t.get("Transaction_Type") == "Outbound"]
            if not pending_load:
                st.success("🎉 No trucks currently waiting for loading!")
            else:
                st.markdown("<p style='font-weight:600; color:#DC2626;'>🚨 Action Required: Load Vehicles</p>", unsafe_allow_html=True)
                load_gp = st.selectbox("Select Empty Vehicle to Load", [format_vehicle_label(t) for t in pending_load]).split(" - ")[0]
                t_load = next((t for t in pending_load if t.get("Gate_Pass_ID") == load_gp), None)
                
                st.info(f"🚚 Empty Tare Weight Confirmed: **{t_load.get('Tare_Weight', 0)} kg**")
                
                with st.form("loading_form", clear_on_submit=False):
                    c1, c2, c3 = st.columns(3)
                    
                    default_feed = t_load.get("Material", "FEED")
                    feed_idx = st.session_state["feed_names"].index(default_feed) if default_feed in st.session_state["feed_names"] else 0
                    
                    with c1: feed_type = st.selectbox("Feed Being Loaded", st.session_state["feed_names"], index=feed_idx if st.session_state["feed_names"] else 0)
                    with c2: dest = st.selectbox("Destination", st.session_state["locations"])
                    with c3: bags = st.number_input("Total Bags Loaded", min_value=1, step=1)
                    
                    st.markdown("**Photographic Proof (Up to 10 images allowed)**")
                    uploaded_photos = st.file_uploader("Capture or upload photos of the loaded truck lines 📸", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
                    
                    if st.form_submit_button("Complete Loading & Send to Final Weighbridge", type="primary"):
                        if not uploaded_photos:
                            st.error("⚠️ You must upload at least one photo of the loaded truck to proceed!")
                        elif len(uploaded_photos) > 10:
                            st.error("⚠️ You can only upload a maximum of 10 photos per dispatch.")
                        else:
                            with st.spinner(f"Securely uploading {len(uploaded_photos)} photo(s) to the cloud..."):
                                photo_urls = []
                                for i, photo_file in enumerate(uploaded_photos):
                                    ext = photo_file.name.split('.')[-1].lower()
                                    content_type = f"image/{ext}" if ext in ['png', 'jpeg', 'jpg'] else "image/jpeg"
                                    photo_name = f"{load_gp}_{int(time.time())}_{i}.{ext}"
                                    
                                    p_url = upload_file_to_supabase(photo_file.getvalue(), photo_name, content_type)
                                    if p_url:
                                        photo_urls.append(p_url)
                                
                                if photo_urls:
                                    joined_urls = ",".join(photo_urls)
                                    update_payload = {"Feed_Name": feed_type, "Destination": dest, "Bags": bags, "Photo_URL": joined_urls, "Status": "Pending Gross"}
                                    if update_table("transactions", "Gate_Pass_ID", load_gp, update_payload):
                                        t_load.update(update_payload)
                                        st.success("✅ Truck loaded, photos securely saved, sent to Weighbridge!")
                                        time.sleep(1.5); st.rerun()
                                else:
                                    st.error("❌ Failed to upload photos to Supabase. Make sure you ran the SQL policy.")

        elif admin_nav == "📜 Transaction Records":
            st.markdown("<h2 style='color:#111827;'>Unified Transaction Records</h2>", unsafe_allow_html=True)
            if not st.session_state["transactions"]: st.info("No records.")
            else:
                rows = "".join([f"<tr><td>{t.get('Date','')}</td><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Transaction_Type','')}</td><td>{t.get('Vehicle_No','')}</td><td>{t.get('Material', t.get('Feed_Name','-'))}</td><td>{format_status(t.get('Status',''))}</td><td style='font-weight:600;'>{t.get('Net_Weight', 0):,.0f} kg</td><td style='text-align:center;'>{get_print_link(t, 'OUTBOUND' if t.get('Transaction_Type')=='Outbound' else 'INWARD')}</td><td>{get_photo_links_html(t.get('Photo_URL', ''))}</td></tr>" for t in reversed(st.session_state["transactions"])])
                render_table(["Date", "Pass ID", "Type", "Vehicle", "Product", "Status", "Net Wt", "Print", "Proof"], rows)

        elif admin_nav == "📦 Warehouse & Stock":
            st.markdown("<h2 style='color:#111827;'>Warehouse Inventory</h2>", unsafe_allow_html=True)
            with st.expander("⚖️ Log Physical Inventory Adjustment"):
                with st.form("adj_form", clear_on_submit=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        adj_date = st.date_input("Date", get_ist_now().date())
                        adj_item = st.selectbox("Item", st.session_state["materials"] + st.session_state["feed_names"])
                    with c2:
                        adj_type = st.radio("Adjustment Type", ["Deduction (-)", "Addition (+)"])
                        adj_qty = st.number_input("Quantity (kg)", min_value=0.0, step=10.0)
                    with c3:
                        adj_reason = st.selectbox("Reason", ["Moisture Loss", "Spillage/Wastage", "Audit Correction"])
                    if st.form_submit_button("Apply Adjustment"):
                        new_data = {"Date": adj_date.strftime("%d-%m-%Y"), "Item": adj_item, "Type": adj_type, "Quantity": adj_qty, "Reason": adj_reason}
                        if insert_table("adjustments", new_data):
                            st.session_state["adjustments"].append(new_data)
                            st.success("✅ Adjustment applied!"); time.sleep(1); st.rerun()

        elif admin_nav == "👥 User Management":
            st.markdown("<h2 style='color:#111827;'>User Management Console</h2>", unsafe_allow_html=True)
            with st.form("create_user_form", clear_on_submit=True):
                new_emp_id = st.text_input("Employee ID")
                new_username = st.text_input("System Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Assign Role", ["Admin", "Security", "QC_Lab", "Weighbridge", "Loading_Supervisor"])
                if st.form_submit_button("Create User", type="primary"):
                    st.session_state["users"][new_username] = {"password": new_password, "role": new_role, "name": new_username, "emp_id": new_emp_id}
                    st.success(f"✅ User created!"); st.rerun()

        elif admin_nav == "🗂️ Master Data":
            st.markdown("<h2 style='color:#111827;'>Master Data & Pricing (Cloud Synced)</h2>", unsafe_allow_html=True)
            tab1, tab2, tab3 = st.tabs(["📦 Materials & Costing", "🤝 Suppliers & Locations", "🧪 Feed Formula Builder"])
            with tab1:
                new_material = st.text_input("Add New Material")
                new_mat_cost = st.number_input("Initial Cost (₹/kg)", min_value=0.0)
                if st.button("Add Material") and new_material and new_material.upper() not in st.session_state["materials"]:
                    if insert_table("materials", {"Name": new_material.upper(), "Cost": new_mat_cost}):
                        st.session_state["materials"].append(new_material.upper())
                        st.session_state["material_costs"][new_material.upper()] = new_mat_cost
                        st.success("✅ Saved!"); time.sleep(1); st.rerun()
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    new_vendor = st.text_input("Add New Vendor")
                    if st.button("Add Vendor") and new_vendor and new_vendor not in st.session_state["vendors"]:
                        if insert_table("vendors", {"Name": new_vendor}):
                            st.session_state["vendors"].append(new_vendor); st.success("✅ Saved!"); time.sleep(1); st.rerun()
                with col2:
                    new_loc = st.text_input("Add New Farm / Customer")
                    if st.button("Add Location") and new_loc and new_loc not in st.session_state["locations"]:
                        if insert_table("locations", {"Name": new_loc}):
                            st.session_state["locations"].append(new_loc); st.success("✅ Saved!"); time.sleep(1); st.rerun()
            with tab3:
                reset_key = st.session_state["formula_reset_key"]
                new_formula_name = st.text_input("Formula Name", key=f"fname_{reset_key}")
                selected_ingredients = st.multiselect("Select Ingredients", st.session_state["materials"], key=f"fings_{reset_key}")
                if selected_ingredients:
                    quantities = {}
                    total_kg = 0.0
                    for ing in selected_ingredients:
                        c1, c2 = st.columns([2, 1])
                        with c1: st.write(f"**{ing}**")
                        with c2:
                            val = st.number_input(f"kg", min_value=0.0, max_value=1000.0, step=10.0, key=f"kg_{ing}_{reset_key}", label_visibility="collapsed")
                            quantities[ing] = val; total_kg += val
                    if total_kg == 1000.0:
                        if st.button("✔️ Save Feed Formula", type="primary"):
                            recipe = {k: v / 1000.0 for k, v in quantities.items()}
                            if insert_table("bom", {"Formula_Name": new_formula_name, "Recipe": recipe}):
                                st.session_state["bom"][new_formula_name] = recipe
                                st.session_state["formula_reset_key"] += 1
                                st.success("✅ Formula saved to cloud!"); time.sleep(1); st.rerun()
                    else: st.error(f"Total: {total_kg:,.0f} / 1,000 kg")

# --- LOADING SUPERVISOR DEDICATED PANEL ---
    elif role == "Loading_Supervisor":
        st.markdown("<h2 style='color:#111827;'>Loading Supervisor Desk</h2>", unsafe_allow_html=True)
            
        st.markdown("<p style='font-weight:600; color:#374151;'>Current Finished Feed Inventory (Tons)</p>", unsafe_allow_html=True)
        if not finished_goods: st.info("No finished goods in inventory.")
        else:
            fg_cols = st.columns(max(1, len(finished_goods)))
            for idx, (feed, qty) in enumerate(finished_goods.items()):
                fg_cols[idx % len(fg_cols)].metric(label=f"{feed}", value=f"{qty:,.2f} Tons")
        st.divider()

        pending_load = [t for t in st.session_state["transactions"] if t.get("Status") == "Loading" and t.get("Transaction_Type") == "Outbound"]
        if not pending_load:
            st.success("🎉 No trucks currently waiting for loading!")
        else:
            st.markdown("<p style='font-weight:600; color:#DC2626;'>🚨 Action Required: Load Vehicles</p>", unsafe_allow_html=True)
            load_gp = st.selectbox("Select Empty Vehicle to Load", [format_vehicle_label(t) for t in pending_load]).split(" - ")[0]
            t_load = next((t for t in pending_load if t.get("Gate_Pass_ID") == load_gp), None)
            
            st.info(f"🚚 Empty Tare Weight Confirmed: **{t_load.get('Tare_Weight', 0)} kg**")
            
            with st.form("loading_form_dedicated", clear_on_submit=False):
                c1, c2, c3 = st.columns(3)
                
                default_feed = t_load.get("Material", "FEED")
                feed_idx = st.session_state["feed_names"].index(default_feed) if default_feed in st.session_state["feed_names"] else 0
                
                with c1: feed_type = st.selectbox("Feed Being Loaded", st.session_state["feed_names"], index=feed_idx if st.session_state["feed_names"] else 0)
                with c2: dest = st.selectbox("Destination", st.session_state["locations"])
                with c3: bags = st.number_input("Total Bags Loaded", min_value=1, step=1)
                
                st.markdown("**Photographic Proof (Up to 10 images allowed)**")
                uploaded_photos = st.file_uploader("Capture or upload photos of the loaded truck lines 📸", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
                
                if st.form_submit_button("Complete Loading & Send to Final Weighbridge", type="primary"):
                    if not uploaded_photos:
                        st.error("⚠️ You must upload at least one photo of the loaded truck to proceed!")
                    elif len(uploaded_photos) > 10:
                        st.error("⚠️ You can only upload a maximum of 10 photos per dispatch.")
                    else:
                        with st.spinner(f"Securely uploading {len(uploaded_photos)} photo(s) to the cloud..."):
                            photo_urls = []
                            for i, photo_file in enumerate(uploaded_photos):
                                ext = photo_file.name.split('.')[-1].lower()
                                content_type = f"image/{ext}" if ext in ['png', 'jpeg', 'jpg'] else "image/jpeg"
                                photo_name = f"{load_gp}_{int(time.time())}_{i}.{ext}"
                                
                                p_url = upload_file_to_supabase(photo_file.getvalue(), photo_name, content_type)
                                if p_url:
                                    photo_urls.append(p_url)
                            
                            if photo_urls:
                                joined_urls = ",".join(photo_urls)
                                update_payload = {"Feed_Name": feed_type, "Destination": dest, "Bags": bags, "Photo_URL": joined_urls, "Status": "Pending Gross"}
                                if update_table("transactions", "Gate_Pass_ID", load_gp, update_payload):
                                    t_load.update(update_payload)
                                    st.success("✅ Truck loaded, photos securely saved, sent to Weighbridge!")
                                    time.sleep(1.5); st.rerun()
                            else:
                                st.error("❌ Failed to upload photos to Supabase. Make sure you ran the SQL policy.")

# --- GATE SECURITY ---
    elif role == "Security":
        st.markdown("<h2 style='color:#111827;'>Gate Security Panel</h2>", unsafe_allow_html=True)
        tab_action, tab_history = st.tabs(["📝 Register Vehicle Arrival", "📅 Daily Registration Log"])
        
        with tab_action:
            direction = st.radio("Vehicle Purpose", ["📥 Inbound (Raw Material Delivery)", "📤 Outbound (Feed Dispatch)"], horizontal=True)
            
            with st.form("vehicle_entry_form", clear_on_submit=True):
                vehicle_no = st.text_input("Vehicle Number *")
                
                if "Inbound" in direction:
                    material = st.selectbox("Material Delivering", st.session_state["materials"])
                    vendor = st.selectbox("Vendor Name", st.session_state["vendors"])
                else:
                    out_mats = ["FEED"] + [x for x in st.session_state["feed_names"] if x != "FEED"]
                    out_parties = ["KJL"] + [x for x in st.session_state["vendors"] + st.session_state["locations"] if x != "KJL"]
                    
                    material = st.selectbox("Material Type", out_mats)
                    vendor = st.selectbox("Party / Vendor Name", out_parties)
                    st.info("Outbound empty trucks go directly to Weighbridge for Tare Weight. Bypassing QC.")
                    
                if st.form_submit_button("Register Vehicle Arrival", type="primary") and vehicle_no:
                    next_gp_num = get_next_id(st.session_state["transactions"], "Gate_Pass_ID")
                    now_ist = get_ist_now()
                    
                    if "Inbound" in direction:
                        new_data = {"Gate_Pass_ID": f"GP-{next_gp_num}", "Date": now_ist.strftime("%d-%m-%Y"), "Time": now_ist.strftime("%I:%M %p"), "Vehicle_No": vehicle_no.upper(), "Transaction_Type": "Inbound", "Material": material, "Vendor": vendor, "Status": "Pending QC"}
                    else:
                        new_data = {"Gate_Pass_ID": f"GP-{next_gp_num}", "Date": now_ist.strftime("%d-%m-%Y"), "Time": now_ist.strftime("%I:%M %p"), "Vehicle_No": vehicle_no.upper(), "Transaction_Type": "Outbound", "Material": material, "Vendor": vendor, "Status": "Pending Tare"}
                        
                    if insert_table("transactions", new_data):
                        st.session_state["transactions"].append(new_data)
                        st.success("✅ Registered Successfully! View it in the cloud.")
                        time.sleep(1); st.rerun()
                    
        with tab_history:
            filter_date = st.date_input("Select Date", get_ist_now().date(), key="sec_date").strftime("%d-%m-%Y")
            filtered_tx = [t for t in st.session_state["transactions"] if t.get("Date") == filter_date]
            if not filtered_tx: st.info(f"No vehicles registered on {filter_date}.")
            else:
                rows = "".join([f"<tr><td>{t.get('Time','')}</td><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Transaction_Type','')}</td><td>{t.get('Vehicle_No','')}</td><td>{format_status(t.get('Status',''))}</td></tr>" for t in reversed(filtered_tx)])
                render_table(["Time", "Gate Pass", "Type", "Vehicle No", "Status"], rows)

# --- QC LAB ---
    elif role == "QC_Lab":
        st.markdown("<h2 style='color:#111827;'>QC & Lab Testing</h2>", unsafe_allow_html=True)
        tab_action, tab_history = st.tabs(["🧪 Pending QC Tests", "📅 QC Test History"])
        
        with tab_action:
            pending_qc = [t for t in st.session_state["transactions"] if t.get("Status") == "Pending QC" and t.get("Transaction_Type") == "Inbound"]
            if pending_qc:
                selected_gp = st.selectbox("Select Inbound Vehicle", [format_vehicle_label(t) for t in pending_qc]).split(" - ")[0]
                with st.form("qc_form", clear_on_submit=True):
                    qc_decision = st.radio("QC Decision", ["QC Passed", "QC Passed with Rebate", "QC Rejected"])
                    remarks = st.text_area("Remarks / Rebate Details")
                    if st.form_submit_button("Submit QC Results", type="primary"):
                        for t in st.session_state["transactions"]:
                            if t.get("Gate_Pass_ID") == selected_gp:
                                qc_time_str = get_ist_now().strftime("%I:%M %p")
                                if update_table("transactions", "Gate_Pass_ID", t["Gate_Pass_ID"], {"Status": qc_decision, "QC_Remarks": remarks.strip(), "QC_Time": qc_time_str}):
                                    t["Status"] = qc_decision; t["QC_Remarks"] = remarks.strip(); t["QC_Time"] = qc_time_str
                                    st.success("✅ QC Results Submitted"); time.sleep(1); st.rerun() 
            else: st.info("No vehicles pending QC.")
            
        with tab_history:
            filter_date = st.date_input("Select Date", get_ist_now().date(), key="qc_date").strftime("%d-%m-%Y")
            filtered_tx = [t for t in st.session_state["transactions"] if t.get("Date") == filter_date and t.get("Status") != "Pending QC" and t.get("Transaction_Type") == "Inbound"]
            if not filtered_tx: st.info(f"No QC tests completed on {filter_date}.")
            else:
                rows = "".join([f"<tr><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Vehicle_No','')}</td><td>{t.get('Material','')}</td><td>{format_status(t.get('Status',''))}</td><td>{t.get('QC_Remarks','')}</td></tr>" for t in reversed(filtered_tx)])
                render_table(["Gate Pass", "Vehicle No", "Material", "QC Decision", "Remarks"], rows)

# --- WEIGHBRIDGE ---
    elif role == "Weighbridge":
        st.markdown("<h2 style='color:#111827;'>Unified Weighbridge Operations</h2>", unsafe_allow_html=True)
        tab_gross, tab_tare, tab_history = st.tabs(["🔴 Weigh In (Gross Weight)", "🔵 Weigh Out (Tare Weight)", "📅 Log"])
        
        with tab_gross:
            st.info("Log **GROSS (Loaded)** weight here. Inbound trucks do this FIRST. Outbound trucks do this LAST.")
            pending_gross = [t for t in st.session_state["transactions"] if (t.get("Transaction_Type", "Inbound") == "Inbound" and t.get("Status") in ["QC Passed", "QC Passed with Rebate"]) or (t.get("Transaction_Type") == "Outbound" and t.get("Status") == "Pending Gross")]
            if pending_gross:
                gp_gross = st.selectbox("Select Loaded Vehicle", [format_vehicle_label(t) for t in pending_gross], key="sgross").split(" - ")[0]
                t_gross = next(t for t in pending_gross if t.get("Gate_Pass_ID") == gp_gross)
                
                with st.form("gross_form", clear_on_submit=True):
                    if t_gross.get("Transaction_Type") == "Outbound":
                        st.markdown(f"**Empty Tare Weight was:** {t_gross.get('Tare_Weight',0)} kg")
                    gross_wt = st.number_input("Gross Weight (kg)", min_value=0.0, step=10.0)
                    
                    if st.form_submit_button("Save Gross Weight", type="primary") and gross_wt > 0:
                        gross_time_str = get_ist_now().strftime("%I:%M %p")
                        update_payload = {"Gross_Weight": gross_wt, "Gross_Time": gross_time_str}
                        
                        if t_gross.get("Transaction_Type", "Inbound") == "Inbound":
                            update_payload["Status"] = "Unloading"
                        else: # Outbound completing
                            update_payload["Status"] = "Completed"
                            if "Tare_Weight" in t_gross and t_gross["Tare_Weight"] > 0:
                                update_payload["Net_Weight"] = gross_wt - t_gross["Tare_Weight"]
                                
                        if update_table("transactions", "Gate_Pass_ID", gp_gross, update_payload):
                            t_gross.update(update_payload)
                            st.success("✅ Gross Weight Saved!"); time.sleep(1); st.rerun()
            else: st.info("No loaded vehicles waiting.")

        with tab_tare:
            st.info("Log **TARE (Empty)** weight here. Inbound trucks do this LAST. Outbound trucks do this FIRST.")
            pending_tare = [t for t in st.session_state["transactions"] if (t.get("Transaction_Type", "Inbound") == "Inbound" and t.get("Status") == "Unloading") or (t.get("Transaction_Type") == "Outbound" and t.get("Status") == "Pending Tare")]
            
            if pending_tare:
                gp_tare = st.selectbox("Select Empty Vehicle", [format_vehicle_label(t) for t in pending_tare], key="stare").split(" - ")[0]
                t_tare = next(t for t in pending_tare if t.get("Gate_Pass_ID") == gp_tare)
                
                with st.form("tare_form", clear_on_submit=True):
                    if t_tare.get("Transaction_Type", "Inbound") == "Inbound":
                        st.markdown(f"**Loaded Gross Weight was:** {t_tare.get('Gross_Weight',0)} kg")
                    tare_wt = st.number_input("Tare Weight (kg)", min_value=0.0, step=10.0)
                    
                    if st.form_submit_button("Save Tare Weight", type="primary") and tare_wt > 0:
                        tare_time_str = get_ist_now().strftime("%I:%M %p")
                        update_payload = {"Tare_Weight": tare_wt, "Tare_Time": tare_time_str}
                        
                        if t_tare.get("Transaction_Type", "Inbound") == "Inbound":
                            if tare_wt < t_tare.get("Gross_Weight", 0):
                                update_payload["Status"] = "Completed"
                                update_payload["Net_Weight"] = t_tare["Gross_Weight"] - tare_wt
                            else: st.error("Tare cannot be greater than Gross!")
                        else: # Outbound starting
                            update_payload["Status"] = "Loading"
                            
                        if update_table("transactions", "Gate_Pass_ID", gp_tare, update_payload):
                            t_tare.update(update_payload)
                            st.success("✅ Tare Weight Saved!"); time.sleep(1); st.rerun()
            else: st.info("No empty vehicles waiting.")
                                    
        with tab_history:
            filter_date = st.date_input("Select Date", get_ist_now().date(), key="wb_date").strftime("%d-%m-%Y")
            filtered_tx = [t for t in st.session_state["transactions"] if t.get("Date") == filter_date and (t.get("Gross_Weight", 0) > 0 or t.get("Tare_Weight", 0) > 0)]
            if not filtered_tx: st.info(f"No weighments on {filter_date}.")
            else:
                rows = "".join([f"<tr><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Transaction_Type','')}</td><td>{t.get('Vehicle_No','')}</td><td>{t.get('Gross_Weight',0)}</td><td>{t.get('Tare_Weight',0)}</td><td style='font-weight:600;'>{t.get('Net_Weight',0)}</td><td>{format_status(t.get('Status',''))}</td></tr>" for t in reversed(filtered_tx)])
                render_table(["Pass", "Type", "Vehicle", "Gross(kg)", "Tare(kg)", "Net(kg)", "Status"], rows)

# --- APP EXECUTION ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if not st.session_state["logged_in"]: login()
else: dashboard()
