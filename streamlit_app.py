import streamlit as st
from streamlit_sortables import sort_items
import uuid

# --- 1. CONFIGURATIE (FORCEER WIDE MODE) ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS STYLING (HUFTERPROOF LAYOUT) ---
st.markdown("""
    <style>
    /* Styling van de kaartjes zelf */
    div[class*="stSortable"] > div > div > div {
        background-color: #262730 !important;
        color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin-bottom: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
    }
    
    /* CRUCIAAL: Zorg dat de kolommen naast elkaar blijven staan */
    div[class*="stSortable"] {
        display: flex;
        flex-direction: row; 
        gap: 10px;
        overflow-x: auto;
    }
    
    /* Headers mooi uitlijnen */
    .kanban-header {
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
        font-size: 1.1em;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA LOGICA (UUID SYSTEEM) ---
def create_lead(company, contact, price, notes):
    return {
        'id': str(uuid.uuid4()), # Uniek ID voor elk item
        'name': company,
        'contact': contact,
        'price': price,
        'notes': notes
    }

# Initialiseer database als die leeg is
if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = {
        'col1': [create_lead('Bakkerij Jansen', 'Peter', '€ 500', 'Interesse pui')],
        'col2': [create_lead('Timmerbedrijf Hout', 'Sanne', '€ 1.200', 'Offerte 3 wanden')],
        'col3': [],
        'col4': [],
        'trash': []
    }

# --- 4. SIDEBAR: FORMULIER ---
with st.sidebar:
    st.header("➕ Nieuwe Deal")
    with st.form("add_lead_form", clear_on_submit=True):
        company = st.text_input("Bedrijfsnaam")
        contact = st.text_input("Contactpersoon")
        price = st.text_input("Waarde (bv. €1500)")
        notes = st.text_area("Notities")
        submitted = st.form_submit_button("Toevoegen")
        
        if submitted and company:
            # 1. Maak item
            new_item = create_lead(company, contact, price, notes)
            # 2. Voeg toe aan de EERSTE kolom (Te benaderen)
            st.session_state['leads_data']['col1'].append(new_item)
            # 3. Geef feedback en herlaad
            st.success(f"Deal '{company}' toegevoegd!")
            st.rerun()

    # Prullenbak Info
    trash_len = len(st.session_state['leads_data']['trash'])
    if trash_len > 0:
        st.divider()
        st.warning(f"🗑️ {trash_len} items in prullenbak")
        if st.button("Leeg Prullenbak Definitief"):
            st.session_state['leads_data']['trash'] = []
            st.rerun()

# --- 5. HET BORD VOORBEREIDEN ---
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
        # Opmaak
        card_text = f"**{lead['name']}**\n👤 {lead['contact']} | 💰 {lead['price']}\n📝 {lead['notes']}"
        # ID verstoppen
        full_item_string = f"{card_text}:::{lead['id']}"
        items.append(full_item_string)
    
    kanban_data.append({'header': display_name, 'items': items})

# --- 6. HET BORD TEKENEN ---
# LET OP: direction='vertical' is de standaard voor items BINNEN een kolom.
# De kolommen zelf komen naast elkaar door de 'layout="wide"' en multi_containers=True
sorted_data = sort_items(kanban_data, multi_containers=True, key='final_board_v3')

# --- 7. DATA OPSLAAN BIJ SLEPEN ---
if len(sorted_data) == 5:
    new_state = {}
    
    # Zoek-tabel maken van alle leads op ID
    all_leads_lookup = {}
    for col in st.session_state['leads_data'].values():
        for lead in col:
            all_leads_lookup[lead['id']] = lead

    # Nieuwe indeling maken
    for i, col_data in enumerate(sorted_data):
        db_key = columns_config[i][0]
        new_items = []
        for item_str in col_data['items']:
            parts = item_str.split(':::')
            if len(parts) > 1:
                item_id = parts[-1]
                if item_id in all_leads_lookup:
                    new_items.append(all_leads_lookup[item_id])
        new_state[db_key] = new_items

    # Check op wijzigingen
    current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
    new_ids = [[l['id'] for l in col] for col in new_state.values()]
    
    if current_ids != new_ids:
        st.session_state['leads_data'] = new_state
        st.rerun()
