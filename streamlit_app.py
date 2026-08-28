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

# --- CUSTOM CSS (MODERN SAAS UI & CUSTOM STATUS COLORS) ---
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
    
    /* Dynamic Color Status Badges */
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
    
    div[data-testid="stVerticalBlock"] > div { margin-bottom: -5px; }
    .dense-label { font-size: 13px; font-weight: 600; color: #374151; margin-top: 10px; }
    .req { color: #DC2626; }
    .blue-header { background-color: #1B5E20; color: white; text-align: center; font-weight: bold; padding: 8px; font-size: 14px; margin-top: 15px; margin-bottom: 10px; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# --- CLOUD DATABASE ENGINE (REQUESTS API) ---
DB_URL = "https://ejbgjfhdotsgpivkvics.supabase.co/rest/v1"
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
        if method == "GET":
            response = requests.get(url, headers=DB_HEADERS)
        elif method == "POST":
            response = requests.post(url, headers=DB_HEADERS, json=payload)
        elif method == "PATCH":
            response = requests.patch(url, headers=DB_HEADERS, json=payload)
            
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

def insert_table(table_name, payload): 
    res = _db_call("POST", table_name, payload)
    return res is not None

def update_table(table_name, pk_col, pk_val, payload): 
    res = _db_call("PATCH", f"{table_name}?{pk_col}=eq.{pk_val}", payload)
    return res is not None

# --- INITIALIZE APP STATE & SYNC DATABASE ---
if "db_synced" not in st.session_state:
    st.session_state["transactions"] = fetch_table("transactions")
    st.session_state["production"] = fetch_table("production")
    st.session_state["dispatches"] = fetch_table("dispatches")
    st.session_state["adjustments"] = fetch_table("adjustments")
    
    # Fetching live master data
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
        "wb": {"password": "123", "role": "Weighbridge", "name": "Scale Operator", "emp_id": "KJL-004"}
    }

LOGO_FILE = "Logo png.png"

# --- HELPER FUNCTIONS ---
def get_next_id(data_list, id_key):
    # Safely finds the highest existing ID number and adds 1
    max_id = 1000
    for item in data_list:
        val = item.get(id_key, "")
        try:
            num = int(val.split("-")[-1])
            if num > max_id: 
                max_id = num
        except: 
            pass
    return max_id + 1

def calculate_inventory():
    inventory = {mat: 50000.0 for mat in st.session_state["materials"]} 
    finished_goods = {feed: 0.0 for feed in st.session_state["feed_names"]}
    for t in st.session_state["transactions"]:
        if t.get("Status") == "Completed" and "Net_Weight" in t and t.get("Material") in inventory: 
            inventory[t["Material"]] += t.get("Net_Weight", 0)
    for p in st.session_state["production"]:
        form = p.get("Formula", "")
        if form in st.session_state["bom"]:
            recipe = st.session_state["bom"][form]
            in_qty = p.get("In_Qty_kg", 0)
            for mat, pct in recipe.items():
                if mat in inventory: inventory[mat] -= (in_qty * pct)
            feed_n = p.get("Feed_Name", "")
            if feed_n in finished_goods: finished_goods[feed_n] += (p.get("Out_Qty_kg", 0) / 1000)
    for d in st.session_state["dispatches"]:
        feed_n = d.get("Feed_Type", "")
        if feed_n in finished_goods: finished_goods[feed_n] -= d.get("Quantity_Tons", 0)
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
        html = f"""<!DOCTYPE html><html><body onload="window.print()" style="font-family: monospace; padding: 20px;"><div style="border: 2px dashed #333; padding: 30px; max-width: 400px; margin: 0 auto;">{logo_img_tag}<h2 style="text-align: center; margin-top: 0;">KJL POULTRIES PVT LTD</h2><h3 style="text-align: center;">DELIVERY CHALLAN</h3><hr><p><b>ID:</b> {data_dict.get('Dispatch_ID', '')} | <b>Date:</b> {data_dict.get('Date', '')}</p><p><b>Vehicle:</b> {data_dict.get('Vehicle_No', '')} | <b>Dest:</b> {data_dict.get('Destination', '')}</p><hr><p><b>Feed:</b> {data_dict.get('Feed_Type', '')}</p><p style="font-size: 18px;"><b>BAGS: {data_dict.get('Bag_Count', 0)}</b></p></div></body></html>"""
    b64 = base64.b64encode(html.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" target="_blank" style="text-decoration: none; font-size: 18px; filter: grayscale(100%);" title="Print in New Tab">🖨️</a>'

def render_table(headers, rows_html):
    st.markdown(f"<div class='custom-table-container'><table class='custom-table'><thead><tr>{''.join([f'<th>{h}</th>' for h in headers])}</tr></thead><tbody>{rows_html}</tbody></table></div>", unsafe_allow_html=True)

def format_status(status_text):
    if status_text == "Pending QC": return f"<span class='status-blue'>{status_text}</span>"
    elif status_text in ["QC Passed", "QC Passed with Rebate"]: return f"<span class='status-green'>{status_text}</span>"
    elif status_text == "QC Rejected": return f"<span class='status-red'>{status_text}</span>"
    elif status_text == "Unloading": return f"<span class='status-orange'>{status_text}</span>"
    elif status_text == "Completed": return f"<span class='status-dark'>{status_text}</span>"
    else: return f"<span>{status_text}</span>"

# =====================================================================
# DRILL-DOWN POP-UP DIALOGS
# =====================================================================
@st.dialog("📥 Daily Inbound Details", width="large")
def view_daily_inbound_dialog(date_str):
    records = [t for t in st.session_state["transactions"] if t.get("Date") == date_str and t.get("Status") == "Completed"]
    if not records: st.info("No inbound records for today.")
    else:
        rows = "".join([f"<tr><td>{t.get('Time','')}</td><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Material','')}</td><td>{t.get('Vehicle_No','')}</td><td style='font-weight:600;'>{t.get('Net_Weight', 0):,.0f} kg</td><td>{t.get('Vendor','')}</td></tr>" for t in reversed(records)])
        render_table(["Time", "Gate Pass", "Material", "Vehicle", "Net Wt", "Vendor"], rows)

@st.dialog("🚛 Active Vehicles in Plant", width="large")
def view_active_vehicles_dialog(date_str):
    records = [t for t in st.session_state["transactions"] if t.get("Date") == date_str and t.get("Status") not in ["Completed", "QC Rejected"]]
    if not records: st.info("No active vehicles right now.")
    else:
        rows = "".join([f"<tr><td>{t.get('Time','')}</td><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Vehicle_No','')}</td><td>{t.get('Material','')}</td><td>{format_status(t.get('Status',''))}</td></tr>" for t in reversed(records)])
        render_table(["Entry Time", "Gate Pass", "Vehicle No", "Material", "Current Status"], rows)

@st.dialog("🏭 Daily Production Details", width="large")
def view_daily_production_dialog(date_str):
    records = [p for p in st.session_state["production"] if p.get("Date") == date_str]
    if not records: st.info("No production records for today.")
    else:
        rows = "".join([f"<tr><td style='font-weight:600;'>{p.get('Invoice','')}</td><td>{p.get('Feed_Name','')}</td><td>{p.get('Formula','')}</td><td style='font-weight:600;'>{p.get('Out_Qty_kg',0):,.0f} kg</td><td>{p.get('Bags',0)}</td><td>₹{p.get('Total_Amount',0):,.2f}</td></tr>" for p in reversed(records)])
        render_table(["Invoice", "Feed", "Formula", "Output", "Bags", "Total Cost"], rows)

@st.dialog("🚚 Daily Dispatch Details", width="large")
def view_daily_dispatch_dialog(date_str):
    records = [d for d in st.session_state["dispatches"] if d.get("Date") == date_str]
    if not records: st.info("No dispatch records for today.")
    else:
        rows = "".join([f"<tr><td>{d.get('Time','')}</td><td style='font-weight:600;'>{d.get('Dispatch_ID','')}</td><td>{d.get('Feed_Type','')}</td><td>{d.get('Vehicle_No','')}</td><td style='font-weight:600;'>{d.get('Quantity_Tons', 0)} Tons</td><td>{d.get('Destination','')}</td></tr>" for d in reversed(records)])
        render_table(["Time", "DC No.", "Feed", "Vehicle", "Quantity", "Destination"], rows)

@st.dialog("✏️ Edit Production Record", width="large")
def edit_production_dialog(invoice_id):
    curr_rec = next((item for item in st.session_state["production"] if item["Invoice"] == invoice_id), None)
    if not curr_rec: return
    c1, c2 = st.columns(2)
    new_out_qty = c1.number_input("Final Output Qty (kg)", value=float(curr_rec.get("Out_Qty_kg", 0)))
    new_bags = c2.number_input("Total Bags Packed", value=int(curr_rec.get("Bags", 0)))
    
    st.markdown("<div class='blue-header'>Update Cost Overheads</div>", unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    c_lab = e1.number_input("Labour (₹)", value=float(curr_rec.get("Cost_Lab", 0.0)))
    c_pac = e2.number_input("Packing (₹)", value=float(curr_rec.get("Cost_Pac", 0.0)))
    c_ele = e3.number_input("Electrical (₹)", value=float(curr_rec.get("Cost_Ele", 0.0)))
    e4, e5, e6 = st.columns(3)
    c_tra = e4.number_input("Transport (₹)", value=float(curr_rec.get("Cost_Tra", 0.0)))
    c_bag = e5.number_input("Bag Cost (₹)", value=float(curr_rec.get("Cost_Bag", 0.0)))
    c_oth = e6.number_input("Other (₹)", value=float(curr_rec.get("Cost_Oth", 0.0)))
    c_jay = st.number_input("KJL Feeds Expense (₹)", value=float(curr_rec.get("Cost_Jay", 0.0)))
    c_fix = st.number_input("Fixed Cost (₹)", value=float(curr_rec.get("Cost_Fix", 0.0)))
    
    if st.button("Save Corrections", type="primary", use_container_width=True):
        plant_expenses = c_lab + c_pac + c_ele + c_tra + c_bag + c_oth + c_jay
        grand_total = float(curr_rec.get("RM_Cost", 0)) + plant_expenses
        price_per_kg = grand_total / new_out_qty if new_out_qty > 0 else 0
        update_payload = {"Out_Qty_kg": new_out_qty, "Bags": new_bags, "Cost_Lab": c_lab, "Cost_Pac": c_pac, "Cost_Ele": c_ele, "Cost_Tra": c_tra, "Cost_Bag": c_bag, "Cost_Oth": c_oth, "Cost_Jay": c_jay, "Cost_Fix": c_fix, "Plant_Expenses": plant_expenses, "Total_Amount": grand_total, "Price_Per_Kg": price_per_kg}
        if update_table("production", "Invoice", invoice_id, update_payload):
            curr_rec.update(update_payload); st.rerun()

@st.dialog("✏️ Edit Inbound Record")
def edit_inbound_dialog(gp_id):
    t_edit = next((item for item in st.session_state["transactions"] if item.get("Gate_Pass_ID") == gp_id), None)
    if not t_edit: return
    status_list = ["Pending QC", "QC Passed", "QC Passed with Rebate", "QC Rejected", "Unloading", "Completed"]
    curr_idx = status_list.index(t_edit['Status']) if t_edit['Status'] in status_list else 0
    new_status = st.selectbox("Status", status_list, index=curr_idx)
    new_gross = st.number_input("Gross Weight (kg)", value=float(t_edit.get("Gross_Weight", 0.0)), step=10.0)
    new_tare = st.number_input("Tare Weight (kg)", value=float(t_edit.get("Tare_Weight", 0.0)), step=10.0)
    if st.button("Save Gate Pass", type="primary"):
        update_payload = {"Status": new_status, "Gross_Weight": new_gross, "Tare_Weight": new_tare}
        if new_gross > 0 and new_tare > 0: update_payload["Net_Weight"] = new_gross - new_tare
        if update_table("transactions", "Gate_Pass_ID", gp_id, update_payload):
            t_edit.update(update_payload); st.rerun()

@st.dialog("✏️ Edit Dispatch Record")
def edit_outbound_dialog(dc_id):
    d_edit = next((item for item in st.session_state["dispatches"] if item.get("Dispatch_ID") == dc_id), None)
    if not d_edit: return
    new_veh = st.text_input("Vehicle Number", value=d_edit.get("Vehicle_No", ""))
    dest_idx = st.session_state["locations"].index(d_edit["Destination"]) if d_edit["Destination"] in st.session_state["locations"] else 0
    new_dest = st.selectbox("Destination", st.session_state["locations"], index=dest_idx)
    new_qty = st.number_input("Quantity (Tons)", value=float(d_edit.get("Quantity_Tons", 0.0)), step=1.0)
    if st.button("Save Dispatch", type="primary"):
        bag_size = d_edit.get("Bag_Size", 50)
        update_payload = {"Vehicle_No": new_veh, "Destination": new_dest, "Quantity_Tons": new_qty, "Quantity_kg": new_qty * 1000, "Bag_Count": int((new_qty * 1000) / bag_size)}
        if update_table("dispatches", "Dispatch_ID", dc_id, update_payload):
            d_edit.update(update_payload); st.rerun()

# --- LOGIN ---
def login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(LOGO_FILE):
            with open(LOGO_FILE, "rb") as img_file:
                b64_logo = base64.b64encode(img_file.read()).decode()
            st.markdown(f"""<div style="display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 25px; margin-top: 50px;"><img src="data:image/png;base64,{b64_logo}" width="65"><h1 style="margin: 0; font-size: 32px; color: #111827;">KJL FeedOps</h1></div>""", unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='text-align: center; margin-bottom: 25px; margin-top: 50px; color: #111827;'>KJL FeedOps</h1>", unsafe_allow_html=True)
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
    
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, "rb") as img_file:
            b64_logo = base64.b64encode(img_file.read()).decode()
        st.sidebar.markdown(f"""<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px; margin-top: 10px;"><img src="data:image/png;base64,{b64_logo}" width="45"><h1 style="margin: 0; font-size: 22px; color: #1B5E20 !important;">KJL FeedOps</h1></div>""", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"<h1>KJL FeedOps</h1>", unsafe_allow_html=True)
        
    st.sidebar.markdown(f"**👤 {st.session_state['users'][st.session_state['username']]['name']}**")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state["logged_in"] = False; st.rerun()

    if role == "Admin":
        st.sidebar.markdown("<br><p style='color:#6B7280; font-size:12px; font-weight:bold; margin-bottom:5px; text-transform:uppercase;'>General Menu</p>", unsafe_allow_html=True)
        admin_nav = st.sidebar.radio("Navigation", ["📊 Dashboard Overview", "🏭 Feed Production", "🚚 Feed Dispatch", "📦 Warehouse & Stock", "📜 Transaction Records", "📑 Reports & Exports", "👥 User Management", "🗂️ Master Data"], label_visibility="collapsed")
        inventory, finished_goods = calculate_inventory()

        if admin_nav == "📊 Dashboard Overview":
            st.markdown("<h2 style='color:#111827;'>Operations Dashboard</h2>", unsafe_allow_html=True)
            tab_ops, tab_fin, tab_sc = st.tabs(["1️⃣ Executive Operations Pulse", "2️⃣ Financial & Costing Hub", "3️⃣ Supply Chain Logistics"])
            today_str = datetime.datetime.now().strftime("%d-%m-%Y")
            today_tx = [t for t in st.session_state["transactions"] if t.get("Date") == today_str]
            today_disp = [d for d in st.session_state["dispatches"] if d.get("Date") == today_str]
            today_prod = [p for p in st.session_state["production"] if p.get("Date") == today_str]
            
            total_qty_in = sum([t.get("Net_Weight", 0) for t in today_tx if t.get("Status") == "Completed"])
            total_qty_out = sum([d.get("Quantity_Tons", 0) for d in today_disp])
            total_prod = sum([p.get("Out_Qty_kg", 0)/1000 for p in today_prod])
            active_tx = [t for t in today_tx if t.get("Status") not in ["Completed", "QC Rejected"]]

            with tab_ops:
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Daily Inbound (kg)", f"{total_qty_in:,.0f}")
                    if st.button("🔍 View Details", key="btn_in", use_container_width=True): view_daily_inbound_dialog(today_str)
                with c2:
                    st.metric("Daily Production (Tons)", f"{total_prod:,.1f}")
                    if st.button("🔍 View Details", key="btn_pr", use_container_width=True): view_daily_production_dialog(today_str)
                with c3:
                    st.metric("Daily Dispatch (Tons)", f"{total_qty_out:,.1f}")
                    if st.button("🔍 View Details", key="btn_out", use_container_width=True): view_daily_dispatch_dialog(today_str)
                with c4:
                    st.metric("Active Vehicles", len(active_tx))
                    if st.button("🔍 View Details", key="btn_act", use_container_width=True): view_active_vehicles_dialog(today_str)
                st.divider()
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.markdown("**Recent Production vs. Dispatch Trend**")
                    dates = pd.date_range(end=datetime.date.today(), periods=7)
                    df_trend = pd.DataFrame({'Date': dates, 'Produced': [12, 15, 14, 18, total_prod if total_prod>0 else 16, 15, total_prod], 'Dispatched': [10, 14, 12, 15, total_qty_out if total_qty_out>0 else 14, 13, total_qty_out]}).melt('Date', var_name='Metric', value_name='Tons')
                    area_chart = alt.Chart(df_trend).mark_area(opacity=0.5).encode(x='Date:T', y='Tons:Q', color=alt.Color('Metric:N', scale=alt.Scale(range=['#1B5E20', '#A5D6A7']))).properties(height=300)
                    st.altair_chart(area_chart, use_container_width=True)
                with col_b:
                    st.markdown("**Live Raw Material Distribution**")
                    inv_df = pd.DataFrame(list(inventory.items()), columns=['Material', 'Stock (kg)'])
                    inv_df = inv_df[inv_df['Stock (kg)'] > 0]
                    if not inv_df.empty:
                        donut = alt.Chart(inv_df).mark_arc(innerRadius=50).encode(theta=alt.Theta(field="Stock (kg)", type="quantitative"), color=alt.Color(field="Material", type="nominal", scale=alt.Scale(scheme='greens')), tooltip=['Material', 'Stock (kg)']).properties(height=300)
                        st.altair_chart(donut, use_container_width=True)

            with tab_fin:
                total_inventory_value = sum([qty * st.session_state["material_costs"].get(mat, 0) for mat, qty in inventory.items()])
                c1, c2, c3 = st.columns(3)
                c1.metric("Warehouse Asset Value", f"₹ {total_inventory_value:,.2f}")
                c2.metric("Avg. Production Cost/Kg", f"₹ {sum([p.get('Price_Per_Kg', 0) for p in st.session_state['production']]) / len(st.session_state['production']) if st.session_state['production'] else 0:,.2f}")
                c3.metric("Live Market Materials", len(st.session_state["materials"]))
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
                    rows = "".join([f"<tr><td>{p.get('Date','')}</td><td style='font-weight:600;'>{p.get('Invoice','')}</td><td>{p.get('Formula','')}</td><td>{p.get('Feed_Name','')}</td><td>{p.get('In_Qty_kg',0):,.0f}</td><td>{p.get('Out_Qty_kg',0):,.0f}</td><td>{p.get('Bags',0)}</td><td>₹{p.get('Price_Per_Kg',0):.2f}</td><td style='font-weight:600;'>₹{p.get('Total_Amount',0):,.2f}</td><td>{p.get('Location','')}</td><td style='text-align:center;'>{get_print_link(p, 'PROD')}</td></tr>" for p in reversed(st.session_state["production"])])
                    render_table(["Date", "Invoice", "Formula", "Item", "In Qty", "Out Qty", "Bags", "Price", "Amount", "Location", "Action"], rows)

            with tab_form:
                c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1.5, 1.5, 1.5])
                with c1: p_date = st.date_input(f"Date *", datetime.date.today())
                with c2: p_dc = st.text_input("Dc No.")
                with c3: p_loc = st.selectbox("Feed Mill *", st.session_state["locations"])
                with c4: p_feed = st.selectbox("Feed Name *", st.session_state["feed_names"])
                with c5: p_form = st.selectbox("Formula *", list(st.session_state["bom"].keys()))
                p_tons = st.number_input("Tons *", min_value=0.1, step=1.0, value=1.0)
                
                prod_kg = p_tons * 1000
                recipe = st.session_state["bom"].get(p_form, {})
                rm_total_cost = sum([(prod_kg * pct) * st.session_state["material_costs"].get(mat, 0) for mat, pct in recipe.items()])

                if st.button("✔️ Save Production Record", type="primary"):
                    next_inv_num = get_next_id(st.session_state["production"], "Invoice")
                    new_data = {
                        "Date": p_date.strftime("%d.%m.%Y"),
                        "Invoice": f"FMP-{datetime.datetime.now().strftime('%m%y')}-{next_inv_num}",
                        "Formula": p_form, "Feed_Name": p_feed, "Location": p_loc,
                        "In_Qty_kg": prod_kg, "Out_Qty_kg": prod_kg, "Bags": int(prod_kg/50), "Bag_Size": 50,
                        "Cost_Lab": 0, "Cost_Pac": 0, "Cost_Ele": 0, "Cost_Tra": 0, "Cost_Bag": 0, "Cost_Oth": 0, "Cost_Jay": 0, "Cost_Fix": 0,
                        "Price_Per_Kg": rm_total_cost / prod_kg if prod_kg > 0 else 0, "Total_Amount": rm_total_cost, "RM_Cost": rm_total_cost, "Plant_Expenses": 0
                    }
                    if insert_table("production", new_data):
                        st.session_state["production"].append(new_data)
                        st.success("✅ Recorded Successfully!")
                        time.sleep(1)
                        st.rerun()

        elif admin_nav == "📜 Transaction Records":
            st.markdown("<h2 style='color:#111827;'>Transaction Records</h2>", unsafe_allow_html=True)
            if not st.session_state["transactions"]: st.info("No records.")
            else:
                c1, c2, c3 = st.columns([3, 2, 5])
                with c1: gp_edit = st.selectbox("Select Gate Pass:", [t["Gate_Pass_ID"] for t in reversed(st.session_state["transactions"])], label_visibility="collapsed")
                with c2: 
                    if st.button("✏️ Quick Edit", use_container_width=True) and gp_edit: edit_inbound_dialog(gp_edit)
                rows = "".join([f"<tr><td>{t.get('Date','')}</td><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Material','')}</td><td>{t.get('Vehicle_No','')}</td><td>{format_status(t.get('Status',''))}</td><td style='font-weight:600;'>{t.get('Net_Weight', 0):,.0f} kg</td><td style='text-align:center;'>{get_print_link(t, 'INWARD')}</td></tr>" for t in reversed(st.session_state["transactions"])])
                render_table(["Date", "Gate Pass", "Material", "Vehicle", "Status", "Net Wt", "Action"], rows)

        elif admin_nav == "🚚 Feed Dispatch":
            st.markdown("<h2 style='color:#111827;'>Feed Dispatch & Outward</h2>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight:600; color:#374151;'>Current Feed Inventory (Tons)</p>", unsafe_allow_html=True)
            if not finished_goods: st.info("No finished goods in inventory.")
            else:
                fg_cols = st.columns(max(1, len(finished_goods)))
                for idx, (feed, qty) in enumerate(finished_goods.items()):
                    fg_cols[idx % len(fg_cols)].metric(label=f"{feed}", value=f"{qty:,.2f} Tons")
            st.divider()
            if not st.session_state["feed_names"]: st.warning("⚠️ No Feed Names available to dispatch.")
            else:
                st.markdown("<p style='font-weight:600; color:#374151;'>Log New Dispatch</p>", unsafe_allow_html=True)
                with st.form("dispatch_form", clear_on_submit=False):
                    colA, colB = st.columns(2)
                    with colA:
                        disp_date = st.date_input("Dispatch Date", datetime.date.today())
                        vehicle_no = st.text_input("Vehicle Number")
                        destination = st.selectbox("Destination Location", st.session_state["locations"] if st.session_state["locations"] else ["Default Location"])
                    with colB:
                        feed_type = st.selectbox("Select Finished Feed", st.session_state["feed_names"])
                        disp_tons = st.number_input("Quantity to Dispatch (Tons)", min_value=0.1, step=1.0)
                        bag_type = st.radio("Bag Packing Size", ["70 kg", "50 kg"], horizontal=True)
                        
                    if st.form_submit_button("Log Outward Dispatch", type="primary"):
                        if not vehicle_no: st.error("⚠️ Vehicle Number required.")
                        elif disp_tons > finished_goods.get(feed_type, 0): st.error(f"⚠️ Insufficient Inventory!")
                        else:
                            bag_kg = 70 if "70" in bag_type else 50
                            next_dc_num = get_next_id(st.session_state["dispatches"], "Dispatch_ID")
                            new_data = {
                                "Dispatch_ID": f"DC-{next_dc_num}", "Date": disp_date.strftime("%d-%m-%Y"), "Time": datetime.datetime.now().strftime("%I:%M %p"),
                                "Vehicle_No": vehicle_no.upper(), "Destination": destination, "Feed_Type": feed_type,
                                "Quantity_Tons": disp_tons, "Quantity_kg": disp_tons * 1000, "Bag_Size": bag_kg, "Bag_Count": int((disp_tons * 1000) / bag_kg)
                            }
                            if insert_table("dispatches", new_data):
                                st.session_state["dispatches"].append(new_data)
                                st.success("✅ Dispatch logged successfully!"); time.sleep(1); st.rerun()

        elif admin_nav == "📦 Warehouse & Stock":
            st.markdown("<h2 style='color:#111827;'>Warehouse Inventory</h2>", unsafe_allow_html=True)
            with st.expander("⚖️ Log Physical Inventory Adjustment"):
                with st.form("adj_form", clear_on_submit=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        adj_date = st.date_input("Date", datetime.date.today())
                        adj_item = st.selectbox("Item", st.session_state["materials"] + st.session_state["feed_names"])
                    with c2:
                        adj_type = st.radio("Adjustment Type", ["Deduction (-)", "Addition (+)"])
                        adj_qty = st.number_input("Quantity (kg)", min_value=0.0, step=10.0)
                    with c3:
                        adj_reason = st.selectbox("Reason", ["Moisture Loss", "Spillage/Wastage", "Audit Correction", "Expired/Damaged"])
                    if st.form_submit_button("Apply Adjustment"):
                        new_data = {"Date": adj_date.strftime("%d-%m-%Y"), "Item": adj_item, "Type": adj_type, "Quantity": adj_qty, "Reason": adj_reason}
                        if insert_table("adjustments", new_data):
                            st.session_state["adjustments"].append(new_data)
                            st.success("✅ Adjustment applied successfully!"); time.sleep(1); st.rerun()

        elif admin_nav == "📑 Reports & Exports":
            st.markdown("<h2 style='color:#111827;'>Data Export</h2>", unsafe_allow_html=True)
            export_type = st.radio("Export:", ["Raw Material", "Dispatches", "Production"], horizontal=True)
            dates = st.date_input("Date Range", [datetime.date.today(), datetime.date.today()])
            if len(dates) == 2:
                start_date, end_date = dates
                if export_type == "Raw Material": filtered = [t for t in st.session_state["transactions"] if start_date <= datetime.datetime.strptime(t.get("Date", "01-01-2000").replace(".","-"), "%d-%m-%Y").date() <= end_date]
                elif export_type == "Dispatches": filtered = [d for d in st.session_state["dispatches"] if start_date <= datetime.datetime.strptime(d.get("Date", "01-01-2000").replace(".","-"), "%d-%m-%Y").date() <= end_date]
                else: filtered = [p for p in st.session_state["production"] if start_date <= datetime.datetime.strptime(p.get("Date", "01-01-2000").replace(".","-"), "%d-%m-%Y").date() <= end_date]
                if not filtered: st.info(f"No records found.")
                else:
                    st.dataframe(pd.DataFrame(filtered), use_container_width=True)
                    csv = pd.DataFrame(filtered).to_csv(index=False).encode('utf-8')
                    st.download_button(label=f"📥 Download Excel", data=csv, file_name=f"KJL_Export.csv", mime="text/csv", type="primary")

        elif admin_nav == "👥 User Management":
            st.markdown("<h2 style='color:#111827;'>User Management Console</h2>", unsafe_allow_html=True)
            with st.form("create_user_form", clear_on_submit=True):
                new_emp_id = st.text_input("Employee ID")
                new_username = st.text_input("System Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Assign Role", ["Admin", "Security", "QC_Lab", "Weighbridge"])
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
                        st.success("✅ Saved to cloud!"); time.sleep(1); st.rerun()
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
                        st.success("Total: 1,000 kg")
                        if st.button("✔️ Save Feed Formula", type="primary"):
                            recipe = {k: v / 1000.0 for k, v in quantities.items()}
                            if insert_table("bom", {"Formula_Name": new_formula_name, "Recipe": recipe}):
                                st.session_state["bom"][new_formula_name] = recipe
                                st.session_state["formula_reset_key"] += 1
                                st.success("✅ Formula saved to cloud!"); time.sleep(1); st.rerun()
                    else: st.error(f"Total: {total_kg:,.0f} / 1,000 kg")

# --- GATE SECURITY ---
    elif role == "Security":
        st.markdown("<h2 style='color:#111827;'>Gate Security Panel</h2>", unsafe_allow_html=True)
        tab_action, tab_history = st.tabs(["📝 Register Vehicle Arrival", "📅 Daily Registration Log"])
        
        with tab_action:
            with st.form("vehicle_entry_form", clear_on_submit=True):
                vehicle_no = st.text_input("Vehicle Number")
                material = st.selectbox("Material / Product", st.session_state["materials"])
                vendor = st.selectbox("Vendor Name", st.session_state["vendors"])
                if st.form_submit_button("Submit & Send to Lab", type="primary") and vehicle_no:
                    next_gp_num = get_next_id(st.session_state["transactions"], "Gate_Pass_ID")
                    new_data = {
                        "Gate_Pass_ID": f"GP-{next_gp_num}", 
                        "Date": datetime.datetime.now().strftime("%d-%m-%Y"), 
                        "Time": datetime.datetime.now().strftime("%I:%M %p"), 
                        "Vehicle_No": vehicle_no.upper(), "Material": material, "Vendor": vendor, "Status": "Pending QC"
                    }
                    if insert_table("transactions", new_data):
                        st.session_state["transactions"].append(new_data)
                        st.success("✅ Registered Successfully! View it in the cloud.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to register. See database error above.")
                    
        with tab_history:
            filter_date = st.date_input("Select Date", datetime.date.today(), key="sec_date").strftime("%d-%m-%Y")
            filtered_tx = [t for t in st.session_state["transactions"] if t.get("Date") == filter_date]
            if not filtered_tx: st.info(f"No vehicles registered on {filter_date}.")
            else:
                rows = "".join([f"<tr><td>{t.get('Time','')}</td><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Vehicle_No','')}</td><td>{t.get('Material','')}</td><td>{t.get('Vendor','')}</td><td>{format_status(t.get('Status',''))}</td></tr>" for t in reversed(filtered_tx)])
                render_table(["Time", "Gate Pass", "Vehicle No", "Material", "Vendor", "Status"], rows)

# --- QC LAB ---
    elif role == "QC_Lab":
        st.markdown("<h2 style='color:#111827;'>QC & Lab Testing</h2>", unsafe_allow_html=True)
        tab_action, tab_history = st.tabs(["🧪 Pending QC Tests", "📅 QC Test History"])
        
        with tab_action:
            pending_qc = [t for t in st.session_state["transactions"] if t.get("Status") == "Pending QC"]
            if pending_qc:
                selected_gp = st.selectbox("Select Vehicle", [f"{t.get('Gate_Pass_ID', 'N/A')} - {t.get('Vehicle_No','')}" for t in pending_qc]).split(" - ")[0]
                with st.form("qc_form", clear_on_submit=True):
                    qc_decision = st.radio("QC Decision", ["QC Passed", "QC Passed with Rebate", "QC Rejected"])
                    remarks = st.text_area("Remarks / Rebate Details")
                    if st.form_submit_button("Submit QC Results", type="primary"):
                        for t in st.session_state["transactions"]:
                            if t.get("Gate_Pass_ID") == selected_gp:
                                if update_table("transactions", "Gate_Pass_ID", t["Gate_Pass_ID"], {"Status": qc_decision, "QC_Remarks": remarks.strip()}):
                                    t["Status"] = qc_decision; t["QC_Remarks"] = remarks.strip()
                                    st.success("✅ QC Results Submitted")
                                    time.sleep(1)
                                    st.rerun() 
            else: st.info("No vehicles pending QC.")
            
        with tab_history:
            filter_date = st.date_input("Select Date", datetime.date.today(), key="qc_date").strftime("%d-%m-%Y")
            filtered_tx = [t for t in st.session_state["transactions"] if t.get("Date") == filter_date and t.get("Status") != "Pending QC"]
            if not filtered_tx: st.info(f"No QC tests completed on {filter_date}.")
            else:
                rows = "".join([f"<tr><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Vehicle_No','')}</td><td>{t.get('Material','')}</td><td>{format_status(t.get('Status',''))}</td><td>{t.get('QC_Remarks','')}</td></tr>" for t in reversed(filtered_tx)])
                render_table(["Gate Pass", "Vehicle No", "Material", "QC Decision", "Remarks"], rows)

# --- WEIGHBRIDGE ---
    elif role == "Weighbridge":
        st.markdown("<h2 style='color:#111827;'>Weighbridge Operations</h2>", unsafe_allow_html=True)
        tab_action, tab_history = st.tabs(["⚖️ Active Weighments", "📅 Daily Weighbridge Log"])
        
        with tab_action:
            pending_gross = [t for t in st.session_state["transactions"] if t.get("Status") in ["QC Passed", "QC Passed with Rebate"]]
            if pending_gross:
                gp_gross = st.selectbox("Select Loaded Vehicle", [f"{t.get('Gate_Pass_ID', 'N/A')} - {t.get('Vehicle_No','')}" for t in pending_gross]).split(" - ")[0]
                with st.form("gross_form", clear_on_submit=True):
                    gross_wt = st.number_input("Gross Weight (kg)", min_value=0.0, step=10.0)
                    if st.form_submit_button("Save Gross Weight", type="primary") and gross_wt > 0:
                        for t in st.session_state["transactions"]:
                            if t.get("Gate_Pass_ID") == gp_gross:
                                if update_table("transactions", "Gate_Pass_ID", t["Gate_Pass_ID"], {"Gross_Weight": gross_wt, "Status": "Unloading"}):
                                    t["Gross_Weight"] = gross_wt; t["Status"] = "Unloading"
                                    st.success("✅ Gross Weight Saved")
                                    time.sleep(1)
                                    st.rerun()

            st.divider()
            pending_tare = [t for t in st.session_state["transactions"] if t.get("Status") == "Unloading"]
            if pending_tare:
                gp_tare = st.selectbox("Select Empty Vehicle", [f"{t.get('Gate_Pass_ID', 'N/A')} - {t.get('Vehicle_No','')}" for t in pending_tare]).split(" - ")[0]
                with st.form("tare_form", clear_on_submit=True):
                    tare_wt = st.number_input("Tare Weight (kg)", min_value=0.0, step=10.0)
                    if st.form_submit_button("Save Tare & Complete", type="primary"):
                        for t in st.session_state["transactions"]:
                            if t.get("Gate_Pass_ID") == gp_tare and tare_wt < t.get("Gross_Weight", 0):
                                net = t["Gross_Weight"] - tare_wt
                                if update_table("transactions", "Gate_Pass_ID", t["Gate_Pass_ID"], {"Tare_Weight": tare_wt, "Net_Weight": net, "Status": "Completed"}):
                                    t["Tare_Weight"] = tare_wt; t["Net_Weight"] = net; t["Status"] = "Completed"
                                    st.success("✅ Vehicle Completed")
                                    time.sleep(1)
                                    st.rerun()
                                    
        with tab_history:
            filter_date = st.date_input("Select Date", datetime.date.today(), key="wb_date").strftime("%d-%m-%Y")
            filtered_tx = [t for t in st.session_state["transactions"] if t.get("Date") == filter_date and (t.get("Gross_Weight", 0) > 0 or t.get("Tare_Weight", 0) > 0)]
            if not filtered_tx: st.info(f"No weighments completed on {filter_date}.")
            else:
                rows = "".join([f"<tr><td style='font-weight:600;'>{t.get('Gate_Pass_ID','')}</td><td>{t.get('Vehicle_No','')}</td><td>{t.get('Material','')}</td><td>{t.get('Gross_Weight',0)}</td><td>{t.get('Tare_Weight',0)}</td><td style='font-weight:600;'>{t.get('Net_Weight',0)}</td><td>{format_status(t.get('Status',''))}</td></tr>" for t in reversed(filtered_tx)])
                render_table(["Gate Pass", "Vehicle No", "Material", "Gross (kg)", "Tare (kg)", "Net (kg)", "Status"], rows)

# --- APP EXECUTION ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if not st.session_state["logged_in"]: login()
else: dashboard()
