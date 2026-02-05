import streamlit as st
from streamlit_sortables import sort_items
import uuid
import json
import os

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS STYLING (DE MAGISCHE TRUC) ---
st.markdown("""
    <style>
    /* Algemene achtergrond */
    .stApp { background-color: #1e1e1e; }

    /* LAYOUT: Kolommen naast elkaar */
    div[class*="stSortable"] {
        display: flex !important;
        flex-direction: row !important; 
        gap: 15px !important;
        overflow-x: auto !important;
        padding-bottom: 50px !important;
    }
    
    /* Kolommen: Items onder elkaar */
    div[class*="stSortable"] > div {
        display: flex !important;
        flex-direction: column !important;
        min-width: 260px !important;
        width: 280px !important;
    }

    /* DE KAARTJES STYLING */
    div[class*="stSortable"] > div > div {
        background-color: #262730 !important; /* Donkergrijs */
        color: #ffffff !important; /* Witte tekst */
        border: 1px solid #444 !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
        padding: 15px !important;
        font-family: sans-serif !important;
        white-space: pre-wrap !important; /* Zorg dat enters werken */
        
        /* HIER ZIT DE TRUC: Verberg alles wat te lang is */
        height: 60px !important;
        overflow: hidden !important; 
        transition: height 0.3s ease !important;
        position: relative;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        cursor: grab;
    }

    /* HOVER EFFECT: Klap open als je muis erop staat */
    div[class*="stSortable"] > div > div:hover {
        height: auto !important;     /* Word zo lang als de tekst */
        min-height: 120px !important; 
        background-color: #32333d !important; /* Iets lichter bij hover */
        border-color: #ff4b4b !important; /* Rood randje */
        z-index: 999;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
    }

    /* Pijltje toevoegen */
    div[class*="stSortable"] > div > div::after {
        content: "🔽";
        position: absolute;
        top: 10px;
        right: 10px;
        font-size: 12px;
        opacity: 0.7;
    }
    div[class*="stSortable"] > div > div:hover::after {
        opacity: 0; /* Verberg pijltje bij openklappen */
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATABASE FUNCTIES ---
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

# --- 4. INITIALISATIE ---
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

# --- 5. SIDEBAR ---
with st.sidebar:
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
        # STAP 1: Clean Text (Geen Markdown sterretjes)
        # We gebruiken Hoofdletters voor de bedrijfsnaam om het op te laten vallen
        title = f"{lead['name'].upper()} | {lead['price']}"
        
        # STAP 2: De Inhoud
        details = f"👤 {lead['contact']}\n📝 {lead['notes']}"
        
        # STAP 3: De ID verstoppen
        # We voegen 20 witregels toe. Hierdoor staat de ID zover naar beneden
        # dat je hem nooit ziet, zelfs niet als je hovert.
        spacer = "\n" * 20 
        hidden_id = f":::{lead['id']}"
        
        full_card_text = f"{title}\n\n{details}{spacer}{hidden_id}"
        
        items.append(full_card_text)
        
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
            # We splitsen op ':::' om de ID terug te vinden
            parts = item_str.split(':::')
            if len(parts) > 1:
                item_id = parts[-1] # Pak het laatste stukje (de ID)
                if item_id in all_leads:
                    new_col_items.append(all_leads[item_id])
        new_state[db_key] = new_col_items

    current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
    new_ids = [[l['id'] for l in col] for col in new_state.values()]
    
    if current_ids != new_ids:
        st.session_state['leads_data'] = new_state
        save_data(new_state)
        st.rerun()
