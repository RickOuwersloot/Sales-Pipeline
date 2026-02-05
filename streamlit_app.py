import streamlit as st
from streamlit_sortables import sort_items
import uuid

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. DATA & LOGICA ---
def create_lead(company, contact, price, notes):
    return {
        'id': str(uuid.uuid4()),
        'name': company,
        'contact': contact,
        'price': price,
        'notes': notes
    }

# Start met een schone lei (of behoud wat er is)
if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = {
        'col1': [], # Te benaderen
        'col2': [], # Opgevolgd
        'col3': [], # Geland
        'col4': [], # Geen interesse
        'trash': [] # Prullenbak
    }

# Forceer refresh teller
if 'board_key' not in st.session_state:
    st.session_state['board_key'] = 0

# --- 3. SIDEBAR (FORMULIER) ---
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
                st.session_state['board_key'] += 1 # Forceer update
                st.success(f"Deal '{company}' toegevoegd!")
                st.rerun()

    if len(st.session_state['leads_data']['trash']) > 0:
        st.divider()
        if st.button("🗑️ Prullenbak Legen"):
            st.session_state['leads_data']['trash'] = []
            st.session_state['board_key'] += 1
            st.rerun()

# --- 4. HET BORD (MET LAYOUT FIX) ---
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
        # HTML/Markdown opmaak voor het kaartje
        card_content = f"""
            <div style="font-weight:bold; font-size:1.1em;">{lead['name']}</div>
            <div style="font-size:0.9em; color:#ccc;">👤 {lead['contact']}</div>
            <div style="font-size:0.9em; color:#4CAF50;">💰 {lead['price']}</div>
            <div style="font-size:0.8em; margin-top:5px; font-style:italic;">📝 {lead['notes']}</div>
        """
        # ID verstoppen
        items.append(f"{card_content}:::{lead['id']}")
    kanban_data.append({'header': display_name, 'items': items})

# --- DE TRUC VOOR DE LAYOUT ---
# We gebruiken 'custom_style' om de container te dwingen 
# de kolommen naast elkaar te zetten (flex-direction: row).
style_hack = {
    "container": {
        "display": "flex",
        "flex-direction": "row", # DIT zorgt dat de kolommen naast elkaar komen
        "align-items": "flex-start",
        "justify-content": "flex-start",
        "gap": "20px",
        "overflow-x": "auto"
    },
    "card": {
        "background-color": "#262730",
        "border": "1px solid #4a4a4a",
        "border-radius": "8px",
        "padding": "10px",
        "margin-bottom": "10px",
        "box-shadow": "0px 2px 5px rgba(0,0,0,0.3)"
    }
}

# HET BORD TEKENEN
sorted_data = sort_items(
    kanban_data, 
    multi_containers=True, 
    direction='vertical', # Bedrijven onder elkaar IN de kolom
    custom_style=style_hack, # Kolommen naast elkaar
    key=f"board_{st.session_state['board_key']}"
)

# --- 5. UPDATE LOGICA ---
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
