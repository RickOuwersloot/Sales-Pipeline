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

# --- CONSTANTEN ---
TASK_CATEGORIES = ["Website Bouw", "Content", "Administratie", "Meeting", "Overig"]
HOURLY_RATE = 30.0

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=Montserrat:wght@400;600;700&display=swap');

    .stApp { font-family: 'Montserrat', sans-serif !important; }
    p, input, textarea, .stMarkdown, h1, h2, h3, h4, h5, h6, .stSelectbox, .stTextInput, .stDateInput, .stNumberInput { 
        font-family: 'Montserrat', sans-serif !important; 
    }
    
    button, i, span[class^="material-symbols"] { font-family: inherit !important; }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarExpandedControl"] button { font-family: "Source Sans Pro", sans-serif !important; }

    h1, h2, h3, .stHeading, .st-emotion-cache-10trblm {
        font-family: 'Dela Gothic One', cursive !important;
        letter-spacing: 1px;
        font-weight: 400 !important;
    }

    .stApp { background-color: #0E1117; }
    .block-container { max_width: 100% !important; padding: 2rem; }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #25262b;
        border-radius: 5px 5px 0 0; gap: 1px; padding: 10px; color: white;
    }
    .stTabs [aria-selected="true"] { background-color: #2196F3 !important; color: white !important; }

    /* METRICS BOX */
    div[data-testid="metric-container"] {
        background-color: #25262b;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* KANBAN */
    div[class*="stSortable"] { display: flex; flex-direction: row; overflow-x: auto; gap: 15px; padding-bottom: 20px; }
    div[class*="stSortable"] > div {
        display: flex; flex-direction: column; flex: 0 0 auto; width: 300px;
        background-color: #25262b; border: 1px solid #333; border-radius: 10px; padding: 10px;
    }
    div[class*="stSortable"] div { background-color: #2b313e !important; color: white !important; border-radius: 6px !important; }
    div[class*="stSortable"] > div > div {
        border: 1px solid #2196F3 !important; border-left: 6px solid #2196F3 !important; 
        margin-bottom: 8px; padding: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
    }
    div[class*="stSortable"] > div > div:hover {
        background-color: #363c4e !important; border-color: #64b5f6 !important; transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. GOOGLE SHEETS VERBINDING (ROBUUST GEMAAKT) ---
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
        try: 
            return client.open("MijnSalesCRM").worksheet(sheet_name)
        except: 
            # HIER IS DE FIX: Geen st.error meer, maar gewoon 'None' teruggeven
            # De app snapt dan dat de sheet er niet is en gaat rustig verder.
            return None
    return None

# --- PIPELINE FUNCTIES ---
def load_pipeline_data():
    sheet = get_sheet("Sheet1")
    if not sheet: return None # Stil falen als sheet er niet is
    try:
        records = sheet.get_all_records()
    except gspread.exceptions.APIError:
        time.sleep(2)
        try: records = sheet.get_all_records()
        except: return None
    except: return None

    data_structure = {'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []}
    status_map = {'Te benaderen': 'col1', 'Opgevolgd': 'col2', 'Geland': 'col3', 'Geen interesse': 'col4', 'Prullenbak': 'trash'}
    for row in records:
        if row.get('Bedrijf'):
            raw_id = str(row.get('ID', '')).strip()
            lead = {
                'id': raw_id if raw_id else str(uuid.uuid4()), 
                'name': row.get('Bedrijf'), 'price': row.get('Prijs'),
                'contact': row.get('Contact'), 'email': row.get('Email'),
                'phone': row.get('Telefoon'), 'website': row.get('Website'), 'notes': row.get('Notities')
            }
            col_key = status_map.get(row.get('Status', 'Te benaderen'), 'col1')
            data_structure[col_key].append(lead)
    return data_structure

def save_pipeline_data(leads_data):
    sheet = get_sheet("Sheet1")
    if not sheet: return
    rows = [['Status', 'Bedrijf', 'Prijs', 'Contact', 'Email', 'Telefoon', 'Website', 'Notities', 'ID']]
    col_map = {'col1': 'Te benaderen', 'col2': 'Opgevolgd', 'col3': 'Geland', 'col4': 'Geen interesse', 'trash': 'Prullenbak'}
    for col_key, items in leads_data.items():
        st_txt = col_map.get(col_key, 'Te benaderen')
        for i in items:
            rows.append([st_txt, i.get('name',''), i.get('price',''), i.get('contact',''), i.get('email',''), i.get('phone',''), i.get('website',''), i.get('notes',''), i.get('id', str(uuid.uuid4()))])
    try: sheet.clear(); sheet.update(rows)
    except: time.sleep(2); sheet.clear(); sheet.update(rows)

def fix_missing_ids():
    sheet = get_sheet("Sheet1")
    if not sheet: return
    try: records = sheet.get_all_records()
    except: return
    rows = [['Status', 'Bedrijf', 'Prijs', 'Contact', 'Email', 'Telefoon', 'Website', 'Notities', 'ID']]
    seen = set(); change = False
    for r in records:
        cid = str(r.get('ID','')).strip()
        if not cid or cid in seen: nid = str(uuid.uuid4()); r['ID'] = nid; change = True
        else: nid = cid
        seen.add(nid)
        rows.append([r.get('Status',''), r.get('Bedrijf',''), r.get('Prijs',''), r.get('Contact',''), r.get('Email',''), r.get('Telefoon',''), r.get('Website',''), r.get('Notities',''), nid])
    if change: sheet.clear(); sheet.update(rows); st.success("IDs fixed!"); st.cache_resource.clear(); st.rerun()
    else: st.toast("IDs OK")

# --- TAKEN FUNCTIES ---
def load_tasks():
    sheet = get_sheet("Taken")
    if not sheet: return []
    try: return [r for r in sheet.get_all_records() if r.get('ID')]
    except: return []

def add_task(klant, taak, categorie, deadline, prioriteit, notities):
    sheet = get_sheet("Taken")
    if not sheet: st.error("Maak eerst het tabblad 'Taken' aan in Google Sheets!"); return
    row = ["FALSE", klant, taak, categorie, str(deadline), prioriteit, notities, str(uuid.uuid4())]
    try: sheet.append_row(row)
    except: time.sleep(1); sheet.append_row(row)

def update_task_data(task_id, new_data):
    sheet = get_sheet("Taken")
    if not sheet: return
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row.get('ID')) == task_id:
            try:
                sheet.update_cell(i + 2, 2, new_data['Klant'])
                sheet.update_cell(i + 2, 3, new_data['Taak'])
                sheet.update_cell(i + 2, 4, new_data['Categorie'])
                sheet.update_cell(i + 2, 5, str(new_data['Deadline']))
                sheet.update_cell(i + 2, 6, new_data['Prioriteit'])
                sheet.update_cell(i + 2, 7, new_data['Notities'])
            except: st.error("Fout bij opslaan."); return
            return

def toggle_task_status(task_id, current_status):
    sheet = get_sheet("Taken")
    if not sheet: return
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row.get('ID')) == task_id:
            new_val = "TRUE" if current_status == "FALSE" else "FALSE"
            try: sheet.update_cell(i + 2, 1, new_val)
            except: time.sleep(1); sheet.update_cell(i + 2, 1, new_val)
            return

def delete_completed_tasks():
    sheet = get_sheet("Taken")
    if not sheet: return
    records = sheet.get_all_records()
    rows = [['Status', 'Klant', 'Taak', 'Categorie', 'Deadline', 'Prioriteit', 'Notities', 'ID']]
    for r in records:
        if str(r.get('Status')).upper() != "TRUE":
            rows.append([r.get('Status'), r.get('Klant'), r.get('Taak'), r.get('Categorie'), r.get('Deadline'), r.get('Prioriteit'), r.get('Notities'), r.get('ID')])
    sheet.clear(); sheet.update(rows)

# --- UREN FUNCTIES ---
def load_hours():
    sheet = get_sheet("Uren")
    if not sheet: return [] # Geen error, gewoon lege lijst teruggeven
    try: return [r for r in sheet.get_all_records() if r.get('ID')]
    except: return []

def log_time(klant, datum, uren, omschrijving):
    sheet = get_sheet("Uren")
    if not sheet: st.error("Maak eerst het tabblad 'Uren' aan in Google Sheets!"); return
    totaal = float(uren) * HOURLY_RATE
    row = [str(datum), klant, float(uren), omschrijving, HOURLY_RATE, totaal, str(uuid.uuid4())]
    try: sheet.append_row(row)
    except: time.sleep(1); sheet.append_row(row)

def delete_hour_entry(entry_id):
    sheet = get_sheet("Uren")
    if not sheet: return
    records = sheet.get_all_records()
    rows = [['Datum', 'Klant', 'Uren', 'Omschrijving', 'Tarief', 'Totaal', 'ID']]
    for r in records:
        if str(r.get('ID')) != entry_id:
            rows.append([r['Datum'], r['Klant'], r['Uren'], r['Omschrijving'], r['Tarief'], r['Totaal'], r['ID']])
    sheet.clear(); sheet.update(rows)

# --- HELPER FUNCTIES VOOR DASHBOARD ---
def parse_price(price_str):
    if not price_str: return 0.0
    clean = str(price_str).replace('€', '').replace('.', '').replace(',', '.').strip()
    clean = clean.split(' ')[0]
    try: return float(clean)
    except: return 0.0

# --- INITIALISATIE ---
if 'leads_data' not in st.session_state:
    loaded = load_pipeline_data()
    st.session_state['leads_data'] = loaded if loaded else {'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []}
if 'board_key' not in st.session_state: st.session_state['board_key'] = 0

all_companies = []
for col_list in st.session_state['leads_data'].values():
    for l in col_list: all_companies.append(l['name'])
all_companies.sort()

# --- APP LAYOUT ---
st.title("🚀 RO Marketing CRM")
# TABS DEFINITIE
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
        
        # 1. FILTERS
        col_fil, col_empty = st.columns([1, 2])
        with col_fil:
            current_month = datetime.now().strftime('%Y-%m')
            available_months = sorted(df['Maand'].unique().tolist(), reverse=True)
            if current_month not in available_months: available_months.insert(0, current_month)
            
            selected_month = st.selectbox("📅 Selecteer Maand:", available_months)
        
        # 2. METRICS
        monthly_data = df[df['Maand'] == selected_month]
        month_revenue = monthly_data['Totaal'].sum()
        month_hours = monthly_data['Uren'].sum()
        
        pipeline_value = 0.0
        for lead in st.session_state['leads_data']['col3']: # col3 = Geland
            pipeline_value += parse_price(lead.get('price'))
            
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Omzet Uren ({selected_month})", f"€ {month_revenue:,.2f}")
        m2.metric(f"Gewerkte Uren ({selected_month})", f"{month_hours:.1f} uur")
        m3.metric("Totaal Deals Geland 🎉", f"€ {pipeline_value:,.2f}")
        
        st.divider()
        
        # 4. GRAFIEK
        st.subheader("📈 Omzetverloop per Maand")
        if not df.empty:
            chart_data = df.groupby('Maand')['Totaal'].sum()
            st.line_chart(chart_data, color="#2196F3")
        else:
            st.info("Nog geen data voor de grafiek.")
            
    else:
        st.info("💡 Tip: Maak een tabblad 'Uren' aan in Google Sheets en log je uren om hier grafieken te zien.")
        
        # Laat toch de Pipeline waarde zien, ook als er nog geen uren zijn
        pipeline_value = 0.0
        if 'leads_data' in st.session_state:
            for lead in st.session_state['leads_data']['col3']: 
                pipeline_value += parse_price(lead.get('price'))
        st.metric("Totaal Deals Geland 🎉", f"€ {pipeline_value:,.2f}")

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
                web = st.text_input("Web")
                pri = st.text_input("€")
                not_ = st.text_area("Note")
                if st.form_submit_button("Toevoegen"):
                    if not comp: st.error("Naam!")
                    else:
                        ni = {'id': str(uuid.uuid4()), 'name': comp, 'contact': cont, 'email': mail, 'phone': tel, 'website': web, 'price': pri, 'notes': not_}
                        st.session_state['leads_data']['col1'].insert(0, ni)
                        save_pipeline_data(st.session_state['leads_data'])
                        st.session_state['board_key'] += 1; st.rerun()
        if st.button("🗑️ Prullenbak Legen"):
            st.session_state['leads_data']['trash'] = []; save_pipeline_data(st.session_state['leads_data']); st.session_state['board_key'] += 1; st.rerun()
        c1, c2 = st.columns(2)
        if c1.button("🔄"): st.cache_resource.clear(); del st.session_state['leads_data']; st.rerun()
        if c2.button("🛠️"): fix_missing_ids()

    cols = [('col1', 'Te benaderen'), ('col2', 'Opgevolgd'), ('col3', 'Geland 🎉'), ('col4', 'Geen interesse'), ('trash', 'Prullenbak 🗑️')]
    k_data = []
    all_leads = []
    for k, name in cols:
        items = [f"{l['name']}{(' | ' + l['price']) if l['price'] else ''}" for l in st.session_state['leads_data'][k]]
        all_leads.extend(st.session_state['leads_data'][k])
        k_data.append({'header': name, 'items': items})

    s_data = sort_items(k_data, multi_containers=True, key=f"board_{st.session_state['board_key']}")

    if len(s_data) == 5:
        new_st = {}
        lookup = {f"{l['name']}{(' | ' + l['price']) if l['price'] else ''}": l for l in all_leads}
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
            fil = st.selectbox("🔍 Filter:", ["Alles"] + [n for _, n in cols])
            f_leads = all_leads if fil == "Alles" else st.session_state['leads_data'][next((k for k, n in cols if n == fil), 'col1')]
            d_opts = {f"{l['name']}": l['id'] for l in f_leads}
            sel = next((l for l in all_leads if l['id'] == d_opts[st.selectbox("Deal:", list(d_opts.keys()))]), None) if d_opts else None
        if sel:
            with c_inf:
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    with c1: st.markdown(f"### {sel['name']}"); st.markdown(f"<h1 style='color:#fff;margin-top:-10px'>{sel['price']}</h1>", unsafe_allow_html=True)
                    with c2: 
                        st.write(f"👤 {sel.get('contact','-')}"); st.write(f"📧 {sel.get('email','-')}"); st.write(f"☎️ {sel.get('phone','-')}")
                        if sel.get('website'): st.markdown(f"🌐 [{sel['website']}]({'https://'+sel['website'] if not sel['website'].startswith('http') else sel['website']})")
                    st.markdown("---"); st.info(sel.get('notes') or "Geen notities.")

# ================= TAB 3: TAKEN =================
with tab_tasks:
    st.header("✅ Projectmanagement")
    
    c_filt1, c_filt2 = st.columns(2)
    with c_filt1:
        klant_filter = st.selectbox("📂 Filter op Klant:", ["Alle Projecten"] + all_companies)
    with c_filt2:
        cat_filter = st.selectbox("🏷️ Filter op Categorie:", ["Alle Categorieën"] + TASK_CATEGORIES)
    
    with st.expander(f"➕ Taak toevoegen", expanded=False):
        with st.form("new_task"):
            ca, cb = st.columns(2)
            with ca:
                n_klant = klant_filter if klant_filter != "Alle Projecten" else st.selectbox("Klant", all_companies)
                n_taak = st.text_input("Taak")
                n_cat = st.selectbox("Categorie", TASK_CATEGORIES)
            with cb:
                n_date = st.date_input("Deadline", date.today())
                n_prio = st.selectbox("Prioriteit", ["🔥 Hoog", "⏺️ Midden", "💤 Laag"])
                n_note = st.text_area("Notities")
            
            if st.form_submit_button("Opslaan"):
                add_task(n_klant, n_taak, n_cat, n_date, n_prio, n_note)
                st.success("Opgeslagen!"); st.rerun()

    all_tasks = load_tasks()
    disp_tasks = all_tasks
    if klant_filter != "Alle Projecten": disp_tasks = [t for t in disp_tasks if t.get('Klant') == klant_filter]
    if cat_filter != "Alle Categorieën": disp_tasks = [t for t in disp_tasks if t.get('Categorie') == cat_filter]

    if not disp_tasks: st.info(f"Geen taken gevonden.")
    else:
        prio_map = {"🔥 Hoog": 1, "⏺️ Midden": 2, "💤 Laag": 3}
        disp_tasks.sort(key=lambda x: (str(x.get('Status')).upper() == 'TRUE', prio_map.get(x.get('Prioriteit'), 2), x.get('Deadline')))
        
        st.write(f"**{len(disp_tasks)} taken**")
        for task in disp_tasks:
            if not task.get('ID'): continue
            is_done = str(task.get('Status')).upper() == 'TRUE'
            opacity = "0.5" if is_done else "1.0"
            strike = "text-decoration: line-through;" if is_done else ""
            
            with st.container(border=True):
                c_check, c_info, c_meta = st.columns([0.5, 5.5, 3])
                with c_check:
                    if st.checkbox("", value=is_done, key=f"chk_{task['ID']}") != is_done:
                        toggle_task_status(task['ID'], str(task.get('Status')).upper()); st.rerun()
                with c_info:
                    klant_lbl = f"<span style='color:#2196F3;font-weight:bold'>{task.get('Klant')}</span> | " if klant_filter == "Alle Projecten" else ""
                    st.markdown(f"<div style='opacity:{opacity};{strike}'>{klant_lbl}<strong>{task['Taak']}</strong></div>", unsafe_allow_html=True)
                    if task.get('Notities'): st.caption(f"📝 {task['Notities']}")
                with c_meta:
                    prio_raw = task.get('Prioriteit', "⏺️ Midden")
                    if prio_raw not in ["🔥 Hoog", "⏺️ Midden", "💤 Laag"]: prio_raw = "⏺️ Midden"
                    prio_color = "#ff4b4b" if "Hoog" in prio_raw else "#ffa421" if "Midden" in prio_raw else "#00c0f2"
                    st.markdown(f"<div style='display:flex;gap:10px;align-items:center;justify-content:flex-end;opacity:{opacity}'><span style='color:{prio_color};font-weight:bold;font-size:0.9em'>{prio_raw}</span><span style='font-weight:700;color:#eee'>📅 {task['Deadline']}</span><span style='background:#333;padding:4px 8px;border-radius:4px;font-size:0.8em;border:1px solid #444'>{task['Categorie']}</span></div>", unsafe_allow_html=True)
                
                with st.expander("✏️ Bewerk"):
                    with st.form(f"edit_{task['ID']}"):
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            e_klant = st.selectbox("Klant", all_companies, index=all_companies.index(task['Klant']) if task['Klant'] in all_companies else 0)
                            e_taak = st.text_input("Taak", task['Taak'])
                            e_cat = st.selectbox("Categorie", TASK_CATEGORIES, index=TASK_CATEGORIES.index(task['Categorie']) if task['Categorie'] in TASK_CATEGORIES else 0)
                        with ec2:
                            d_val = datetime.strptime(task['Deadline'], "%Y-%m-%d").date() if task['Deadline'] else date.today()
                            e_date = st.date_input("Deadline", d_val)
                            p_safe = task.get('Prioriteit', "⏺️ Midden"); 
                            if p_safe not in ["🔥 Hoog", "⏺️ Midden", "💤 Laag"]: p_safe = "⏺️ Midden"
                            e_prio = st.selectbox("Prioriteit", ["🔥 Hoog", "⏺️ Midden", "💤 Laag"], index=["🔥 Hoog", "⏺️ Midden", "💤 Laag"].index(p_safe))
                        e_note = st.text_area("Notities", task.get('Notities', ''))
                        if st.form_submit_button("Opslaan"):
                            new_data = {'Klant': e_klant, 'Taak': e_taak, 'Categorie': e_cat, 'Deadline': e_date, 'Prioriteit': e_prio, 'Notities': e_note}
                            update_task_data(task['ID'], new_data); st.success("Opgeslagen!"); st.rerun()

    st.divider()
    if st.button("🧹 Voltooide taken verwijderen"):
        delete_completed_tasks(); st.success("Opgeruimd!"); st.rerun()

# ================= TAB 4: UREN =================
with tab_hours:
    st.header("⏱️ Urenregistratie")
    st.markdown(f"**Vast Tarief:** €{HOURLY_RATE} / uur")
    
    with st.container(border=True):
        st.subheader("✍️ Tijd Schrijven")
        with st.form("log_time"):
            hc1, hc2, hc3 = st.columns([2, 1, 2])
            with hc1:
                h_klant = st.selectbox("Klant", all_companies)
                h_datum = st.date_input("Datum", date.today())
            with hc2:
                h_uren = st.number_input("Uren", min_value=0.0, step=0.25, format="%.2f")
            with hc3:
                h_desc = st.text_input("Omschrijving (Wat heb je gedaan?)")
                submit_hours = st.form_submit_button("⏱️ Log Tijd", use_container_width=True)
            
            if submit_hours:
                if h_uren > 0:
                    log_time(h_klant, h_datum, h_uren, h_desc)
                    st.success(f"{h_uren} uur geschreven op {h_klant}!")
                    st.rerun()
                else: st.error("Vul een aantal uren in!")

    st.divider()
    h_filter = st.selectbox("🔍 Filter overzicht op klant:", ["Alle Klanten"] + all_companies)
    all_hours = load_hours()
    filtered_hours = [h for h in all_hours if h.get('Klant') == h_filter] if h_filter != "Alle Klanten" else all_hours

    total_hours = sum([float(h.get('Uren', 0)) for h in filtered_hours])
    total_money = sum([float(h.get('Totaal', 0)) for h in filtered_hours])

    m1, m2 = st.columns(2)
    m1.metric("Totaal Uren", f"{total_hours:.2f} uur")
    m2.metric("Totale Waarde", f"€ {total_money:,.2f}")

    if filtered_hours:
        st.markdown("### 📜 Logboek")
        for entry in reversed(filtered_hours):
            with st.container(border=True):
                col_a, col_b, col_c, col_d = st.columns([1.5, 4, 1.5, 1])
                with col_a:
                    st.caption(entry['Datum'])
                    st.write(f"**{entry['Klant']}**")
                with col_b: st.write(entry['Omschrijving'])
                with col_c: st.markdown(f"**{entry['Uren']}u** (€{entry['Totaal']})")
                with col_d:
                    if st.button("🗑️", key=f"del_h_{entry['ID']}"):
                        delete_hour_entry(entry['ID']); st.rerun()
    else: st.info("Nog geen uren geschreven voor deze selectie.")
