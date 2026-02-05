import streamlit as st
from streamlit_sortables import sort_items
import uuid

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS STYLING (Dark Mode & Layout) ---
st.markdown("""
    <style>
    /* Styling van de sleepbare kaartjes */
    div[class*="stSortable"] > div > div > div {
        background-color: #262730 !important; /* Donkergrijs */
        color: #ffffff !important; /* Witte tekst */
        border: 1px solid #4a4a4a !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin-bottom: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        font-size: 0.95rem;
    }
    
    /* Zorg dat kolommen een minimale breedte hebben */
    div[class*="stSortable"] {
        min-width: 200px;
    }
    
    /* Header styling */
    .kanban-header {
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA MANAGEMENT (Met UUIDs) ---
# We gebruiken een functie om nieuwe leads te maken zodat ze ALTIJD een uniek ID hebben.
def create_lead(company, contact, price, notes):
    return {
        'id': str(uuid.uuid4()), # Dit is het geheim: een unieke code voor elk item
        'name': company,
        'contact': contact,
        'price': price,
        'notes': notes
    }

# Initialiseer de database als die er nog niet is
if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = {
        'col1': [create_lead('Bakkerij Jansen', 'Peter', '€ 500', 'Interesse pui')],
        'col2': [create_lead('Timmerbedrijf Hout', 'Sanne', '€ 1.200', 'Offerte 3 wanden')],
        'col3': [], # Geland
        'col4': [], # Geen interesse
        'trash': [] # Prullenbak
    }

# --- 4. SIDEBAR: TOEVOEGEN ---
with st.sidebar:
    st.header("➕ Nieuwe Deal")
    with st.form("add_lead_form", clear_on_submit=True):
        company = st.text_input("Bedrijfsnaam")
        contact = st.text_input("Contactpersoon")
        price = st.text_input("Waarde (bv. €1500)")
        notes = st.text_area("Notities")
        submitted = st.form_submit_button("Toevoegen")
        
        if submitted and company:
            new_item = create_lead(company, contact, price, notes)
            st.session_state['leads_data']['col1'].append(new_item)
            st.success(f"{company} toegevoegd!")
            st.rerun()

    # Prullenbak Logica
    trash_count = len(st.session_state['leads_data']['trash'])
    if trash_count > 0:
        st.divider()
        st.error(f"🗑️ {trash_count} items in prullenbak")
        if st.button("Leeg Prullenbak Definitief"):
            st.session_state['leads_data']['trash'] = []
            st.rerun()

# --- 5. HET BORD VOORBEREIDEN ---
st.title("🚀 Sales Pipeline")

# Mapping: Database naam -> Scherm naam
columns_config = [
    ('col1', 'Te benaderen'),
    ('col2', 'Opgevolgd'),
    ('col3', 'Geland 🎉'),
    ('col4', 'Geen interesse'),
    ('trash', 'Prullenbak 🗑️')
]

# We maken de lijstjes klaar voor de plugin.
# We stoppen het unieke ID stiekem in de tekst met ':::' als scheiding.
kanban_data = []
for db_key, display_name in columns_config:
    items = []
    for lead in st.session_state['leads_data'][db_key]:
        # Opmaak van het kaartje
        card_text = f"**{lead['name']}**\n👤 {lead['contact']} | 💰 {lead['price']}\n📝 {lead['notes']}"
        # Plak ID erachter:  "Zichtbare tekst:::UNIEK_ID"
        full_item_string = f"{card_text}:::{lead['id']}"
        items.append(full_item_string)
    
    kanban_data.append({'header': display_name, 'items': items})

# --- 6. HET BORD TEKENEN & UPDATEN ---
# direction='horizontal' zorgt voor kolommen naast elkaar!
sorted_data = sort_items(kanban_data, multi_containers=True, direction='horizontal', key='my_pro_board')

# --- 7. DE CRUCIALE LOGICA (Terugschrijven naar database) ---
# We kijken of de sorted_data (wat jij ziet) anders is dan de opgeslagen data.

if len(sorted_data) == 5: # Checken of we alle kolommen hebben
    new_state = {}
    
    # Maak een platte lijst van ALLE leads die we hebben, zodat we ze kunnen opzoeken op ID
    all_leads_lookup = {}
    for col in st.session_state['leads_data'].values():
        for lead in col:
            all_leads_lookup[lead['id']] = lead

    # Nu bouwen we de nieuwe staat op basis van wat jij hebt gesleept
    state_has_changed = False
    
    for i, col_data in enumerate(sorted_data):
        db_key = columns_config[i][0] # col1, col2 etc.
        new_items_for_this_col = []
        
        for item_string in col_data['items']:
            # We splitsen de tekst weer: "Tekst:::ID" -> ["Tekst", "ID"]
            parts = item_string.split(':::')
            if len(parts) > 1:
                item_id = parts[-1] # Het ID is het laatste deel
                # Zoek het originele object op
                if item_id in all_leads_lookup:
                    new_items_for_this_col.append(all_leads_lookup[item_id])
                else:
                    # ID niet gevonden? (Zou niet moeten kunnen), negeer of maak nieuw.
                    continue
            else:
                # Fallback voor als er iets mis is met de string
                continue
        
        new_state[db_key] = new_items_for_this_col

    # Nu controleren we of de lijsten écht anders zijn dan wat we al hadden
    # Dit voorkomt onnodige reruns
    current_ids = [[l['id'] for l in col] for col in st.session_state['leads_data'].values()]
    new_ids = [[l['id'] for l in col] for col in new_state.values()]
    
    if current_ids != new_ids:
        st.session_state['leads_data'] = new_state
        # Een rerun forceert de update zodat de cirkel rond is
        st.rerun()
