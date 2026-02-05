import streamlit as st
from streamlit_sortables import sort_items
import uuid

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS VOOR HORIZONTALE KOLOMMEN ---
st.markdown("""
    <style>
    div[class*="stSortable"] {
        display: flex;
        flex-direction: row; 
        gap: 15px;
        overflow-x: auto;
        padding-bottom: 20px;
    }
    div[class*="stSortable"] > div {
        flex: 1;
        min-width: 250px;
    }
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

# --- 3. DATA & INITIALISATIE ---
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

# DIT IS DE FIX: Een teller om het bord te dwingen te verversen
if 'board_key' not in st.session_state:
    st.session_state['board_key'] = 0

# --- 4. SIDEBAR (FORMULIER) ---
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
                # 1. Item maken
                new_item = create_lead(company, contact, price, notes)
                # 2. Toevoegen aan data
                st.session_state['leads_data']['col1'].insert(0, new_item)
                # 3. FIX: Verander de sleutel van het bord zodat hij MOET verversen
                st.session_state['board_key'] += 1
                
                st.success(f"{company} toegevoegd!")
                st.rerun()

    # Prullenbak
    if len(st.session_state['leads_data']['trash']) > 0:
        st.divider()
        if st.button("🗑️ Prullenbak Legen"):
            st.session_state['leads_data']['trash'] = []
            st.session_state['board_key'] += 1 # Ook hier forceren we een verversing
            st.rerun()

# --- 5. HET BORD ---
st.title("🚀 Sales Pipeline")

# Check of er data is (Debug info)
total_count = sum(len(x) for x in st.session_state['leads_data'].values())
if total_count == 0:
    st.info("👈 Je lijst is leeg. Voeg links een deal toe.")

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
        card_text = f"**{lead['name']}**\n👤 {lead['contact']} | 💰 {lead['price']}\n📝 {lead['notes']}"
        items.append(f"{card_text}:::{lead['id']}")
    kanban_data.append({'header': display_name, 'items': items})

# HET BORD TEKENEN
# We gebruiken nu de dynamische key!
current_key = f"board_{st.session_state['board_key']}"
sorted_data = sort_items(kanban_data, multi_containers=True, key=current_key)

# --- 6. UPDATE LOGICA ---
if len(sorted_data) == 5:
    new_state = {}
    all_leads = {}
    # Indexeer alle huidige leads
    for col in st.session_state['leads_data'].values():
        for lead in col:
            all_leads[lead['id']] = lead
            
    # Bouw nieuwe structuur
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

    # Check op wijzigingen
    current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
    new_ids = [[l['id'] for l in col] for col in new_state.values()]
    
    if current_ids != new_ids:
        st.session_state['leads_data'] = new_state
        st.rerun()

# --- 7. DEBUG SECTION (OM TE ZIEN OF HET ECHT WERKT) ---
# Als je twijfelt, open dit blokje onderaan de pagina.
# Daar zie je de "echte" database inhoud, los van het mooie bord.
with st.expander("🔧 Debug Data (Klik hier als je niets ziet)"):
    st.write(st.session_state['leads_data'])
