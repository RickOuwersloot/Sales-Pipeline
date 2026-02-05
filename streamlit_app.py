import streamlit as st
from streamlit_sortables import sort_items
import uuid
import json
import os

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS STYLING (DE CANVA MAKE-OVER) ---
st.markdown("""
    <style>
    /* Algemene achtergrond */
    .stApp { background-color: #1e1e1e; }

    /* --- LAYOUT: DE KOLOMMEN NAAST ELKAAR (CRUCIAAL) --- */
    /* We dwingen de container om horizontaal te werken */
    div[class*="stSortable"] {
        display: flex !important;
        flex-direction: row !important; /* Horizontaal */
        overflow-x: auto !important;    /* Scrollen als het niet past */
        gap: 20px !important;           /* Ruimte tussen de kolommen */
        padding-bottom: 20px !important;
        align-items: flex-start !important; /* Starten bovenaan */
    }
    
    /* --- STYLING VAN DE KOLOMMEN (DE "LANES") --- */
    div[class*="stSortable"] > div {
        display: flex !important;
        flex-direction: column !important;
        min-width: 300px !important; /* Vaste breedte per kolom */
        max-width: 300px !important;
        background-color: #25262b !important; /* Iets lichtere achtergrond voor de baan */
        border-radius: 12px !important; /* Mooie ronde hoeken */
        padding: 15px !important;       /* Ruimte binnenin */
        border: 1px solid #333 !important;
    }

    /* --- STYLING VAN DE KAARTJES --- */
    div[class*="stSortable"] > div > div {
        background-color: #3b3d45 !important; /* Kaartje iets lichter dan de baan */
        color: white !important;
        border: none !important;
        border-left: 5px solid #ff4b4b !important; /* Rood accentje */
        border-radius: 6px !important;
        margin-bottom: 10px !important;
        padding: 15px !important;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        cursor: grab;
        transition: transform 0.1s;
    }
    
    /* Hover effect op kaartje */
    div[class*="stSortable"] > div > div:hover {
        transform: scale(1.02); /* Klein plop effectje */
        background-color: #454752 !important;
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

# --- 6. HET BORD (KANBAN STYLE) ---
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
        # Strakke weergave op het kaartje
        price_part = f" | {lead['price']}" if lead['price'] else ""
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

# --- 8. DETAILS ONDERAAN ---
st.divider()
st.subheader("📋 Deal Details")

if len(all_leads_list) > 0:
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
                st.markdown("**Notities:**")
                st.info(selected_deal['notes'] if selected_deal['notes'] else "Geen notities.")
else:
    st.info("Nog geen deals in de pijplijn.")
