import streamlit as st
from streamlit_sortables import sort_items
import uuid
import json
import os

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #1e1e1e; }
    
    /* Layout: Kolommen naast elkaar */
    div[class*="stSortable"] {
        display: flex !important;
        flex-direction: row !important; 
        gap: 20px !important;
        overflow-x: auto !important;
        padding-bottom: 20px !important;
    }
    
    /* Kolommen zelf: verticaal stapelen */
    div[class*="stSortable"] > div {
        display: flex !important;
        flex-direction: column !important;
        min-width: 250px !important;
        width: 280px !important;
    }

    /* Kaartjes styling */
    div[class*="stSortable"] > div > div {
        background-color: #262730 !important;
        color: white !important;
        border: 1px solid #444 !important;
        border-radius: 6px !important;
        margin-bottom: 10px !important;
        padding: 12px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATABASE (OPSLAAN & LADEN) ---
DATA_FILE = "leads_database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: return None
    return None

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f: json.dump(data, f)
    except: pass

# --- 4. DATA INITIALISATIE ---
def create_lead(company, contact, price, notes):
    return {
        'id': str(uuid.uuid4()),
        'name': company, 'contact': contact, 'price': price, 'notes': notes
    }

if 'leads_data' not in st.session_state:
    saved_data = load_data()
    st.session_state['leads_data'] = saved_data if saved_data else {
        'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []
    }

if 'board_key' not in st.session_state:
    st.session_state['board_key'] = 0

# --- 5. SIDEBAR (FORMULIER & OPTIES) ---
with st.sidebar:
    st.title("Instellingen")
    
    # --- HIER IS DE MAGIE: DE SCHAKELAAR ---
    show_details = st.toggle("🔍 Toon details op kaartjes", value=False)
    st.divider()

    st.header("➕ Nieuwe Deal")
    with st.form("add_lead_form", clear_on_submit=True):
        company = st.text_input("Bedrijfsnaam")
        contact = st.text_input("Contactpersoon")
        price = st.text_input("Waarde (bv. €500)")
        notes = st.text_area("Notities")
        submitted = st.form_submit_button("Toevoegen")
        
        if submitted:
            if not company:
                st.error("Naam is verplicht!")
            else:
                new_item = create_lead(company, contact, price, notes)
                st.session_state['leads_data']['col1'].insert(0, new_item)
                save_data(st.session_state['leads_data'])
                st.session_state['board_key'] += 1
                st.rerun()

    if len(st.session_state['leads_data']['trash']) > 0:
        st.divider()
        if st.button("🗑️ Prullenbak Legen"):
            st.session_state['leads_data']['trash'] = []
            save_data(st.session_state['leads_data'])
            st.session_state['board_key'] += 1
            st.rerun()

# --- 6. HET BORD ---
st.title("🚀 Sales Pipeline")

columns_config = [
    ('col1', 'Te benaderen'),
    ('col2', 'Opgevolgd'),
    ('col3', 'Geland 🎉'),
    ('col4', 'Geen interesse'),
    ('trash', 'Prullenbak 🗑️')
]

kanban_data = []
for db_key, display_name in columns_config:
    items = []
    for lead in st.session_state['leads_data'][db_key]:
        # HIER BEPALEN WE WAT JE ZIET
        if show_details:
            # Uitgeklapte weergave
            card_text = f"**{lead['name']}**\n💰 {lead['price']}\n👤 {lead['contact']}\n📝 {lead['notes']}"
        else:
            # Compacte weergave (Alleen naam + prijs)
            # Als er geen prijs is, alleen de naam.
            price_tag = f" | {lead['price']}" if lead['price'] else ""
            card_text = f"**{lead['name']}**{price_tag}"
            
        items.append(f"{card_text}:::{lead['id']}")
    kanban_data.append({'header': display_name, 'items': items})

# Bord tekenen
sorted_data = sort_items(
    kanban_data, 
    multi_containers=True, 
    key=f"board_{st.session_state['board_key']}"
)

# --- 7. UPDATE LOGICA ---
if len(sorted_data) == 5:
    new_state = {}
    all_leads = {}
    for col in st.session_state['leads_data'].values():
        for lead in col: all_leads[lead['id']] = lead
            
    for i, col_data in enumerate(sorted_data):
        db_key = columns_config[i][0]
        new_col_items = []
        for item_str in col_data['items']:
            parts = item_str.split(':::')
            if len(parts) > 1 and parts[-1] in all_leads:
                new_col_items.append(all_leads[parts[-1]])
        new_state[db_key] = new_col_items

    # Check wijzigingen
    current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
    new_ids = [[l['id'] for l in col] for col in new_state.values()]
    
    if current_ids != new_ids:
        st.session_state['leads_data'] = new_state
        save_data(new_state)
        st.rerun()
