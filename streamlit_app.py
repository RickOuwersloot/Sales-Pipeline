import streamlit as st
from streamlit_sortables import sort_items
import uuid
import json
import time
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime

# --- 1. CONFIGURATIE ---
st.set_page_config(
    page_title="RO Marketing CRM", 
    page_icon="Logo RO Marketing.png", 
    layout="wide", 
    initial_sidebar_state="auto" 
)

# --- KALENDER IMPORT ---
try:
    from streamlit_calendar import calendar
except ImportError:
    st.error("⚠️ Plugin mist. Voeg 'streamlit-calendar' toe aan requirements.txt")

# ==========================================
# 🔐 BEVEILIGING
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["passwords"]["mijn_wachtwoord"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("### 🔐 Inloggen RO Marketing CRM")
    st.text_input("Voer wachtwoord in", type="password", on_change=password_entered, key="password")
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Wachtwoord onjuist")
    return False

if not check_password():
    st.stop()

# --- CONSTANTEN ---
TASK_CATEGORIES = ["Website Bouw", "Content", "Administratie", "Meeting", "Overig"]
HOURLY_RATE = 30.0
THEME_COLOR = "#ff6b6b"

# --- 2. CSS STYLING ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=Montserrat:wght@400;600;700&display=swap');
    .stApp {{ font-family: 'Montserrat', sans-serif !important; }}
    p, input, textarea, .stMarkdown, h1, h2, h3, h4, h5, h6, .stSelectbox, .stTextInput, .stDateInput, .stNumberInput {{ 
        font-family: 'Montserrat', sans-serif !important; 
    }}
    button, i, span[class^="material-symbols"] {{ font-family: inherit !important; }}
    h1, h2, h3, .stHeading, .st-emotion-cache-10trblm {{
        font-family: 'Dela Gothic One', cursive !important;
        letter-spacing: 1px;
        font-weight: 400 !important;
    }}
    .stApp {{ background-color: #0E1117; }}
    .block-container {{ max_width: 100% !important; padding: 2rem; }}
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {{ gap: 20px; overflow-x: auto; flex-wrap: nowrap; }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px; white-space: nowrap; background-color: #25262b;
        border-radius: 5px 5px 0 0; gap: 1px; padding: 10px; color: white;
    }}
    .stTabs [aria-selected="true"] {{ background-color: {THEME_COLOR} !important; color: white !important; }}

    /* METRICS & KANBAN */
    div[data-testid="metric-container"] {{
        background-color: #25262b; border: 1px solid #333; padding: 20px; border-radius: 10px; color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;
    }}
    div[class*="stSortable"] {{ display: flex; flex-direction: row; overflow-x: auto; gap: 15px; padding-bottom: 20px; }}
    div[class*="stSortable"] > div {{
        display: flex; flex-direction: column; flex: 0 0 auto; width: 300px;
        background-color: #25262b; border: 1px solid #333; border-radius: 10px; padding: 10px;
    }}
    div[class*="stSortable"] div {{ background-color: #2b313e !important; color: white !important; border-radius: 6px !important; }}
    div[class*="stSortable"] > div > div {{
        border: 1px solid {THEME_COLOR} !important; border-left: 6px solid {THEME_COLOR} !important; 
        margin-bottom: 8px; padding: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
    }}
    @media (max-width: 768px) {{
        .block-container {{ padding: 1rem 0.5rem !important; }}
        h1 {{ font-size: 1.8rem !important; }}
        div[class*="stSortable"] > div {{ width: 260px !important; min-width: 260px !important; }}
        div[style*="display:flex;gap:10px"] {{ flex-wrap: wrap !important; }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. GOOGLE SHEETS VERBINDING (GECACHE) ---
@st.cache_resource
def get_google_client():
    try:
        json_text = st.secrets["service_account"]
        creds_dict = json.loads(json_text, strict=False)
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        return None

def get_sheet(sheet_name="Sheet1"):
    client = get_google_client()
    if client:
        try: return client.open("MijnSalesCRM").worksheet(sheet_name)
        except: return None
    return None

# --- CRUCIALE FUNCTIE: CLEAR CACHE ---
def clear_data_cache():
    st.cache_data.clear()

# --- DATALOADERS ---
@st.cache_data(ttl=600) 
def get_all_records_cached(sheet_name):
    sheet = get_sheet(sheet_name)
    if not sheet: return []
    try: return sheet.get_all_records()
    except: time.sleep(1); return sheet.get_all_records()

# --- PIPELINE LOGICA ---
def load_pipeline_data():
    records = get_all_records_cached("Sheet1")
    if not records: return None

    data_structure = {'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []}
    status_map = {'Te benaderen': 'col1', 'Opgevolgd': 'col2', 'Geland': 'col3', 'Geen interesse': 'col4', 'Prullenbak': 'trash'}
    for row in records:
        if row.get('Bedrijf'):
            raw_id = str(row.get('ID', '')).strip()
            has_maint = str(row.get('Onderhoud', '')).upper() == 'TRUE'
            lead = {
                'id': raw_id if raw_id else str(uuid.uuid4()), 
                'name': row.get('Bedrijf'), 'price': row.get('Prijs'),
                'contact': row.get('Contact'), 'email': row.get('Email'),
                'phone': row.get('Telefoon'), 'website': row.get('Website'),        
                'project_map': row.get('Projectmap'), 'notes': row.get('Notities'),
                'maintenance': has_maint
            }
            col_key = status_map.get(row.get('Status', 'Te benaderen'), 'col1')
            data_structure[col_key].append(lead)
    return data_structure

def save_pipeline_data(leads_data):
    sheet = get_sheet("Sheet1")
    if not sheet: return
    rows = [['Status', 'Bedrijf', 'Prijs', 'Contact', 'Email', 'Telefoon', 'Website', 'Projectmap', 'Notities', 'Onderhoud', 'ID']]
    col_map = {'col1': 'Te benaderen', 'col2': 'Opgevolgd', 'col3': 'Geland', 'col4': 'Geen interesse', 'trash': 'Prullenbak'}
    for col_key, items in leads_data.items():
        st_txt = col_map.get(col_key, 'Te benaderen')
        for i in items:
            m_val = "TRUE" if i.get('maintenance') else "FALSE"
            rows.append([st_txt, i.get('name',''), i.get('price',''), i.get('contact',''), i.get('email',''), i.get('phone',''), i.get('website',''), i.get('project_map',''), i.get('notes',''), m_val, i.get('id', str(uuid.uuid4()))])
    try: sheet.clear(); sheet.update(rows)
    except: time.sleep(2); sheet.clear(); sheet.update(rows)
    clear_data_cache()

def update_single_lead(updated_lead):
    found = False
    for col_key, leads in st.session_state['leads_data'].items():
        for i, lead in enumerate(leads):
            if lead['id'] == updated_lead['id']:
                st.session_state['leads_data'][col_key][i] = updated_lead
                found = True; break
        if found: break
    if found: save_pipeline_data(st.session_state['leads_data'])

def fix_missing_ids():
    sheet = get_sheet("Sheet1")
    if not sheet: return
    records = sheet.get_all_records()
    rows = [['Status', 'Bedrijf', 'Prijs', 'Contact', 'Email', 'Telefoon', 'Website', 'Projectmap', 'Notities', 'Onderhoud', 'ID']]
    seen = set(); change = False
    for r in records:
        cid = str(r.get('ID','')).strip()
        if not cid or cid in seen: nid = str(uuid.uuid4()); r['ID'] = nid; change = True
        else: nid = cid
        seen.add(nid)
        rows.append([r.get('Status',''), r.get('Bedrijf',''), r.get('Prijs',''), r.get('Contact',''), r.get('Email',''), r.get('Telefoon',''), r.get('Website',''), r.get('Projectmap',''), r.get('Notities',''), r.get('Onderhoud','FALSE'), nid])
    if change: 
        sheet.clear(); sheet.update(rows); clear_data_cache(); st.success("IDs fixed!"); st.rerun()
    else: st.toast("IDs OK")

# --- TAKEN LOGICA ---
def load_tasks():
    records = get_all_records_cached("Taken")
    return [r for r in records if r.get('ID')]

def add_task(klant, taak, categorie, deadline, prioriteit, notities):
    sheet = get_sheet("Taken")
    row = ["FALSE", klant, taak, categorie, str(deadline), prioriteit, notities, str(uuid.uuid4())]
    sheet.append_row(row)
    clear_data_cache()

def add_batch_tasks(tasks_list):
    sheet = get_sheet("Taken")
    rows_to_add = []
    for t in tasks_list:
        rows_to_add.append(["FALSE", t['klant'], t['taak'], t['cat'], str(t['deadline']), t['prio'], "", str(uuid.uuid4())])
    sheet.append_rows(rows_to_add)
    clear_data_cache()

def update_task_data(task_id, new_data):
    sheet = get_sheet("Taken")
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row.get('ID')) == task_id:
            sheet.update_cell(i + 2, 2, new_data['Klant'])
            sheet.update_cell(i + 2, 3, new_data['Taak'])
            sheet.update_cell(i + 2, 4, new_data['Categorie'])
            sheet.update_cell(i + 2, 5, str(new_data['Deadline']))
            sheet.update_cell(i + 2, 6, new_data['Prioriteit'])
            sheet.update_cell(i + 2, 7, new_data['Notities'])
            clear_data_cache(); return

def toggle_task_status(task_id, current_status):
    sheet = get_sheet("Taken")
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row.get('ID')) == task_id:
            new_val = "TRUE" if current_status == "FALSE" else "FALSE"
            sheet.update_cell(i + 2, 1, new_val)
            clear_data_cache(); return

def delete_completed_tasks():
    sheet = get_sheet("Taken")
    records = sheet.get_all_records()
    rows = [['Status', 'Klant', 'Taak', 'Categorie', 'Deadline', 'Prioriteit', 'Notities', 'ID']]
    for r in records:
        if str(r.get('Status')).upper() != "TRUE":
            rows.append([r.get('Status'), r.get('Klant'), r.get('Taak'), r.get('Categorie'), r.get('Deadline'), r.get('Prioriteit'), r.get('Notities'), r.get('ID')])
    sheet.clear(); sheet.update(rows)
    clear_data_cache()

def delete_single_task(task_id):
    sheet = get_sheet("Taken")
    records = sheet.get_all_records()
    rows = [['Status', 'Klant', 'Taak', 'Categorie', 'Deadline', 'Prioriteit', 'Notities', 'ID']]
    for r in records:
        if str(r.get('ID')) != task_id:
            rows.append([r.get('Status'), r.get('Klant'), r.get('Taak'), r.get('Categorie'), r.get('Deadline'), r.get('Prioriteit'), r.get('Notities'), r.get('ID')])
    sheet.clear(); sheet.update(rows)
    clear_data_cache()

# --- UREN LOGICA ---
def load_hours():
    records = get_all_records_cached("Uren")
    return [r for r in records if r.get('ID')]

def save_queued_hours(queue):
    sheet = get_sheet("Uren")
    rows = []
    for h in queue:
        totaal = float(h['uren']) * HOURLY_RATE
        rows.append([str(h['datum']), h['klant'], float(h['uren']), h['desc'], HOURLY_RATE, totaal, str(uuid.uuid4())])
    try: 
        sheet.append_rows(rows)
        clear_data_cache(); return True
    except: return False

def delete_hour_entry(entry_id):
    sheet = get_sheet("Uren")
    records = sheet.get_all_records()
    rows = [['Datum', 'Klant', 'Uren', 'Omschrijving', 'Tarief', 'Totaal', 'ID']]
    for r in records:
        if str(r.get('ID')) != entry_id:
            rows.append([r['Datum'], r['Klant'], r['Uren'], r['Omschrijving'], r['Tarief'], r['Totaal'], r['ID']])
    sheet.clear(); sheet.update(rows)
    clear_data_cache()

def parse_price(price_str):
    if not price_str: return 0.0
    clean = str(price_str).replace('€', '').replace('.', '').replace(',', '.').strip().split(' ')[0]
    try: return float(clean)
    except: return 0.0

# --- INITIALISATIE ---
if 'leads_data' not in st.session_state:
    loaded = load_pipeline_data()
    st.session_state['leads_data'] = loaded if loaded else {'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []}
if 'board_key' not in st.session_state: st.session_state['board_key'] = 0
if 'hour_queue' not in st.session_state: st.session_state['hour_queue'] = [] 

all_companies = []
for col_list in st.session_state['leads_data'].values():
    for l in col_list: all_companies.append(l['name'])
all_companies.sort()

# --- APP LAYOUT ---
st.title("🚀 RO Marketing CRM")
# Knop om handmatig alles te verversen
if st.button("🔄 Ververs Data", help="Haal de nieuwste gegevens op uit Google Sheets"):
    clear_data_cache()
    st.rerun()

tab_dash, tab_pipeline, tab_tasks, tab_hours = st.tabs(["📈 Dashboard", "📊 Pipeline", "✅ Projecten & Taken", "⏱️ Uren & Tijd"])

# ================= TAB 1: DASHBOARD =================
with tab_dash:
    st.header("📈 Financieel Dashboard")
    all_hours = load_hours()
    if all_hours:
        df = pd.DataFrame(all_hours)
        df['Totaal'] = pd.to_numeric(df['Totaal'], errors='coerce').fillna(0)
        df['Uren'] = pd.to_numeric(df['Uren'], errors='coerce').fillna(0)
        df['Datum'] = pd.to_datetime(df['Datum'], errors='coerce')
        df['Maand'] = df['Datum'].dt.strftime('%Y-%m')
        
        col_fil, col_empty = st.columns([1, 2])
        with col_fil:
            cur_m = datetime.now().strftime('%Y-%m')
            months = sorted(df['Maand'].unique().tolist(), reverse=True)
            if cur_m not in months: months.insert(0, cur_m)
            sel_month = st.selectbox("📅 Maand:", months, key="dash_month_filter")
        
        m_data = df[df['Maand'] == sel_month]
        pipe_val = sum([parse_price(l.get('price')) for l in st.session_state['leads_data']['col3']])
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Waarde Uren ({sel_month})", f"€ {m_data['Totaal'].sum():,.2f}")
        m2.metric(f"Gewerkte Uren ({sel_month})", f"{m_data['Uren'].sum():.1f} uur")
        m3.metric("Totaal Deals Geland 🎉", f"€ {pipe_val:,.2f}")
        
        st.divider(); 
        
        c_chart, c_list = st.columns([2, 1])
        with c_chart:
            st.subheader("📈 Omzetverloop per Maand")
            if not df.empty: st.line_chart(df.groupby('Maand')['Totaal'].sum(), color=THEME_COLOR)
            
        with c_list:
            st.subheader("🔧 Contracten")
            maintenance_clients = []
            for col in ['col1', 'col2', 'col3', 'col4']:
                for lead in st.session_state['leads_data'][col]:
                    if lead.get('maintenance'):
                        maintenance_clients.append(lead['name'])
            
            if maintenance_clients:
                with st.container(height=300, border=True):
                    for client in maintenance_clients:
                        st.markdown(f"<div style='font-size: 0.9em; color: #aaa; padding: 4px 0; border-bottom: 1px solid #333;'>🔧 {client}</div>", unsafe_allow_html=True)
            else: st.caption("Geen contracten.")
    else:
        st.info("Nog geen uren geschreven.")
        pipe_val = sum([parse_price(l.get('price')) for l in st.session_state['leads_data']['col3']])
        st.metric("Totaal Deals Geland 🎉", f"€ {pipe_val:,.2f}")

# ================= TAB 2: PIPELINE =================
with tab_pipeline:
    with st.sidebar:
        try: st.image("Logo RO Marketing.png", width=150)
        except: st.warning("Logo?")
        with st.expander("➕ Nieuwe Deal", expanded=False):
            with st.form("add_lead"):
                comp = st.text_input("Bedrijf *")
                cont = st.text_input("Contact")
                mail = st.text_input("Email")
                tel = st.text_input("Tel")
                web = st.text_input("Website URL")
                proj = st.text_input("Link naar Projectmap (URL)") 
                m_contr = st.checkbox("🔧 Heeft Onderhoudscontract?")
                pri = st.text_input("€")
                not_ = st.text_area("Note")
                if st.form_submit_button("Toevoegen"):
                    if not comp: st.error("Naam!")
                    else:
                        ni = {
                            'id': str(uuid.uuid4()), 'name': comp, 'contact': cont, 
                            'email': mail, 'phone': tel, 'website': web, 
                            'project_map': proj, 'price': pri, 'notes': not_,
                            'maintenance': m_contr
                        }
                        st.session_state['leads_data']['col1'].insert(0, ni)
                        save_pipeline_data(st.session_state['leads_data'])
                        st.session_state['board_key'] += 1; st.rerun()
        if st.button("🗑️ Prullenbak Legen", key="empty_trash"):
            st.session_state['leads_data']['trash'] = []; save_pipeline_data(st.session_state['leads_data']); st.session_state['board_key'] += 1; st.rerun()
        c1, c2 = st.columns(2)
        if c1.button("🔄", key="reload_data"): st.cache_resource.clear(); del st.session_state['leads_data']; st.rerun()
        if c2.button("🛠️", key="fix_ids"): fix_missing_ids()

    cols = [('col1', 'Te benaderen'), ('col2', 'Opgevolgd'), ('col3', 'Geland 🎉'), ('col4', 'Geen interesse'), ('trash', 'Prullenbak 🗑️')]
    k_data = []
    all_leads = []
    for k, name in cols:
        items = []
        for l in st.session_state['leads_data'][k]:
            name_label = l['name']
            if l.get('maintenance'): name_label += " 🔧"
            price_part = f" | {l['price']}" if l['price'] else ""
            items.append(f"{name_label}{price_part}")
        all_leads.extend(st.session_state['leads_data'][k])
        k_data.append({'header': name, 'items': items})

    s_data = sort_items(k_data, multi_containers=True, key=f"board_{st.session_state['board_key']}")

    if len(s_data) == 5:
        new_st = {}
        lookup = {}
        for l in all_leads:
            name_label = l['name']
            if l.get('maintenance'): name_label += " 🔧"
            price_part = f" | {l['price']}" if l['price'] else ""
            lookup[f"{name_label}{price_part}"] = l

        for i, cd in enumerate(s_data):
            new_st[cols[i][0]] = [lookup[x] for x in cd['items'] if x in lookup]
        curr_ids = [[l['id'] for l in c] for c in st.session_state['leads_data'].values()]
        new_ids = [[l['id'] for l in c] for c in new_st.values()]
        if curr_ids != new_ids:
            st.session_state['leads_data'] = new_st; save_pipeline_data(new_st); st.rerun()

    st.divider()
    if len(all_leads) > 0:
        c_sel, c_inf = st.columns([1, 2])
        with c_sel:
            fil = st.selectbox("🔍 Filter:", ["Alles"] + [n for _, n in cols], key="pipeline_filter_phase")
            f_leads = all_leads if fil == "Alles" else st.session_state['leads_data'][next((k for k, n in cols if n == fil), 'col1')]
            d_opts = {f"{l['name']}": l['id'] for l in f_leads}
            
            if d_opts:
                sel_name = st.selectbox("Selecteer deal:", list(d_opts.keys()), key="pipeline_deal_selector")
                sel_id = d_opts[sel_name]
                sel = next((l for l in all_leads if l['id'] == sel_id), None)
            else:
                sel = None; st.info("Geen deals gevonden.")

        if sel:
            if 'editing_id' not in st.session_state or st.session_state['editing_id'] != sel['id']:
                st.session_state['edit_mode'] = False
                st.session_state['editing_id'] = sel['id']

            with c_inf:
                with st.container(border=True):
                    if st.session_state['edit_mode']:
                        st.subheader(f"✏️ Bewerk: {sel['name']}")
                        with st.form(key=f"edit_form_{sel['id']}"):
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                u_name = st.text_input("Bedrijfsnaam", sel['name'])
                                u_contact = st.text_input("Contactpersoon", sel['contact'])
                                u_email = st.text_input("Email", sel['email'])
                                u_phone = st.text_input("Telefoon", sel['phone'])
                            with ec2:
                                u_price = st.text_input("Prijs (bv. €1500)", sel['price'])
                                u_web = st.text_input("Website URL", sel.get('website', ''))
                                u_proj = st.text_input("Projectmap URL", sel.get('project_map', ''))
                                u_maint = st.checkbox("🔧 Onderhoudscontract actief?", value=sel.get('maintenance', False))
                            u_notes = st.text_area("Notities", sel.get('notes', ''))
                            if st.form_submit_button("💾 Opslaan & Sluiten", use_container_width=True):
                                updated_lead = sel.copy()
                                updated_lead.update({'name': u_name, 'contact': u_contact, 'email': u_email, 'phone': u_phone, 'price': u_price, 'website': u_web, 'project_map': u_proj, 'notes': u_notes, 'maintenance': u_maint})
                                update_single_lead(updated_lead)
                                st.session_state['edit_mode'] = False; st.rerun()
                    else:
                        r1, r2 = st.columns([4, 1])
                        with r1: 
                            dn = sel['name']
                            if sel.get('maintenance'): dn += " 🔧"
                            st.markdown(f"### {dn}")
                        with r2: 
                            if st.button("✏️ Bewerken", key="btn_edit_mode"):
                                st.session_state['edit_mode'] = True; st.rerun()
                        st.markdown(f"<h1 style='color:#fff;margin-top:-10px;font-size:2em'>{sel['price']}</h1>", unsafe_allow_html=True)
                        rc1, rc2 = st.columns(2)
                        with rc1:
                            st.write(f"👤 **Contact:** {sel.get('contact','-')}")
                            st.write(f"📧 **Email:** {sel.get('email','-')}")
                            st.write(f"☎️ **Tel:** {sel.get('phone','-')}")
                        with rc2:
                            if sel.get('website'):
                                url = sel['website']; 
                                if not url.startswith('http'): url = 'https://' + url
                                st.markdown(f"🌐 [{sel['website']}]({url})")
                            if sel.get('project_map'):
                                purl = sel['project_map']; 
                                if not purl.startswith('http'): purl = 'https://' + purl
                                st.link_button("📂 Open Projectmap", purl)
                            else: st.caption("Geen projectmap gekoppeld")
                        st.markdown("---"); st.info(sel.get('notes') or "Geen notities.")

# ================= TAB 3: TAKEN =================
with tab_tasks:
    st.header("✅ Projectmanagement")
    
    with st.expander("⚡ Snel Taken Toevoegen (Checklists)", expanded=False):
        st.caption("Kies een standaardlijst om in één keer toe te voegen aan een klant.")
        sl_c1, sl_c2 = st.columns(2)
        with sl_c1:
            sl_klant = st.selectbox("Voor welke klant?", all_companies, key="checklist_client_select")
        with sl_c2:
            st.write("") 
            st.write("") 
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("🌐 Nieuwe Website"):
                tasks = [
                    {"klant": sl_klant, "taak": "Hosting & Domeinnaam vastleggen", "cat": "Website Bouw", "deadline": date.today(), "prio": "🔥 Hoog"},
                    {"klant": sl_klant, "taak": "Wordpress installeren", "cat": "Website Bouw", "deadline": date.today(), "prio": "🔥 Hoog"},
                    {"klant": sl_klant, "taak": "Pagina structuur aanmaken (Sitemap)", "cat": "Website Bouw", "deadline": date.today(), "prio": "⏺️ Midden"},
                    {"klant": sl_klant, "taak": "Responsiveness checken", "cat": "Website Bouw", "deadline": date.today(), "prio": "⏺️ Midden"},
                    {"klant": sl_klant, "taak": "Projectmap aanmaken in Google Drive", "cat": "Administratie", "deadline": date.today(), "prio": "⏺️ Midden"},
                ]
                add_batch_tasks(tasks)
                st.success(f"5 Taken toegevoegd voor {sl_klant}!")
                st.rerun()
            if c_btn2.button("🔧 Onderhoud Starten"):
                today = date.today()
                year_jan = today.year + 1 if today >= date(today.year, 1, 1) else today.year
                d_jan = date(year_jan, 1, 1)
                year_jun = today.year + 1 if today >= date(today.year, 6, 1) else today.year
                d_jun = date(year_jun, 6, 1)
                tasks = [
                    {"klant": sl_klant, "taak": "Factuur Onderhoud versturen (Ronde Januari)", "cat": "Administratie", "deadline": d_jan, "prio": "🔥 Hoog"},
                    {"klant": sl_klant, "taak": "Factuur Onderhoud versturen (Ronde Juni)", "cat": "Administratie", "deadline": d_jun, "prio": "🔥 Hoog"},
                ]
                add_batch_tasks(tasks)
                st.success(f"Facturatie taken ingepland voor {sl_klant}!")
                st.rerun()

    with st.expander(f"➕ Losse Taak toevoegen", expanded=False):
        with st.form("new_task"):
            ca, cb = st.columns(2)
            with ca:
                def_klant_idx = 0
                if 'task_filter_client' in st.session_state and st.session_state['task_filter_client'] != "Alle Projecten":
                     if st.session_state['task_filter_client'] in all_companies:
                         def_klant_idx = all_companies.index(st.session_state['task_filter_client'])
                n_klant = st.selectbox("Klant", all_companies, index=def_klant_idx, key="new_task_client")
                n_taak = st.text_input("Taak")
                n_cat = st.selectbox("Categorie", TASK_CATEGORIES, key="new_task_cat")
            with cb:
                n_date = st.date_input("Deadline", date.today())
                n_prio = st.selectbox("Prioriteit", ["🔥 Hoog", "⏺️ Midden", "💤 Laag"], key="new_task_prio")
                n_note = st.text_area("Notities")
            if st.form_submit_button("Opslaan"):
                add_task(n_klant, n_taak, n_cat, n_date, n_prio, n_note); st.success("Opgeslagen!"); st.rerun()

    st.divider()

    c_filt1, c_filt2 = st.columns(2)
    with c_filt1: k_filt = st.selectbox("📂 Filter op Klant:", ["Alle Projecten"] + all_companies, key="task_filter_client")
    with c_filt2: c_filt = st.selectbox("🏷️ Filter op Categorie:", ["Alle Categorieën"] + TASK_CATEGORIES, key="task_filter_cat")

    all_tasks = load_tasks()
    disp = all_tasks
    if k_filt != "Alle Projecten": disp = [t for t in disp if t.get('Klant') == k_filt]
    if c_filt != "Alle Categorieën": disp = [t for t in disp if t.get('Categorie') == c_filt]

    if not disp: st.info(f"Geen taken gevonden.")
    else:
        p_map = {"🔥 Hoog": 1, "⏺️ Midden": 2, "💤 Laag": 3}
        disp.sort(key=lambda x: (str(x.get('Status')).upper() == 'TRUE', p_map.get(x.get('Prioriteit'), 2), x.get('Deadline')))
        st.write(f"**{len(disp)} taken**")
        for t in disp:
            if not t.get('ID'): continue
            done = str(t.get('Status')).upper() == 'TRUE'
            opac = "0.5" if done else "1.0"
            strike = "text-decoration: line-through;" if done else ""
            with st.container(border=True):
                c_chk, c_inf, c_met, c_del = st.columns([0.5, 5, 2.5, 0.5])
                with c_chk:
                    if st.checkbox("", value=done, key=f"chk_{t['ID']}") != done:
                        toggle_task_status(t['ID'], str(t.get('Status')).upper()); st.rerun()
                with c_inf:
                    kl = f"<span style='color:{THEME_COLOR};font-weight:bold'>{t.get('Klant')}</span> | " if k_filt == "Alle Projecten" else ""
                    st.markdown(f"<div style='opacity:{opac};{strike}'>{kl}<strong>{t['Taak']}</strong></div>", unsafe_allow_html=True)
                    if t.get('Notities'): st.caption(f"📝 {t['Notities']}")
                with c_met:
                    praw = t.get('Prioriteit', "⏺️ Midden")
                    if praw not in ["🔥 Hoog", "⏺️ Midden", "💤 Laag"]: praw = "⏺️ Midden"
                    pcol = "#ff4b4b" if "Hoog" in praw else "#ffa421" if "Midden" in praw else "#00c0f2"
                    st.markdown(f"<div style='display:flex;gap:10px;align-items:center;justify-content:flex-end;flex-wrap:wrap;opacity:{opac}'><span style='color:{pcol};font-weight:bold;font-size:0.9em'>{praw}</span><span style='font-weight:700;color:#eee'>📅 {t['Deadline']}</span><span style='background:#333;padding:4px 8px;border-radius:4px;font-size:0.8em;border:1px solid #444'>{t['Categorie']}</span></div>", unsafe_allow_html=True)
                with c_del:
                    if st.button("🗑️", key=f"del_task_{t['ID']}"):
                        delete_single_task(t['ID'])
                        st.rerun()
                with st.expander("✏️ Bewerk"):
                    with st.form(f"edit_{t['ID']}"):
                        e1, e2 = st.columns(2)
                        with e1:
                            ek = st.selectbox("Klant", all_companies, index=all_companies.index(t['Klant']) if t['Klant'] in all_companies else 0, key=f"ek_{t['ID']}")
                            et = st.text_input("Taak", t['Taak'], key=f"et_{t['ID']}")
                            ec = st.selectbox("Categorie", TASK_CATEGORIES, index=TASK_CATEGORIES.index(t['Categorie']) if t['Categorie'] in TASK_CATEGORIES else 0, key=f"ec_{t['ID']}")
                        with e2:
                            dv = datetime.strptime(t['Deadline'], "%Y-%m-%d").date() if t['Deadline'] else date.today()
                            ed = st.date_input("Deadline", dv, key=f"ed_{t['ID']}")
                            ps = t.get('Prioriteit', "⏺️ Midden")
                            if ps not in ["🔥 Hoog", "⏺️ Midden", "💤 Laag"]: ps = "⏺️ Midden"
                            ep = st.selectbox("Prioriteit", ["🔥 Hoog", "⏺️ Midden", "💤 Laag"], index=["🔥 Hoog", "⏺️ Midden", "💤 Laag"].index(ps), key=f"ep_{t['ID']}")
                        en = st.text_area("Notities", t.get('Notities', ''), key=f"en_{t['ID']}")
                        if st.form_submit_button("Opslaan"):
                            new_d = {'Klant': ek, 'Taak': et, 'Categorie': ec, 'Deadline': ed, 'Prioriteit': ep, 'Notities': en}
                            update_task_data(t['ID'], new_d); st.success("Opgeslagen!"); st.rerun()
    st.divider()
    if st.button("🧹 Voltooide taken verwijderen", key="del_completed_tasks"):
        delete_completed_tasks(); st.success("Opgeruimd!"); st.rerun()

# ================= TAB 4: UREN (BATCHING UPDATE) =================
with tab_hours:
    st.header("⏱️ Urenregistratie")
    st.markdown(f"**Vast Tarief:** €{HOURLY_RATE} / uur")
    
    with st.container(border=True):
        st.subheader("✍️ Tijd Schrijven")
        h1, h2, h3 = st.columns([2, 1, 2])
        with h1: 
            hk = st.selectbox("Klant", all_companies, key="hour_client")
            hd = st.date_input("Datum", date.today(), key="hour_date")
        with h2: 
            hu = st.number_input("Uren", min_value=0.0, step=0.25, format="%.2f", key="hour_amount")
        with h3: 
            hdc = st.text_input("Omschrijving", key="hour_desc")
            st.write("") 
            if st.button("➕ Voeg toe aan lijst", use_container_width=True):
                if hu > 0:
                    st.session_state['hour_queue'].append({"klant": hk, "datum": hd, "uren": hu, "desc": hdc})
                    st.success("Toegevoegd aan wachtrij!")
                else: st.error("Vul aantal uren in!")

    if st.session_state['hour_queue']:
        st.write("---")
        st.subheader(f"⏳ Klaar om op te slaan ({len(st.session_state['hour_queue'])})")
        q_df = pd.DataFrame(st.session_state['hour_queue'])
        st.table(q_df)
        if st.button("💾 Alles Opslaan naar Google Sheets", type="primary", use_container_width=True):
            if save_queued_hours(st.session_state['hour_queue']):
                st.session_state['hour_queue'] = [] 
                st.success("✅ Alles succesvol opgeslagen!"); time.sleep(1); st.rerun()
            else: st.error("Fout bij opslaan.")
        if st.button("❌ Wachtrij wissen"):
            st.session_state['hour_queue'] = []; st.rerun()

    st.divider()
    st.subheader("📅 Kalender Overzicht")
    all_hours_data = load_hours()
    calendar_events = []
    if all_hours_data:
        for h in all_hours_data:
            try:
                d_str = str(h['Datum'])
                iso_date = pd.to_datetime(d_str, dayfirst=True).strftime('%Y-%m-%d')
                evt = {"title": f"{h['Klant']} ({h['Uren']}u)", "start": iso_date, "allDay": True, "backgroundColor": THEME_COLOR, "borderColor": THEME_COLOR}
                calendar_events.append(evt)
            except: continue

    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth" # Alleen maandoverzicht
        },
        "initialView": "dayGridMonth",
        "selectable": True,
    }
    
    if 'calendar' in globals():
        calendar(events=calendar_events, options=calendar_options)
    
    with st.expander("📜 Bekijk als Lijst"):
        hf = st.selectbox("🔍 Filter overzicht op klant:", ["Alle Klanten"] + all_companies, key="hour_overview_filter")
        fh = [h for h in all_hours_data if h.get('Klant') == hf] if hf != "Alle Klanten" else all_hours_data
        th = sum([float(h.get('Uren', 0)) for h in fh])
        tm = sum([float(h.get('Totaal', 0)) for h in fh])
        m1, m2 = st.columns(2)
        m1.metric("Totaal Uren (Selectie)", f"{th:.2f} uur")
        m2.metric("Totale Waarde (Selectie)", f"€ {tm:,.2f}")
        
        # --- HIER IS DE NIEUWE DOWNLOAD KNOP ---
        if fh:
            # 1. Maak een mooie DataFrame voor export
            df_export = pd.DataFrame(fh)
            # Alleen de relevante kolommen voor de klant
            df_export = df_export[['Datum', 'Omschrijving', 'Uren', 'Tarief', 'Totaal']]
            
            # CSV maken
            csv = df_export.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label=f"📥 Download Urenspecificatie voor {hf}",
                data=csv,
                file_name=f"Urenregistratie_{hf}_{date.today()}.csv",
                mime="text/csv",
            )
        # ---------------------------------------

        for e in reversed(fh):
            with st.container(border=True):
                ca, cb, cc, cd = st.columns([1.5, 4, 1.5, 1])
                with ca: st.caption(e['Datum']); st.write(f"**{e['Klant']}**")
                with cb: st.write(e['Omschrijving'])
                with cc: st.markdown(f"**{e['Uren']}u** (€{e['Totaal']})")
                with cd:
                    if st.button("🗑️", key=f"del_h_{e['ID']}"): delete_hour_entry(e['ID']); st.rerun()
