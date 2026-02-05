import streamlit as st
from streamlit_sortables import sort_items

# --- CONFIGURATIE ---
st.set_page_config(page_title="Mijn CRM", layout="wide")

# --- CSS STYLING (OM HET BLAUW TE MAKEN) ---
st.markdown("""
    <style>
    /* Pas de achtergrondkleur van de kaartjes aan */
    div[class*="stSortable"] > div > div > div {
        background-color: #e3f2fd !important; /* Lichtblauw */
        border: 1px solid #90caf9 !important; /* Blauwe rand */
        color: #0d47a1 !important; /* Donkerblauwe tekst */
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA OPSLAG ---
if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = {
        'Te benaderen': [
            {'name': 'Bedrijf A', 'contact': 'Jan', 'tag': ''},
            {'name': 'Bedrijf B', 'contact': 'Els', 'tag': ''}
        ],
        'Opgevolgd': [],
        'Geland': [],
        'Geen interesse': [],
        'Prullenbak 🗑️': []  # Nieuwe kolom voor verwijderen
    }

# --- SIDEBAR (INVOER & ACTIES) ---
with st.sidebar:
    st.header("Nieuwe Lead")
    with st.form("add_lead_form", clear_on_submit=True):
        company = st.text_input("Bedrijfsnaam")
        contact = st.text_input("Contactpersoon")
        notes = st.text_area("Notities")
        submitted = st.form_submit_button("Toevoegen")
        
        if submitted and company:
            # We voegen hem toe aan de sessie met een tijdelijk ID
            new_lead = {'name': company, 'contact': contact, 'notes': notes, 'tag': ''}
            st.session_state['leads_data']['Te benaderen'].append(new_lead)
            st.success(f"{company} toegevoegd!")
            st.rerun()

    st.divider()
    
    # Knop om prullenbak te legen
    trash_count = len(st.session_state['leads_data']['Prullenbak 🗑️'])
    if trash_count > 0:
        st.warning(f"Er zitten {trash_count} items in de prullenbak.")
        if st.button("🗑️ Leeg Prullenbak definitief"):
            st.session_state['leads_data']['Prullenbak 🗑️'] = []
            st.rerun()

# --- TITEL ---
st.title("🚀 Sales Pipeline")

# --- HELPER FUNCTIE ---
# Omdat sortables alleen met tekst werkt, maken we tekst-labels
def create_sortable_list(column_name):
    items = []
    for i, lead in enumerate(st.session_state['leads_data'][column_name]):
        # We maken een label: "Bedrijfsnaam (Contact) #ID"
        # De #ID is nodig zodat Streamlit niet crasht bij dubbele namen
        label = f"{lead['name']} ({lead['contact']}) ||{i}"
        items.append(label)
    return items

# --- HET KANBAN BORD (SLEPEN) ---
# Dit is de enige visualisatie die je nu ziet
kanban_data = [
    {'header': 'Te benaderen', 'items': create_sortable_list('Te benaderen')},
    {'header': 'Opgevolgd', 'items': create_sortable_list('Opgevolgd')},
    {'header': 'Geland 🎉', 'items': create_sortable_list('Geland')},
    {'header': 'Geen interesse', 'items': create_sortable_list('Geen interesse')},
    {'header': 'Prullenbak 🗑️', 'items': create_sortable_list('Prullenbak 🗑️')}
]

# Hier wordt het bord getekend en de nieuwe volgorde opgevangen
sorted_data = sort_items(kanban_data, multi_containers=True, key='mijn_bord')

# --- LOGICA: DATA BIJWERKEN NA SLEPEN ---
# Dit stukje code zorgt dat als jij sleept, de database op de achtergrond ook echt verandert.
# We moeten de labels (Tekst) terugvertalen naar de data (Objecten).

# Check of er gesleept is (is de data veranderd?)
needs_update = False
new_state = {}

for col_data in sorted_data:
    col_name = col_data['header']
    new_items_in_col = []
    
    for item_label in col_data['items']:
        # We halen de "oude" kolom en index uit het label hackje "||{index}"
        # Dit is een trucje om de originele data terug te vinden
        try:
            original_index = int(item_label.split('||')[-1])
            # We moeten zoeken waar dit item vandaan kwam. 
            # Omdat dit complex is in sortables, doen we een simpele lookup:
            # We zoeken in ALLE huidige kolommen naar dit specifieke item.
            found_lead = None
            for c_name, leads in st.session_state['leads_data'].items():
                if original_index < len(leads):
                    # Check of de naam matcht (voor de zekerheid)
                    check_lead = leads[original_index]
                    if f"{check_lead['name']} ({check_lead['contact']})" in item_label:
                        found_lead = check_lead
                        break
            
            if found_lead:
                new_items_in_col.append(found_lead)
            else:
                # Fallback voor als er iets geks gebeurt, maak nieuw object
                clean_name = item_label.split('||')[0]
                new_items_in_col.append({'name': clean_name, 'contact': '?', 'tag': ''})
                
        except:
            continue

    new_state[col_name] = new_items_in_col

# Vergelijk lengtes om te zien of we moeten updaten (simpele check)
# In een echte productie-app zou je dit robuuster doen, maar voor nu werkt dit.
current_total = sum(len(v) for v in st.session_state['leads_data'].values())
new_total = sum(len(v) for v in new_state.values())

# Als de gebruiker sleept, update sortables de visuals direct. 
# Wij updaten de sessie state pas bij de volgende actie of rerun, 
# maar om dataverlies te voorkomen schrijven we de nieuwe sortering terug als de formaten kloppen.
if len(sorted_data) == 5: # We hebben 5 kolommen
    # Update de sessie state met de nieuwe volgorde
    # Let op: Dit is een "gevaarlijke" operatie bij sortables.
    # We vertrouwen erop dat de visual matcht met de logica.
    
    # Om te voorkomen dat items 'verdwijnen' bij een refresh, updaten we de state alleen
    # als we zeker weten dat de structuur klopt. 
    # Voor nu (MVP): We updaten de state op basis van wat sortables teruggeeft.
    
    # We bouwen de state opnieuw op basis van de labels die sortables teruggeeft.
    # Dit is de enige manier om "verplaatsing" permanent te maken.
    
    # Reset de state containers
    temp_state = {k: [] for k in st.session_state['leads_data'].keys()}
    
    all_leads_flat = []
    for col in st.session_state['leads_data'].values():
        all_leads_flat.extend(col)
        
    # Nu gaan we puzzelen: Welk item hoort bij welk label?
    # Dit is nodig omdat sortables alleen tekst verplaatst, geen objecten.
    for col_data in sorted_data:
        c_name = col_data['header']
        for item_label in col_data['items']:
             # Haal de tekst voor de '||' op
             text_part = item_label.split('||')[0]
             
             # Zoek de data erbij in onze oude lijst
             # (Dit pakt de eerste match, dus bij 2 exact dezelfde bedrijven pakt hij de eerste)
             for lead in all_leads_flat:
                 lead_str = f"{lead['name']} ({lead['contact']})"
                 if lead_str == text_part:
                     temp_state[c_name].append(lead)
                     # Verwijder uit flat list zodat we bij dubbele namen de volgende pakken
                     all_leads_flat.remove(lead)
                     break
    
    # Overschrijf de sessie
    st.session_state['leads_data'] = temp_state
