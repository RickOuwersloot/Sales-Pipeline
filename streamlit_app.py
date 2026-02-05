import streamlit as st
from streamlit_sortables import sort_items

# --- CONFIGURATIE ---
# We zetten de layout op wide, zodat de kolommen naast elkaar passen
st.set_page_config(page_title="Mijn Sales CRM", layout="wide")

# --- MONDAY.COM STYLING (CSS) ---
# Dit blok tovert de standaard Streamlit look om naar een 'Monday' look
st.markdown("""
    <style>
    /* 1. Achtergrond van de hele app iets lichter grijs maken (SaaS look) */
    .stApp {
        background-color: #f7f9fc;
    }
    
    /* 2. De Kaartjes zelf stylen */
    div[class*="stSortable"] > div > div > div {
        background-color: white !important;
        color: #323338 !important;  /* Donkere tekst */
        border: 1px solid #d0d4e4 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; /* Zachte schaduw */
        padding: 15px !important;
        margin-bottom: 10px !important;
        border-left: 6px solid #0073ea !important; /* Monday Blauw accent aan de zijkant */
        font-family: 'Roboto', sans-serif;
    }
    
    /* 3. De Header tekst boven de kolommen */
    div[class*="stSortable"] {
        background-color: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA OPSLAG ---
if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = {
        'Te benaderen': [
            {'name': 'Bakkerij Jansen', 'contact': 'Peter', 'price': '€ 500', 'tag': ''},
            {'name': 'Timmerbedrijf Hout', 'contact': 'Sanne', 'price': '€ 1.200', 'tag': ''}
        ],
        'Opgevolgd': [],
        'Geland': [],
        'Geen interesse': [],
        'Prullenbak 🗑️': [] 
    }

# --- SIDEBAR (INVOER) ---
with st.sidebar:
    st.title("Nieuwe Deal")
    with st.form("add_lead_form", clear_on_submit=True):
        company = st.text_input("Bedrijfsnaam")
        contact = st.text_input("Contactpersoon")
        price = st.text_input("Verwachte Waarde (bijv. €1000)")
        notes = st.text_area("Notities")
        submitted = st.form_submit_button("Maak Deal Aan")
        
        if submitted and company:
            new_lead = {'name': company, 'contact': contact, 'price': price, 'notes': notes, 'tag': ''}
            st.session_state['leads_data']['Te benaderen'].append(new_lead)
            st.success("Toegevoegd!")
            st.rerun()

    # Prullenbak logica
    trash_count = len(st.session_state['leads_data']['Prullenbak 🗑️'])
    if trash_count > 0:
        st.divider()
        st.warning(f"{trash_count} items in prullenbak")
        if st.button("Leeg Prullenbak"):
            st.session_state['leads_data']['Prullenbak 🗑️'] = []
            st.rerun()

# --- HOOFDSCHERM ---
st.title("💼 Mijn Sales Board")

# --- HELPER FUNCTIE VOOR KAARTJES ---
def create_sortable_list(column_name):
    items = []
    for i, lead in enumerate(st.session_state['leads_data'][column_name]):
        # We gebruiken HTML trucs om tekst dikgedrukt te krijgen in de kaart
        # De `\n` zorgt voor een enter. 
        # Monday toont vaak: Naam, daaronder details.
        
        # OPMERKING: Sortables ondersteunt beperkte opmaak, we doen het zo netjes mogelijk
        name_part = lead['name']
        details_part = f"{lead['contact']} | {lead.get('price', '-')}"
        
        # Het ID hackje (||) blijft nodig voor de logica
        label = f"{name_part}\n👤 {details_part} ||{i}"
        items.append(label)
    return items

# --- HET BORD ---
# We definiëren de kolommen. 
kanban_data = [
    {'header': 'Te benaderen 🔵', 'items': create_sortable_list('Te benaderen')},
    {'header': 'Opgevolgd 🟣', 'items': create_sortable_list('Opgevolgd')},
    {'header': 'Geland 🟢', 'items': create_sortable_list('Geland')},
    {'header': 'Geen interesse ⚪', 'items': create_sortable_list('Geen interesse')},
    {'header': 'Prullenbak 🗑️', 'items': create_sortable_list('Prullenbak 🗑️')}
]

# Render het bord
sorted_data = sort_items(kanban_data, multi_containers=True, key='monday_board')

# --- LOGICA (OPSLAAN VAN SLEPEN) ---
# Dit is exact dezelfde logica als de vorige keer, om te zorgen dat de data klopt.

new_state = {}
for col_data in sorted_data:
    col_name = col_data['header']
    new_items_in_col = []
    for item_label in col_data['items']:
        try:
            original_index = int(item_label.split('||')[-1])
            found_lead = None
            # Zoek het originele object
            for c_name, leads in st.session_state['leads_data'].items():
                if original_index < len(leads):
                    check_lead = leads[original_index]
                    # Check of de naam overeenkomt (veiligheid)
                    if check_lead['name'] in item_label:
                        found_lead = check_lead
                        break
            if found_lead:
                new_items_in_col.append(found_lead)
            else:
                # Fallback
                new_items_in_col.append({'name': item_label.split('\n')[0], 'contact': '?', 'price': ''})
        except:
            continue
    new_state[col_name] = new_items_in_col

# Update alleen als er echt geschoven is (lengte check is simpele trigger)
if len(sorted_data) == 5:
    # Rebuild state
    temp_state = {k: [] for k in st.session_state['leads_data'].keys()}
    all_leads_flat = []
    for col in st.session_state['leads_data'].values():
        all_leads_flat.extend(col)
        
    for col_data in sorted_data:
        c_name = col_data['header']
        for item_label in col_data['items']:
             text_part = item_label.split(' ||')[0] # Let op de spatie voor ||
             # We zoeken op de naam (eerste deel voor de \n)
             name_to_find = text_part.split('\n')[0]
             
             for lead in all_leads_flat:
                 if lead['name'] == name_to_find:
                     temp_state[c_name].append(lead)
                     all_leads_flat.remove(lead)
                     break
    
    st.session_state['leads_data'] = temp_state
