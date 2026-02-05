import streamlit as st
from streamlit_sortables import sort_items
import uuid
import json
import os

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS STYLING (DE VEILIGE MANIER) ---
st.markdown("""
    <style>
    /* Algemene achtergrond */
    .stApp {
        background-color: #1e1e1e;
    }

    /* HIER FORCEREN WE DE KOLOMMEN NAAST ELKAAR 
       We gebruiken !important om de standaardinstellingen te overschrijven.
    */
    div[class*="stSortable"] {
        display: flex !important;
        flex-direction: row !important; /* Naast elkaar */
        gap: 20px !important;
        overflow-x: auto !important;
        padding-bottom: 20px !important;
    }
    
    /* Zorg dat de kolommen zelf verticaal stapelen (items onder elkaar) */
    div[class*="stSortable"] > div {
        display: flex !important;
        flex-direction: column !important;
        min-width: 250px !important; /* Minimale breedte per kolom */
        width: 300px !important;
    }

    /* Styling van de kaartjes zelf */
    div[class*="stSortable"] > div > div {
        background-color: #262730 !important;
        color: white !important;
        border: 1px solid #444 !important;
        border-radius: 6px !important;
        margin-bottom: 10px !important;
        padding: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATABASE FUNCTIES (OPSLAAN & LADEN) ---
DATA_FILE = "leads_database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Fout bij opslaan: {e}")

# --- 4. DATA INITIALISATIE ---
def create_lead(company, contact, price, notes):
    return {
        'id': str(uuid.uuid4()),
        'name': company,
        'contact': contact,
        'price': price,
        'notes': notes
    }

# Check of we data moeten laden
if 'leads_data' not in st.session_state:
    saved_data = load_data()
    if saved_data:
        st.session_state['leads_data'] = saved_data
        st.toast("📂 Data hersteld!")
    else:
        st.session_state['leads_data'] = {
            'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []
        }

if 'board_key' not in st.session_state:
    st.session_state['board_key'] = 0

# --- 5. SIDEBAR ---
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
                save_data(st.session_state['leads_data']) # Direct opslaan
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
        # Markdown tekst (Veilig, geen HTML/CSS objecten die crashen)
        card_text = f"**{lead['name']}**\n👤 {lead['contact']} | 💰 {lead['price']}\n📝 {lead['notes']}"
        items.append(f"{card_text}:::{lead['id']}")
    kanban_data.append({'header': display_name, 'items': items})

# HET BORD TEKENEN
# Let op: ik heb 'custom_style' WEGGEHAALD. Dit voorkomt Error #31.
# De styling gebeurt nu puur via de CSS bovenaan dit bestand.
sorted_data = sort_items(
    kanban_data, 
    multi_containers=True, 
    key=f"board_{st.session_state['board_key']}"
)

# --- 7. UPDATE LOGICA ---
if len(sorted_data) == 5:
    new_state = {}
    all_leads = {}
    
    # Maak lookup table
    for col in st.session_state['leads_data'].values():
        for lead in col:
            all_leads[lead['id']] = lead
            
    # Bouw nieuwe state
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

    # Check verandering
    current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
    new_ids = [[l['id'] for l in col] for col in new_state.values()]
    
    if current_ids != new_ids:
        st.session_state['leads_data'] = new_state
        save_data(new_state) # Opslaan na slepen
        st.rerun()
