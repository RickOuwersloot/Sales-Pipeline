import streamlit as st
from streamlit_sortables import sort_items
import uuid

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS VOOR HORIZONTALE KOLOMMEN ---
st.markdown("""
    <style>
    /* Zorg dat de kolommen NAAST elkaar staan (Flexbox) */
    div[class*="stSortable"] {
        display: flex;
        flex-direction: row; 
        gap: 15px;
        overflow-x: auto;
        padding-bottom: 20px;
    }
    
    /* Zorg dat de kaartjes ONDER elkaar staan binnen de kolom */
    div[class*="stSortable"] > div {
        flex: 1; /* Elke kolom even breed */
        min-width: 250px; /* Niet te smal worden */
    }

    /* Styling van de kaartjes */
    div[class*="stSortable"] > div > div > div {
        background-color: #262730 !important;
        color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin-bottom: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA & LOGICA ---
def create_lead(company, contact, price, notes):
    return {
        'id': str(uuid.uuid4()),
        'name': company,
        'contact': contact,
        'price': price,
        'notes': notes
    }

# START LEEG (Zoals je vroeg)
if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = {
        'col1': [], # Te benaderen
        'col2': [], # Opgevolgd
        'col3': [], # Geland
        'col4': [], # Geen interesse
        'trash': [] # Prullenbak
    }

# --- 4. SIDEBAR (HET FORMULIER) ---
with st.sidebar:
    st.header("➕ Nieuwe Deal")
    # Gebruik een formulier zodat de pagina niet bij elke letter ververst
    with st.form("add_lead_form", clear_on_submit=True):
        company = st.text_input("Bedrijfsnaam")
        contact = st.text_input("Contactpersoon")
        price = st.text_input("Waarde")
        notes = st.text_area("Notities")
        
        # De knop
        submitted = st.form_submit_button("Toevoegen")
        
        if submitted:
            if not company:
                st.error("Vul in ieder geval een bedrijfsnaam in.")
            else:
                # MAAK ITEM
                new_item = create_lead(company, contact, price, notes)
                
                # VOEG TOE AAN DE EERSTE LIJST
                st.session_state['leads_data']['col1'].insert(0, new_item) # Vooraan toevoegen
                
                # MELDING & HERSTART
                st.toast(f"✅ {company} is toegevoegd!")
                st.rerun()

    # Prullenbak knop
    if len(st.session_state['leads_data']['trash']) > 0:
        st.divider()
        if st.button("🗑️ Prullenbak Legen"):
            st.session_state['leads_data']['trash'] = []
            st.rerun()

# --- 5. HET BORD ---
st.title("🚀 Sales Pipeline")

# Als er nog helemaal geen data is, toon een hulptekst
total_items = sum(len(col) for col in st.session_state['leads_data'].values())
if total_items == 0:
    st.info("👈 Gebruik het menu links om je eerste bedrijf toe te voegen!")

columns_config = [
    ('col1', 'Te benaderen'),
    ('col2', 'Opgevolgd'),
    ('col3', 'Geland 🎉'),
    ('col4', 'Geen interesse'),
    ('trash', 'Prullenbak 🗑️')
]

# Data omzetten naar tekst voor de plugin
kanban_data = []
for db_key, display_name in columns_config:
    items = []
    for lead in st.session_state['leads_data'][db_key]:
        # Tekst op kaartje
        card_text = f"**{lead['name']}**\n👤 {lead['contact']} | 💰 {lead['price']}\n📝 {lead['notes']}"
        # ID verstoppen
        items.append(f"{card_text}:::{lead['id']}")
    
    kanban_data.append({'header': display_name, 'items': items})

# HET BORD TEKENEN
# Note: key verandert niet, zodat hij stabiel blijft.
sorted_data = sort_items(kanban_data, multi_containers=True, key='main_board')

# --- 6. UPDATE LOGICA (ALS JE SLEEPT) ---
# Alleen uitvoeren als de gebruiker iets heeft verplaatst
if len(sorted_data) == 5:
    new_state = {}
    state_changed = False
    
    # Zoeklijst maken
    all_leads = {}
    for col in st.session_state['leads_data'].values():
        for lead in col:
            all_leads[lead['id']] = lead
            
    # Nieuwe indeling bouwen
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

    # Check of er daadwerkelijk iets veranderd is ten opzichte van de huidige state
    # (Dit voorkomt infinite reruns)
    current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
    new_ids = [[l['id'] for l in col] for col in new_state.values()]
    
    if current_ids != new_ids:
        st.session_state['leads_data'] = new_state
        st.rerun()
