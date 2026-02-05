import streamlit as st
from streamlit_sortables import sort_items
import uuid
import json
import os

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. AGRESSIEVE CSS STYLING ---
st.markdown("""
    <style>
    /* 1. Achtergrond */
    .stApp { background-color: #1e1e1e; }
    
    /* 2. Maak de app breder zodat de kolommen passen */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100% !important;
    }

    /* 3. DE LAYOUT FIX (DIT IS DE BELANGRIJKSTE) 
       We targeten ELKE div die lijkt op de sortable container.
    */
    div[class*="stSortable"] {
        display: flex !important;
        flex-direction: row !important; /* Dwingt horizontaal */
        flex-wrap: nowrap !important;   /* Verbiedt naar de volgende regel gaan */
        overflow-x: auto !important;    /* Scrollbalk als het niet past */
        align-items: flex-start !important;
        gap: 15px !important;
        padding-bottom: 20px !important;
        width: 100% !important;
    }
    
    /* 4. De Kolommen (De "Banen") */
    div[class*="stSortable"] > div {
        display: flex !important;
        flex-direction: column !important;
        flex: 0 0 auto !important;      /* NIET krimpen, NIET groeien */
        width: 300px !important;        /* HARDE BREEDTE: 300px */
        min-width: 300px !important;
        
        background-color: #25262b !important;
        border: 1px solid #333 !important;
        border-radius: 10px !important;
        padding: 10px !important;
        margin-right: 10px !important;
    }

    /* 5. De Kaartjes */
    div[class*="stSortable"] > div > div {
        background-color: #3b3d45 !important;
        color: white !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin-bottom: 8px !important;
        border-left: 4px solid #ff4b4b !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
        white-space: normal !important; /* Tekst mag wel wrappen IN het kaartje */
    }
    
    /* Hover effect */
    div[class*="stSortable"] > div > div:hover {
        background-color: #454752 !important;
        transform: translateY(-2px);
        transition: all 0.2s ease;
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
def create_lead(company, contact, email, phone, price, notes):
    return {
        'id': str(uuid.uuid4()),
        'name': company, 'contact': contact, 'email': email, 
        'phone': phone, 'price': price, 'notes': notes
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
                new_item = create_lead(company, contact, email, phone, price, notes)
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
all_leads_list = []

for db_key, display_name in columns_config:
    items = []
    for lead in st.session_state['leads_data'][db_key]:
        price_part = f" | {lead['price']}" if lead['price'] else ""
        # We voegen wat witregels toe om het kaartje 'body' te geven
        card_text = f"{lead['name']}{price_part}"
        items.append(card_text)
        all_leads_list.append(lead)
        
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
        save_data(new_state)
        st.rerun()

# --- 8. DETAILS ---
st.divider()
if len(all_leads_list) > 0:
    st.subheader("📋 Deal Details")
    deal_options = {f"{l['name']}": l['id'] for l in all_leads_list}
    
    col_sel, col_info = st.columns([1, 2])
    with col_sel:
        selected_deal_name = st.selectbox("Selecteer deal:", list(deal_options.keys()))
        selected_id = deal_options[selected_deal_name]
        selected_deal = next((l for l in all_leads_list if l['id'] == selected_id), None)
    
    if selected_deal:
        with col_info:
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"### {selected_deal['name']}")
                    st.write(f"**Waarde:** {selected_deal['price']}")
                with c2:
                    st.write(f"👤 **{selected_deal.get('contact', '-')}")
                    st.write(f"📧 {selected_deal.get('email', '-')}")
                    st.write(f"☎️ {selected_deal.get('phone', '-')}")
                st.markdown("---")
                st.info(selected_deal['notes'] if selected_deal['notes'] else "Geen notities.")
