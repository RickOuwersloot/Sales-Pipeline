import streamlit as st
from streamlit_sortables import sort_items
import uuid
import json
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURATIE ---
st.set_page_config(
    page_title="RO Marketing Pipeline", 
    page_icon="Logo RO Marketing.png", 
    layout="wide", 
    initial_sidebar_state="auto" 
)

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    /* A. FONTS IMPORTEREN */
    @import url('https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=Montserrat:wght@400;600;700&display=swap');

    /* B. ALGEMENE STYLING (Veilige modus voor icoontjes) */
    .stApp { font-family: 'Montserrat', sans-serif !important; }
    p, input, textarea, .stMarkdown { font-family: 'Montserrat', sans-serif !important; }
    .stButton > button p { font-family: 'Montserrat', sans-serif !important; }

    /* C. KOPTEKSTEN */
    h1, h2, h3, .stHeading, .st-emotion-cache-10trblm {
        font-family: 'Dela Gothic One', cursive !important;
        letter-spacing: 1px;
        font-weight: 400 !important;
    }

    /* D. LAYOUT & KLEUREN */
    .stApp { background-color: #0E1117; }
    .block-container { max_width: 100% !important; padding: 2rem; }
    
    /* E. SIDEBAR BREEDTE (HIER PAS JE HEM AAN!) */
    section[data-testid="stSidebar"] {
        width: 400px !important; /* Pas dit getal aan (bv. 350px, 450px) */
        min-width: 400px !important;
    }

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
    
    /* G. KAARTJES STYLING */
    div[class*="stSortable"] > div > div {
        background-color: #2b313e !important;
        color: white !important;
        border: 1px solid #2196F3 !important;
        border-left: 6px solid #2196F3 !important; 
        border-radius: 6px !important;
        padding: 12px !important;
        margin-bottom: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
        font-weight: 500 !important;
    }
    
    div[class*="stSortable"] > div > div:hover {
        background-color: #363c4e !important;
        border-color: #64b5f6 !important;
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. GOOGLE SHEETS VERBINDING ---
@st.cache_resource
def get_google_sheet():
    try:
        json_text = st.secrets["service_account"]
        creds_dict = json.loads(json_text, strict=False)
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open("MijnSalesCRM").sheet1 
        return sheet
        
    except Exception as e:
        st.error(f"Fout bij verbinden met Google: {e}")
        return None

def fix_missing_ids():
    """Checkt de sheet op lege IDs en vult ze in."""
    try:
        sheet = get_google_sheet()
        if not sheet: return
        
        records = sheet.get_all_records()
        updated_rows = [['Status', 'Bedrijf', 'Prijs', 'Contact', 'Email', 'Telefoon', 'Notities', 'ID']]
        
        existing_ids = set()
        changes_made = False
        
        for row in records:
            current_id = str(row.get('ID', '')).strip()
            
            if not current_id or current_id in existing_ids:
                new_id = str(uuid.uuid4())
                row['ID'] = new_id
                changes_made = True
            else:
                new_id = current_id
                
            existing_ids.add(new_id)
            
            updated_rows.append([
                row.get('Status', 'Te benaderen'),
                row.get('Bedrijf', ''),
                row.get('Prijs', ''),
                row.get('Contact', ''),
                row.get('Email', ''),
                row.get('Telefoon', ''),
                row.get('Notities', ''),
                new_id
            ])
            
        if changes_made:
            sheet.clear()
            sheet.update(updated_rows)
            st.success("✅ IDs gerepareerd! De app herlaadt nu...")
            st.cache_resource.clear()
            if 'leads_data' in st.session_state: del st.session_state['leads_data']
            st.rerun()
        else:
            st.toast("👍 Alle IDs waren al in orde.")
            
    except Exception as e:
        st.error(f"Fout bij repareren: {e}")

def load_data_from_sheet():
    try:
        sheet = get_google_sheet()
        if not sheet: return None
        records = sheet.get_all_records()
        
        data_structure = {
            'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []
        }
        status_map = {
            'Te benaderen': 'col1', 'Opgevolgd': 'col2',
            'Geland': 'col3', 'Geen interesse': 'col4', 'Prullenbak': 'trash'
        }
        
        for row in records:
            if row.get('Bedrijf'):
                raw_id = str(row.get('ID', '')).strip()
                safe_id = raw_id if raw_id else str(uuid.uuid4())
                
                lead = {
                    'id': safe_id,
                    'name': row.get('Bedrijf'),
                    'price': row.get('Prijs'),
                    'contact': row.get('Contact'),
                    'email': row.get('Email'),
                    'phone': row.get('Telefoon'),
                    'notes': row.get('Notities')
                }
                status = row.get('Status', 'Te benaderen')
                col_key = status_map.get(status, 'col1')
                data_structure[col_key].append(lead)
        return data_structure
    except Exception as e:
        return None

def save_data_to_sheet(leads_data):
    try:
        sheet = get_google_sheet()
        if not sheet: return

        rows_to_write = [['Status', 'Bedrijf', 'Prijs', 'Contact', 'Email', 'Telefoon', 'Notities', 'ID']]
        col_map = {
            'col1': 'Te benaderen', 'col2': 'Opgevolgd',
            'col3': 'Geland', 'col4': 'Geen interesse', 'trash': 'Prullenbak'
        }
        
        for col_key, items in leads_data.items():
            status_text = col_map.get(col_key, 'Te benaderen')
            for item in items:
                row = [
                    status_text,
                    item.get('name', ''), item.get('price', ''),
                    item.get('contact', ''), item.get('email', ''),
                    item.get('phone', ''), item.get('notes', ''),
                    item.get('id', str(uuid.uuid4()))
                ]
                rows_to_write.append(row)
        
        sheet.clear()
        sheet.update(rows_to_write)
    except Exception as e:
        st.error(f"Kon niet opslaan: {e}")

# --- 4. INITIALISATIE ---
if 'leads_data' not in st.session_state:
    with st.spinner('Verbinding maken met Google Sheets...'):
        loaded = load_data_from_sheet()
        if loaded:
            st.session_state['leads_data'] = loaded
        else:
            st.session_state['leads_data'] = {'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []}

if 'board_key' not in st.session_state:
    st.session_state['board_key'] = 0

def create_lead_obj(company, contact, email, phone, price, notes):
    return {
        'id': str(uuid.uuid4()),
        'name': company, 'contact': contact, 'email': email, 
        'phone': phone, 'price': price, 'notes': notes
    }

# --- 5. SIDEBAR ---
with st.sidebar:
    try:
        st.image("Logo RO Marketing.png", width=150)
    except:
        st.warning("Logo uploaden!")

    with st.expander("➕ Nieuwe Deal Toevoegen", expanded=True):
        with st.form("add_lead_form", clear_on_submit=True):
            company = st.text_input("Bedrijfsnaam *")
            contact = st.text_input("Contactpersoon")
            email = st.text_input("Emailadres")
            phone = st.text_input("Telefoonnummer")
            price = st.text_input("Waarde (bv. €1500)")
            notes = st.text_area("Notities")
            
            submitted = st.form_submit_button("Toevoegen")
            
            if submitted:
                if not company:
                    st.error("Vul een naam in!")
                else:
                    new_item = create_lead_obj(company, contact, email, phone, price, notes)
                    st.session_state['leads_data']['col1'].insert(0, new_item)
                    save_data_to_sheet(st.session_state['leads_data'])
                    st.session_state['board_key'] += 1
                    st.rerun()

    if len(st.session_state['leads_data']['trash']) > 0:
        st.divider()
        if st.button("🗑️ Prullenbak Legen"):
            st.session_state['leads_data']['trash'] = []
            save_data_to_sheet(st.session_state['leads_data'])
            st.session_state['board_key'] += 1
            st.rerun()
            
    st.divider()
    
    col_ref, col_fix = st.columns(2)
    with col_ref:
        if st.button("🔄 Reload"):
            st.cache_resource.clear()
            if 'leads_data' in st.session_state: del st.session_state['leads_data']
            st.rerun()
    with col_fix:
        if st.button("🛠️ Fix IDs"):
            fix_missing_ids()

# --- 6. HET BORD ---
st.title("🚀 RO Marketing Sales Pipeline")

columns_config = [
    ('col1', 'Te benaderen'),
    ('col2', 'Opgevolgd'),
    ('col3', 'Geland 🎉'),
    ('col4', 'Geen interesse'),
    ('trash', 'Prullenbak 🗑️')
]

kanban_data = []
all_leads_list = []

for db_key, display_name in columns_config:
    items = []
    for lead in st.session_state['leads_data'][db_key]:
        price_part = f" | {lead['price']}" if lead['price'] else ""
        card_text = f"{lead['name']}{price_part}"
        items.append(card_text)
        all_leads_list.append(lead)
    kanban_data.append({'header': display_name, 'items': items})

sorted_data = sort_items(
    kanban_data, 
    multi_containers=True, 
    key=f"board_{st.session_state['board_key']}"
)

# --- 7. UPDATE LOGICA ---
if len(sorted_data) == 5:
    new_state = {}
    lead_lookup = {}
    
    for lead in all_leads_list:
        price_part = f" | {lead['price']}" if lead['price'] else ""
        key = f"{lead['name']}{price_part}"
        lead_lookup[key] = lead
            
    for i, col_data in enumerate(sorted_data):
        db_key = columns_config[i][0]
        new_col_items = []
        for item_str in col_data['items']:
            if item_str in lead_lookup:
                new_col_items.append(lead_lookup[item_str])
        new_state[db_key] = new_col_items

    current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
    new_ids = [[l['id'] for l in col] for col in new_state.values()]
    
    if current_ids != new_ids:
        st.session_state['leads_data'] = new_state
        save_data_to_sheet(new_state)
        st.rerun()

# --- 8. DETAILS ---
st.divider()
if len(all_leads_list) > 0:
    st.subheader("📋 Deal Details")
    
    c_sel, c_inf = st.columns([1, 2])
    
    with c_sel:
        filter_options = ["Alles tonen"] + [name for _, name in columns_config]
        selected_filter = st.selectbox("🔍 Filter op fase:", filter_options)
        
        filtered_leads = []
        if selected_filter == "Alles tonen":
            filtered_leads = all_leads_list
        else:
            target_col_key = next((k for k, n in columns_config if n == selected_filter), None)
            if target_col_key:
                filtered_leads = st.session_state['leads_data'][target_col_key]

        deal_options = {f"{l['name']}": l['id'] for l in filtered_leads}
        
        if not deal_options:
            st.info("Geen deals gevonden in deze fase.")
            sel_deal = None
        else:
            sel_name = st.selectbox("Selecteer deal:", list(deal_options.keys()))
            sel_id = deal_options[sel_name]
            sel_deal = next((l for l in all_leads_list if l['id'] == sel_id), None)
    
    if sel_deal:
        with c_inf:
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"### {sel_deal['name']}")
                    st.markdown(f"<h1 style='color: #fff; font-size: 2.5rem; font-weight: 800; margin-top: -10px;'>{sel_deal['price']}</h1>", unsafe_allow_html=True)
                with c2:
                    st.write(f"👤 **{sel_deal.get('contact', '-')}")
                    st.write(f"📧 {sel_deal.get('email', '-')}")
                    st.write(f"☎️ {sel_deal.get('phone', '-')}")
                st.markdown("---")
                st.info(sel_deal['notes'] if sel_deal['notes'] else "Geen notities.")
