import streamlit as st
from streamlit_sortables import sort_items
import uuid
import json
import os

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS LAYOUT (DEFINITIEVE VERSIE) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #1e1e1e;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATABASE FUNCTIES (OPSLAAN & LADEN) ---
DATA_FILE = "leads_database.json"

def load_data():
    """Lees de database uit het bestand als het bestaat."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return None # Bestand corrupt of leeg
    return None

def save_data(data):
    """Schrijf de data direct naar het bestand."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --- 4. DATA INITIALISATIE ---
def create_lead(company, contact, price, notes):
    return {
        'id': str(uuid.uuid4()),
        'name': company,
        'contact': contact,
        'price': price,
        'notes': notes
    }

# We kijken eerst of er een opgeslagen bestand is
if 'leads_data' not in st.session_state:
    saved_data = load_data()
    if saved_data:
        st.session_state['leads_data'] = saved_data
        st.toast("📂 Oude gegevens geladen!")
    else:
        # Start met lege indeling als er niks is
        st.session_state['leads_data'] = {
            'col1': [], 
            'col2': [], 
            'col3': [], 
            'col4': [], 
            'trash': []
        }

if 'board_key' not in st.session_state:
    st.session_state['board_key'] = 0

# --- 5. SIDEBAR (FORMULIER) ---
with st.sidebar:
    st.header("➕ Nieuwe Deal")
    with st.form("add_lead_form", clear_on_submit=True):
        company = st.text_input("Bedrijfsnaam")
        contact = st.text_input("Contactpersoon")
        price = st.text_input("Waarde")
        notes = st.text_area("Notities")
        submitted = st.form_submit_button("Toevoegen")
        
        if submitted:
            if not company:
                st.error("Vul een naam in!")
            else:
                new_item = create_lead(company, contact, price, notes)
                st.session_state['leads_data']['col1'].insert(0, new_item)
                
                # DIRECT OPSLAAN
                save_data(st.session_state['leads_data'])
                
                st.session_state['board_key'] += 1
                st.rerun()

    if len(st.session_state['leads_data']['trash']) > 0:
        st.divider()
        if st.button("🗑️ Prullenbak Legen"):
            st.session_state['leads_data']['trash'] = []
            
            # DIRECT OPSLAAN
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
        # Markdown layout (Veilig & Netjes)
        card_text = f"**{lead['name']}**\n👤 {lead['contact']} | 💰 {lead['price']}\n📝 {lead['notes']}"
        items.append(f"{card_text}:::{lead['id']}")
    kanban_data.append({'header': display_name, 'items': items})

# CSS voor Horizontale Layout (CamelCase voor React)
custom_css = {
    "container": {
        "display": "flex",
        "flexDirection": "row", 
        "alignItems": "flex-start",
        "justifyContent": "flex-start",
        "gap": "20px",
        "overflowX": "auto",
        "width": "100%"
    },
    "card": {
        "backgroundColor": "#262730",
        "color": "white",
        "borderRadius": "6px",
        "padding": "10px",
        "marginBottom": "10px",
        "border": "1px solid #444"
    }
}

sorted_data = sort_items(
    kanban_data, 
    multi_containers=True, 
    custom_style=custom_css,
    key=f"board_{st.session_state['board_key']}"
)

# --- 7. UPDATE LOGICA & OPSLAAN ---
if len(sorted_data) == 5:
    new_state = {}
    all_leads = {}
    for col in st.session_state['leads_data'].values():
        for lead in col:
            all_leads[lead['id']] = lead
            
    for i, col_data in enumerate(sorted_data):
        db_key = columns_config[i][0]
        new_col_items = []
        for item_str in col_data['items']:
            parts = item_str.split(':::')
            if len(parts) > 1:
                item_id = parts[-1]
                if item_id in all_leads:
                    new_col_items.append(all_leads[item_id])
        new_state[db_key] = new_col_items

    current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
    new_ids = [[l['id'] for l in col] for col in new_state.values()]
    
    if current_ids != new_ids:
        st.session_state['leads_data'] = new_state
        
        # DIRECT OPSLAAN BIJ ELKE VERPLAATSING
        save_data(new_state)
        
        st.rerun()
