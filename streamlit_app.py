import streamlit as st
from streamlit_sortables import sort_items

# --- CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- STYLING (DARK MODE & KOLOMMEN) ---
st.markdown("""
    <style>
    /* Styling van de kaartjes */
    div[class*="stSortable"] > div > div > div {
        background-color: #262730 !important;
        color: white !important;
        border: 1px solid #4e4f57 !important;
        border-radius: 8px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
        border-left: 5px solid #ff4b4b !important;
    }
    
    /* Styling van de header titels */
    .kanban-header {
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA OPSLAG ---
if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = {
        'col1': [{'name': 'Bakkerij Jansen', 'contact': 'Peter', 'price': '€ 500', 'notes': 'Interesse in grote glazen pui.'}],
        'col2': [{'name': 'Timmerbedrijf Hout', 'contact': 'Sanne', 'price': '€ 1.200', 'notes': 'Wil offerte voor 3 wanden.'}],
        'col3': [], # Geland
        'col4': [], # Geen interesse
        'trash': [] # Prullenbak
    }

# --- HELPER: FORMATTEER DE KAARTJES ---
def create_card_content(item):
    # De tekst die OP het kaartje komt te staan
    display_text = f"**{item['name']}**\n" \
                   f"👤 {item['contact']} | 💰 {item['price']}\n" \
                   f"📝 {item['notes']}"
    return display_text

# --- SIDEBAR: NIEUWE DEAL ---
with st.sidebar:
    st.header("➕ Nieuwe Deal")
    with st.form("add_lead_form", clear_on_submit=True):
        company = st.text_input("Bedrijfsnaam")
        contact = st.text_input("Contactpersoon")
        price = st.text_input("Waarde (bv. €1500)")
        notes = st.text_area("Notities (kort)")
        submitted = st.form_submit_button("Toevoegen")
        
        if submitted and company:
            new_lead = {'name': company, 'contact': contact, 'price': price, 'notes': notes}
            st.session_state['leads_data']['col1'].append(new_lead)
            st.success("Toegevoegd!")
            st.rerun()

    # --- PRULLENBAK ---
    trash_items = st.session_state['leads_data']['trash']
    if len(trash_items) > 0:
        st.divider()
        st.error(f"🗑️ {len(trash_items)} items in prullenbak")
        if st.button("Leeg Prullenbak Definitief"):
            st.session_state['leads_data']['trash'] = []
            st.rerun()

# --- HOOFDSCHERM ---
st.title("🚀 Sales Pipeline")

# Data voorbereiden voor plugin
kanban_data = []
columns_map = [
    ('col1', 'Te benaderen'),
    ('col2', 'Opgevolgd'),
    ('col3', 'Geland 🎉'),
    ('col4', 'Geen interesse'),
    ('trash', 'Prullenbak 🗑️')
]

for db_key, display_name in columns_map:
    items = []
    for i, lead in enumerate(st.session_state['leads_data'][db_key]):
        content = create_card_content(lead)
        # Uniek ID toevoegen (||id) om errors te voorkomen
        items.append(f"{content}||{i}") 
    kanban_data.append({'header': display_name, 'items': items})

# --- HET BORD TEKENEN (HIER ZAT DE FOUT!) ---
# direction='horizontal' zorgt dat de kolommen naast elkaar staan!
sorted_data = sort_items(kanban_data, multi_containers=True, direction='horizontal', key='sales_board')

# --- DATA SYNCHRONISATIE ---
if len(sorted_data) == 5: 
    new_state = {}
    
    # Alle huidige items verzamelen
    all_current_leads = []
    for col in st.session_state['leads_data'].values():
        all_current_leads.extend(col)

    # Nieuwe staat opbouwen
    for idx, col_data in enumerate(sorted_data):
        db_key = columns_map[idx][0] 
        new_items_in_this_col = []
        
        for item_label in col_data['items']:
            clean_text = item_label.split('||')[0]
            
            # Zoek originele data
            found = False
            for lead in all_current_leads:
                if create_card_content(lead) == clean_text:
                    new_items_in_this_col.append(lead)
                    all_current_leads.remove(lead)
                    found = True
                    break
            
            if not found:
                # Fallback
                lines = clean_text.replace('**', '').split('\n')
                name = lines[0] if len(lines) > 0 else "Onbekend"
                new_items_in_this_col.append({'name': name, 'contact': '?', 'price': '?', 'notes': ''})

        new_state[db_key] = new_items_in_this_col

    # Update database
    st.session_state['leads_data'] = new_state
