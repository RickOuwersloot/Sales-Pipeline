import streamlit as st
from streamlit_sortables import sort_items
import uuid

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS LAYOUT HACKS (DIT ZORGT VOOR DE KOLOMMEN) ---
st.markdown("""
    <style>
    /* Forceer de sortables container om horizontaal te zijn */
    div[data-testid="stVerticalBlock"] > div > div[class*="stSortable"] {
        display: flex !important;
        flex-direction: row !important;
        gap: 20px !important;
        overflow-x: auto !important;
    }
    
    /* Zorg dat de kolommen zelf verticaal stapelen */
    div[class*="stSortable"] > div {
        display: flex !important;
        flex-direction: column !important;
        min-width: 250px !important;
        flex: 1 !important;
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

# --- 3. DATA & FUNCTIES ---
def create_lead(company, contact, price, notes):
    return {
        'id': str(uuid.uuid4()),
        'name': company,
        'contact': contact,
        'price': price,
        'notes': notes
    }

if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = {
        'col1': [], 'col2': [], 'col3': [], 'col4': [], 'trash': []
    }

# Forceer refresh teller
if 'board_key' not in st.session_state:
    st.session_state['board_key'] = 0

# --- 4. SIDEBAR ---
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
                st.session_state['board_key'] += 1
                st.rerun()

    if len(st.session_state['leads_data']['trash']) > 0:
        st.divider()
        if st.button("🗑️ Prullenbak Legen"):
            st.session_state['leads_data']['trash'] = []
            st.session_state['board_key'] += 1
            st.rerun()

# --- 5. HET BORD ---
st.title("🚀 Sales Pipeline")

# Kolom configuratie
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
        # Mooie HTML opmaak
        card_content = f"""
            <div style="font-weight:bold; font-size:1.1em;">{lead['name']}</div>
            <div style="font-size:0.9em; color:#ccc;">👤 {lead['contact']}</div>
            <div style="font-size:0.9em; color:#4CAF50;">💰 {lead['price']}</div>
            <div style="font-size:0.8em; margin-top:5px; font-style:italic;">📝 {lead['notes']}</div>
        """
        # ID verstoppen
        items.append(f"{card_content}:::{lead['id']}")
    kanban_data.append({'header': display_name, 'items': items})

# HET BORD TEKENEN
# BELANGRIJK: Hier heb ik 'custom_style' WEGGEHAALD om de error te voorkomen.
# De layout wordt nu geregeld door het CSS blok helemaal bovenaan.
sorted_data = sort_items(
    kanban_data, 
    multi_containers=True, 
    key=f"board_{st.session_state['board_key']}"
)

# --- 6. UPDATE LOGICA ---
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
        st.rerun()
