import streamlit as st
from streamlit_sortables import sort_items
import uuid
import json
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

# --- 2. CSS STYLING (MET ALLE FIXES 🛠️) ---
st.markdown("""
    <style>
    /* A. FONTS IMPORTEREN */
    @import url('https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=Montserrat:wght@400;600;700&display=swap');

    /* B. ALGEMENE STYLING */
    .stApp { font-family: 'Montserrat', sans-serif !important; }
    p, input, textarea, .stMarkdown, h1, h2, h3, h4, h5, h6, .stSelectbox, .stTextInput, .stDateInput { 
        font-family: 'Montserrat', sans-serif !important; 
    }
    
    /* ICON SAVER FIX */
    button, i, span[class^="material-symbols"] { font-family: inherit !important; }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarExpandedControl"] button { font-family: "Source Sans Pro", sans-serif !important; }

    /* C. KOPTEKSTEN */
    h1, h2, h3, .stHeading, .st-emotion-cache-10trblm {
        font-family: 'Dela Gothic One', cursive !important;
        letter-spacing: 1px;
        font-weight: 400 !important;
    }

    /* D. LAYOUT & KLEUREN */
    .stApp { background-color: #0E1117; }
    .block-container { max_width: 100% !important; padding: 2rem; }
    
    /* TABBLADEN STYLING */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #25262b;
        border-radius: 5px 5px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2196F3 !important;
        color: white !important;
    }

    /* E. SIDEBAR BREEDTE */
    section[data-testid="stSidebar"] { width: 400px !important; min-width: 400px !important; }

    /* F. KANBAN LAYOUT */
    div[class*="stSortable"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        align-items: flex-start !important;
        gap: 15px !important;
        padding-bottom: 20px !important;
    }
    div[class*="stSortable"] > div {
        display: flex !important;
        flex-direction: column !important;
        flex: 0 0 auto !important;
        width: 300px !important;
        min-width: 300px !important;
        background-color: #25262b !important;
        border: 1px solid #333 !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }
    div[class*="stSortable"] div {
        background-color: #2b313e !important; color: white !important; border-radius: 6px !important;
    }
    div[class*="stSortable"] > div > div {
        border: 1px solid #2196F3 !important;
        border-left: 6px solid #2196F3 !important; 
        margin-bottom: 8px !important; padding: 12px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
    }
    div[class*="stSortable"] > div > div:hover {
        background-color: #363c4e !important; border-color: #64b5f6 !important; transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. GOOGLE SHEETS VERBINDING ---
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
        st.error(f"Fout bij verbinden met Google: {e}")
        return None

def get_sheet(sheet_name="Sheet1"):
    client = get_google_client()
    if client:
        try:
            return client.open("MijnSalesCRM").worksheet(sheet_name)
        except:
            st.error(f"Kan tabblad '{sheet_name}' niet vinden! Heb je die aangemaakt?")
            return None
    return None

# --- FUNCTIES VOOR PIPELINE ---
def load_pipeline_data():
    sheet = get_sheet("Sheet1") # Oude data zit hier
    if not sheet: return None
    records = sheet.get_all_records()
    data_structure = {'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []}
    status_map = {'Te benaderen': 'col1', 'Opgevolgd': 'col2', 'Geland': 'col3', 'Geen interesse': 'col4', 'Prullenbak': 'trash'}
    
    for row in records:
        if row.get('Bedrijf'):
            raw_id = str(row.get('ID', '')).strip()
            safe_id = raw_id if raw_id else str(uuid.uuid4())
            lead = {
                'id': safe_id, 'name': row.get('Bedrijf'), 'price': row.get('Prijs'),
                'contact': row.get('Contact'), 'email': row.get('Email'),
                'phone': row.get('Telefoon'), 'website': row.get('Website'), 'notes': row.get('Notities')
            }
            status = row.get('Status', 'Te benaderen')
            col_key = status_map.get(status, 'col1')
            data_structure[col_key].append(lead)
    return data_structure

def save_pipeline_data(leads_data):
    sheet = get_sheet("Sheet1")
    if not sheet: return
    rows_to_write = [['Status', 'Bedrijf', 'Prijs', 'Contact', 'Email', 'Telefoon', 'Website', 'Notities', 'ID']]
    col_map = {'col1': 'Te benaderen', 'col2': 'Opgevolgd', 'col3': 'Geland', 'col4': 'Geen interesse', 'trash': 'Prullenbak'}
    for col_key, items in leads_data.items():
        status_text = col_map.get(col_key, 'Te benaderen')
        for item in items:
            row = [status_text, item.get('name', ''), item.get('price', ''), item.get('contact', ''), item.get('email', ''), item.get('phone', ''), item.get('website', ''), item.get('notes', ''), item.get('id', str(uuid.uuid4()))]
            rows_to_write.append(row)
    sheet.clear()
    sheet.update(rows_to_write)

def fix_missing_ids():
    sheet = get_sheet("Sheet1")
    if not sheet: return
    records = sheet.get_all_records()
    updated_rows = [['Status', 'Bedrijf', 'Prijs', 'Contact', 'Email', 'Telefoon', 'Website', 'Notities', 'ID']]
    existing_ids = set()
    changes_made = False
    for row in records:
        current_id = str(row.get('ID', '')).strip()
        if not current_id or current_id in existing_ids:
            new_id = str(uuid.uuid4()); row['ID'] = new_id; changes_made = True
        else: new_id = current_id
        existing_ids.add(new_id)
        updated_rows.append([row.get('Status', 'Te benaderen'), row.get('Bedrijf', ''), row.get('Prijs', ''), row.get('Contact', ''), row.get('Email', ''), row.get('Telefoon', ''), row.get('Website', ''), row.get('Notities', ''), new_id])
    if changes_made:
        sheet.clear(); sheet.update(updated_rows); st.success("✅ IDs gerepareerd!"); st.cache_resource.clear(); st.rerun()
    else: st.toast("👍 IDs OK")

# --- FUNCTIES VOOR TAKEN ---
def load_tasks():
    sheet = get_sheet("Taken")
    if not sheet: return []
    records = sheet.get_all_records()
    return records

def add_task(taak, categorie, deadline, subtaken):
    sheet = get_sheet("Taken")
    if not sheet: return
    new_id = str(uuid.uuid4())
    # Status FALSE betekent: nog niet afgevinkt
    row = ["FALSE", taak, categorie, str(deadline), subtaken, new_id]
    sheet.append_row(row)

def toggle_task_status(task_id, current_status):
    sheet = get_sheet("Taken")
    if not sheet: return
    # We moeten de cel vinden. Dit is even een trick om rows te vinden.
    # Voor betere performance zou je cell objects gebruiken, maar dit is simpel:
    records = sheet.get_all_records()
    # Rij index vinden (header is rij 1, records beginnen bij rij 2 in sheet, index 0 in list)
    for i, row in enumerate(records):
        if str(row.get('ID')) == task_id:
            # Update de Status kolom (Kolom A = 1)
            new_val = "TRUE" if current_status == "FALSE" else "FALSE"
            sheet.update_cell(i + 2, 1, new_val)
            return

def delete_completed_tasks():
    sheet = get_sheet("Taken")
    if not sheet: return
    records = sheet.get_all_records()
    # We bouwen de lijst opnieuw op, zonder de 'TRUE' taken
    rows_to_keep = [['Status', 'Taak', 'Categorie', 'Deadline', 'Subtaken', 'ID']]
    for row in records:
        if str(row.get('Status')).upper() != "TRUE":
            rows_to_keep.append([
                row.get('Status'), row.get('Taak'), row.get('Categorie'),
                row.get('Deadline'), row.get('Subtaken'), row.get('ID')
            ])
    sheet.clear()
    sheet.update(rows_to_keep)

# --- 4. INITIALISATIE ---
if 'leads_data' not in st.session_state:
    loaded = load_pipeline_data()
    st.session_state['leads_data'] = loaded if loaded else {'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []}
if 'board_key' not in st.session_state: st.session_state['board_key'] = 0

# --- 5. APP LAYOUT MET TABS ---
st.title("🚀 RO Marketing CRM")

# Hier splitsen we de app in tweeën!
tab_pipeline, tab_tasks = st.tabs(["📊 Pipeline", "✅ Takenbeheer"])

# ==========================================
# TAB 1: DE PIPELINE (OUDE CODE)
# ==========================================
with tab_pipeline:
    # --- SIDEBAR (ALLEEN VOOR PIPELINE) ---
    with st.sidebar:
        try: st.image("Logo RO Marketing.png", width=150)
        except: st.warning("Logo uploaden!")
        
        st.markdown("### ➕ Pipeline Acties")
        with st.expander("Nieuwe Deal", expanded=False):
            with st.form("add_lead_form", clear_on_submit=True):
                company = st.text_input("Bedrijf *")
                contact = st.text_input("Contact")
                email = st.text_input("Email")
                phone = st.text_input("Tel")
                website = st.text_input("Web")
                price = st.text_input("€")
                notes = st.text_area("Note")
                if st.form_submit_button("Toevoegen"):
                    if not company: st.error("Naam nodig!")
                    else:
                        new_item = {'id': str(uuid.uuid4()), 'name': company, 'contact': contact, 'email': email, 'phone': phone, 'website': website, 'price': price, 'notes': notes}
                        st.session_state['leads_data']['col1'].insert(0, new_item)
                        save_pipeline_data(st.session_state['leads_data'])
                        st.session_state['board_key'] += 1
                        st.rerun()
        
        if len(st.session_state['leads_data']['trash']) > 0:
            if st.button("🗑️ Prullenbak Legen"):
                st.session_state['leads_data']['trash'] = []
                save_pipeline_data(st.session_state['leads_data'])
                st.session_state['board_key'] += 1
                st.rerun()
        
        c1, c2 = st.columns(2)
        if c1.button("🔄"): st.cache_resource.clear(); del st.session_state['leads_data']; st.rerun()
        if c2.button("🛠️ IDs"): fix_missing_ids()

    # --- HET BORD ---
    columns_config = [('col1', 'Te benaderen'), ('col2', 'Opgevolgd'), ('col3', 'Geland 🎉'), ('col4', 'Geen interesse'), ('trash', 'Prullenbak 🗑️')]
    kanban_data = []
    all_leads_list = []
    for db_key, display_name in columns_config:
        items = []
        for lead in st.session_state['leads_data'][db_key]:
            price_part = f" | {lead['price']}" if lead['price'] else ""
            items.append(f"{lead['name']}{price_part}")
            all_leads_list.append(lead)
        kanban_data.append({'header': display_name, 'items': items})

    sorted_data = sort_items(kanban_data, multi_containers=True, key=f"board_{st.session_state['board_key']}")

    if len(sorted_data) == 5:
        new_state = {}
        lead_lookup = {f"{l['name']}{(' | ' + l['price']) if l['price'] else ''}": l for l in all_leads_list}
        for i, col_data in enumerate(sorted_data):
            new_col_items = [lead_lookup[item_str] for item_str in col_data['items'] if item_str in lead_lookup]
            new_state[columns_config[i][0]] = new_col_items
        
        current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
        new_ids = [[l['id'] for l in col] for col in new_state.values()]
        if current_ids != new_ids:
            st.session_state['leads_data'] = new_state
            save_pipeline_data(new_state)
            st.rerun()

    # --- DETAILS ---
    st.divider()
    if len(all_leads_list) > 0:
        c_sel, c_inf = st.columns([1, 2])
        with c_sel:
            filter_options = ["Alles tonen"] + [name for _, name in columns_config]
            selected_filter = st.selectbox("🔍 Filter op fase:", filter_options)
            filtered_leads = all_leads_list if selected_filter == "Alles tonen" else st.session_state['leads_data'][next((k for k, n in columns_config if n == selected_filter), 'col1')]
            deal_options = {f"{l['name']}": l['id'] for l in filtered_leads}
            sel_deal = next((l for l in all_leads_list if l['id'] == deal_options[st.selectbox("Selecteer deal:", list(deal_options.keys()))]), None) if deal_options else None
        
        if sel_deal:
            with c_inf:
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"### {sel_deal['name']}")
                        st.markdown(f"<h1 style='color: #fff; margin-top: -10px;'>{sel_deal['price']}</h1>", unsafe_allow_html=True)
                    with c2:
                        st.write(f"👤 {sel_deal.get('contact', '-')}")
                        st.write(f"📧 {sel_deal.get('email', '-')}")
                        st.write(f"☎️ {sel_deal.get('phone', '-')}")
                        if sel_deal.get('website'):
                             st.markdown(f"🌐 [{sel_deal['website']}]({'https://' + sel_deal['website'] if not sel_deal['website'].startswith('http') else sel_deal['website']})")
                    st.markdown("---")
                    st.info(sel_deal['notes'] if sel_deal['notes'] else "Geen notities.")

# ==========================================
# TAB 2: TAKENBEHEER (NIEUW! ✨)
# ==========================================
with tab_tasks:
    st.header("✅ Mijn Takenlijst")
    
    # 1. Nieuwe Taak Toevoegen
    with st.expander("➕ Nieuwe Taak Aanmaken", expanded=False):
        with st.form("new_task_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                t_naam = st.text_input("Wat moet er gebeuren?")
                t_cat = st.selectbox("Categorie", ["Opvolging", "Administratie", "Meeting", "Koud Bellen", "Overig"])
            with col_b:
                t_date = st.date_input("Deadline", date.today())
                t_sub = st.text_area("Details / Subtaken")
            
            if st.form_submit_button("Taak Opslaan"):
                add_task(t_naam, t_cat, t_date, t_sub)
                st.success("Taak toegevoegd!")
                st.rerun()

    # 2. Taken Weergeven
    tasks = load_tasks()
    
    if not tasks:
        st.info("Je hebt nog geen taken. Geniet van je rust! 🏝️")
    else:
        # Sorteren: Eerst de niet-afgevinkte, dan op datum
        tasks.sort(key=lambda x: (x.get('Status') == 'TRUE', x.get('Deadline')))
        
        for task in tasks:
            is_done = str(task.get('Status')).upper() == 'TRUE'
            
            # Styling van het taak-blokje
            border_color = "#4CAF50" if is_done else "#2196F3"
            opacity = "0.6" if is_done else "1.0"
            
            with st.container(border=True):
                c_check, c_info, c_date = st.columns([1, 6, 2])
                
                with c_check:
                    # Checkbox logic
                    check_val = st.checkbox("", value=is_done, key=f"chk_{task['ID']}")
                    if check_val != is_done:
                        toggle_task_status(task['ID'], str(task.get('Status')).upper())
                        st.rerun()
                
                with c_info:
                    st.markdown(f"<div style='opacity: {opacity}'><strong>{task['Taak']}</strong> <span style='background:#333; padding:2px 6px; border-radius:4px; font-size:0.8em; margin-left:10px;'>{task['Categorie']}</span></div>", unsafe_allow_html=True)
                    if task.get('Subtaken'):
                        st.caption(f"📝 {task['Subtaken']}")
                
                with c_date:
                    st.markdown(f"<div style='opacity: {opacity}; text-align:right;'>📅 {task['Deadline']}</div>", unsafe_allow_html=True)

        st.divider()
        if st.button("🧹 Afgevinkte taken verwijderen"):
            delete_completed_tasks()
            st.success("Opgeruimd staat netjes!")
            st.rerun()
