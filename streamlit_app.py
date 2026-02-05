import streamlit as st
from streamlit_sortables import sort_items
import uuid
import json
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="RO Marketing Pipeline", page_icon="Logo RO Marketing.png", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS STYLING (THE BLUE FORCE FIX) ---
st.markdown("""
    <style>
    .stApp { background-color: #1e1e1e; }
    .block-container { max_width: 100% !important; padding: 2rem; }
    
    /* Layout: Banen naast elkaar */
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
    
    /* --- HIER ZIT DE FIX VOOR DE RODE KAARTJES --- */
    /* We targeten specifiek de kaartjes binnen de sortable div */
    div[class*="stSortable"] > div > div {
        background-color: #2b313e !important;   /* Donkerblauw/grijs (Geen Rood meer!) */
        color: white !important;                 /* Witte tekst */
        border: 1px solid #2196F3 !important;    /* Blauwe rand rondom */
        border-left: 6px solid #2196F3 !important; /* Dikke blauwe balk links */
        border-radius: 6px !important;
        padding: 12px !important;
        margin-bottom: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
        font-weight: 500 !important;
    }
    
    /* Als je eroverheen muist */
    div[class*="stSortable"] > div > div:hover {
        background-color: #363c4e !important;    /* Iets lichter blauw bij hover */
        border-color: #64b5f6 !important;        /* Lichtere rand */
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
                lead = {
                    'id': str(row.get('ID', uuid.uuid4())),
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
        st.warning("Upload 'Logo RO Marketing.png' naar GitHub!")

    st.header("➕ Nieuwe Deal")
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
    if st.button("🔄 Herlaad data uit Sheet"):
        st.cache_resource.clear()
        if 'leads_data' in st.session_state: del st.session_state['leads_data']
        st.rerun()

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
    deal_options = {f"{l['name']}": l['id'] for l in all_leads_list}
    
    c_sel, c_inf = st.columns([1, 2])
    with c_sel:
        sel_name = st.selectbox("Selecteer:", list(deal_options.keys()))
        sel_id = deal_options[sel_name]
        sel_deal = next((l for l in all_leads_list if l['id'] == sel_id), None)
    
    if sel_deal:
        with c_inf:
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"### {sel_deal['name']}")
                    st.write(f"**Waarde:** {sel_deal['price']}")
                with c2:
                    st.write(f"👤 **{sel_deal.get('contact', '-')}")
                    st.write(f"📧 {sel_deal.get('email', '-')}")
                    st.write(f"☎️ {sel_deal.get('phone', '-')}")
                st.markdown("---")
                st.info(sel_deal['notes'] if sel_deal['notes'] else "Geen notities.")
