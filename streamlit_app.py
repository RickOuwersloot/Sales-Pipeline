import streamlit as st
from streamlit_sortables import sort_items

# --- CONFIGURATIE ---
st.set_page_config(page_title="Sales Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- DARK MODE STYLING (CSS) ---
# We maken de kaartjes donkergrijs met een mooie rand, passend bij de dark mode.
st.markdown("""
    <style>
    /* De achtergrond van de kaartjes */
    div[class*="stSortable"] > div > div > div {
        background-color: #262730 !important; /* Donkergrijs */
        color: #ffffff !important; /* Witte tekst */
        border: 1px solid #4e4f57 !important;
        border-radius: 8px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
        border-left: 5px solid #ff4b4b !important; /* Rode accentstreep (standaard Streamlit rood) */
    }
    
    /* Zorg dat de header tekst boven de kolommen goed zichtbaar is */
    .kanban-header {
        font-size: 18px;
        font-weight: bold;
        color: white;
        margin-bottom: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA OPSLAG ---
# We gebruiken simpele namen voor de kolommen in de database om errors te voorkomen
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
    # Dit bepaalt wat er OP het kaartje staat.
    # We gebruiken Markdown voor dikgedrukte tekst.
    # Let op: ':::' gebruiken we als scheidingsteken voor later.
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

    # --- PRULLENBAK LOGICA ---
    trash_items = st.session_state['leads_data']['trash']
    if len(trash_items) > 0:
        st.divider()
        st.error(f"🗑️ {len(trash_items)} items in prullenbak")
        if st.button("Leeg Prullenbak Definitief"):
            st.session_state['leads_data']['trash'] = []
            st.rerun()

# --- HOOFDSCHERM ---
st.title("🚀 Sales Pipeline")

# We bereiden de data voor de visualisatie voor
# We moeten zorgen dat elk kaartje uniek is met een ID hack (||id)
kanban_data = []
columns_map = [
    ('col1', 'Te benaderen'),
    ('col2', 'Opgevolgd'),
    ('col3', 'Geland 🎉'),
    ('col4', 'Geen interesse'),
    ('trash', 'Prullenbak 🗑️')
]

# Bouw de lijsten voor de plugin
for db_key, display_name in columns_map:
    items = []
    for i, lead in enumerate(st.session_state['leads_data'][db_key]):
        content = create_card_content(lead)
        # Voeg uniek ID toe zodat de app niet crasht bij dubbele namen
        items.append(f"{content}||{i}") 
    kanban_data.append({'header': display_name, 'items': items})

# --- HET BORD TEKENEN ---
# key='sales_board' zorgt dat hij niet in de war raakt bij verversen
sorted_data = sort_items(kanban_data, multi_containers=True, key='sales_board')

# --- DATA SYNCHRONISATIE (CRUCIAAL) ---
# Als je sleept, updaten we hier de database op de achtergrond.

if len(sorted_data) == 5: # Check of de structuur klopt
    new_state = {}
    
    # Haal alle leads op in een platte lijst om ze terug te vinden
    all_current_leads = []
    for col in st.session_state['leads_data'].values():
        all_current_leads.extend(col)

    # Loop door de NIEUWE volgorde van het bord
    for idx, col_data in enumerate(sorted_data):
        # We moeten weten bij welke database-key deze kolom hoort (col1, col2, etc)
        db_key = columns_map[idx][0] 
        new_items_in_this_col = []
        
        for item_label in col_data['items']:
            # Haal de tekst los van het unieke ID (voor de ||)
            clean_text = item_label.split('||')[0]
            
            # Zoek de originele data erbij
            # (We vergelijken de geformatteerde tekst)
            found = False
            for lead in all_current_leads:
                if create_card_content(lead) == clean_text:
                    new_items_in_this_col.append(lead)
                    # Verwijder uit de zoeklijst om dubbelen te voorkomen
                    all_current_leads.remove(lead)
                    found = True
                    break
            
            if not found:
                # Fallback: als er iets heel geks gebeurt, maak een nieuw item
                # Dit voorkomt de KeyError die je eerder zag
                lines = clean_text.replace('**', '').split('\n')
                name = lines[0] if len(lines) > 0 else "Onbekend"
                new_items_in_this_col.append({'name': name, 'contact': '?', 'price': '?', 'notes': ''})

        new_state[db_key] = new_items_in_this_col

    # Update de database
    st.session_state['leads_data'] = new_state
