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

    /* LAYOUT: Horizontale kolommen */
    div[class*="stSortable"] {
        display: flex !important;
        flex-direction: row !important; 
        gap: 20px !important;
        overflow-x: auto !important;
        padding-bottom: 20px !important;
    }
    
    /* Kolommen: Items onder elkaar */
    div[class*="stSortable"] > div {
        display: flex !important;
        flex-direction: column !important;
        min-width: 250px !important;
        width: 280px !important;
    }

    /* KAARTJES: Simpel en strak */
    div[class*="stSortable"] > div > div {
        background-color: #262730 !important;
        color: white !important;
        border: 1px solid #444 !important;
        border-radius: 6px !important;
        margin-bottom: 10px !important;
        padding: 15px !important;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
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
# Update: Nu met email en telefoon
def create_lead(company, contact, email, phone, price, notes):
    return {
        'id': str(uuid.uuid4()),
        'name': company,
        'contact': contact,
        'email': email,    # Nieuw veld
        'phone': phone,    # Nieuw veld
        'price': price,
        'notes': notes
    }

if 'leads_data' not in st.session_state:
    saved_data = load_data()
    st.session_state['leads_data'] = saved_data if saved_data else {
        'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []
    }

if 'board_key' not in st.session_state:
    st.session_state['board_key'] = 0

# --- 5. SIDEBAR (FORMULIER UPDATE) ---
with st.sidebar:
    st.header("➕ Nieuwe Deal")
    with st.form("add_lead_form", clear_on_submit=True):
        company = st.text_input("Bedrijfsnaam *") # * geeft aan dat het verplicht is
        contact = st.text_input("Contactpersoon")
        email = st.text_input("Emailadres")       # Nieuw
        phone = st.text_input("Telefoonnummer")   # Nieuw
        price = st.text_input("Waarde (bv. €1500)")
        notes = st.text_area("Notities")
        
        submitted = st.form_submit_button("Toevoegen")
        
        if submitted:
            if not company:
                st.error("Vul tenminste een bedrijfsnaam in!")
            else:
                # Hier geven we de nieuwe velden mee aan de functie
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

# --- 6. HET BORD (OVERZICHT) ---
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
        # Op het bord houden we het simpel: Naam + Prijs
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
    
    # Lookup tabel maken
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

    # Check en update
    current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
    new_ids = [[l['id'] for l in col] for col in new_state.values()]
    
    if current_ids != new_ids:
        st.session_state['leads_data'] = new_state
        save_data(new_state)
        st.rerun()

# --- 8. DETAIL SECTIE (NU MET MEER INFO) ---
st.divider()
st.header("📋 Deal Details")

if len(all_leads_list) > 0:
    # Maak namen voor de dropdown
    deal_options = {f"{l['name']}": l['id'] for l in all_leads_list}
    
    selected_deal_name = st.selectbox("Kies een deal om details te bekijken:", list(deal_options.keys()))
    
    selected_id = deal_options[selected_deal_name]
    # Zoek object
    selected_deal = next((l for l in all_leads_list if l['id'] == selected_id), None)
    
    if selected_deal:
        # We maken nu 3 kolommen voor een mooi overzicht
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.caption("Bedrijf & Waarde")
            st.subheader(selected_deal['name'])
            st.metric("Verwachte Omzet", selected_deal['price'] if selected_deal['price'] else "—")
            
        with c2:
            st.caption("Contactgegevens")
            # Gebruik .get() om crashes te voorkomen bij oude data zonder deze velden
            contact = selected_deal.get('contact', '-')
            email = selected_deal.get('email', '-')
            phone = selected_deal.get('phone', '-')
            
            st.write(f"👤 **{contact}**")
            st.write(f"📧 {email}")
            st.write(f"☎️ {phone}")

        with c3:
            st.caption("Notities")
            st.info(selected_deal['notes'] if selected_deal['notes'] else "Geen notities.")
        
else:
    st.info("Nog geen deals. Voeg er eentje toe in het menu links!")
