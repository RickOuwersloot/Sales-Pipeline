import streamlit as st
from streamlit_sortables import sort_items

# --- CONFIGURATIE ---
st.set_page_config(page_title="Mijn CRM", layout="wide")

# --- DATA OPSLAG (TIJDELIJK IN GEHEUGEN) ---
# Let op: Bij Streamlit Cloud ben je je data kwijt als je de pagina ververst
# tenzij we later een database koppelen. Dit is voor nu even de sessie-opslag.
if 'leads_data' not in st.session_state:
    st.session_state['leads_data'] = {
        'Te benaderen': [
            {'name': 'Bedrijf A', 'contact': 'Jan', 'phone': '0612345678', 'tag': ''},
            {'name': 'Bedrijf B', 'contact': 'Els', 'phone': '0687654321', 'tag': ''}
        ],
        'Opgevolgd': [],
        'Geland': [],
        'Geen interesse': []
    }

# --- TITEL ---
st.title("🚀 Mijn Sales Pipeline")
st.markdown("Sleep de kaarten naar de juiste kolom.")

# --- NIEUWE LEAD TOEVOEGEN (SIDEBAR) ---
with st.sidebar:
    st.header("Nieuwe Lead Toevoegen")
    with st.form("add_lead_form", clear_on_submit=True):
        company = st.text_input("Bedrijfsnaam")
        contact = st.text_input("Contactpersoon")
        email = st.text_input("E-mailadres")
        phone = st.text_input("Telefoonnummer")
        notes = st.text_area("Opmerkingen")
        
        submitted = st.form_submit_button("Toevoegen")
        
        if submitted and company:
            new_lead = {
                'name': company, 
                'contact': contact, 
                'phone': phone, 
                'email': email,
                'notes': notes,
                'tag': ''
            }
            st.session_state['leads_data']['Te benaderen'].append(new_lead)
            st.success(f"{company} toegevoegd!")

# --- FUNCTIE OM DATA TE FORMATTEREN VOOR HET BORD ---
# De sleep-tool werkt het beste met simpele tekst. 
# We maken hier "kaartjes" van de data.
def get_card_labels(column_name):
    cards = []
    # We gebruiken 'enumerate' om elk kaartje een uniek nummer (i) te geven
    for i, item in enumerate(st.session_state['leads_data'][column_name]):
        label = f"{item['name']} ({item['contact']}) #{i+1}"
        if column_name == 'Opgevolgd' and item.get('tag'):
             label += f" - [{item['tag']}]"
        cards.append(label)
    return cards

# --- HET KANBAN BORD (SLEPEN) ---
# We halen de huidige status op
# --- HET KANBAN BORD (SLEPEN) ---
# We maken een lijst van kolommen (headers) en items
kanban_data = [
    {'header': 'Te benaderen', 'items': get_card_labels('Te benaderen')},
    {'header': 'Opgevolgd', 'items': get_card_labels('Opgevolgd')},
    {'header': 'Geland', 'items': get_card_labels('Geland')},
    {'header': 'Geen interesse', 'items': get_card_labels('Geen interesse')}
]

# Dit toont het bord en laat je slepen
sorted_data = sort_items(kanban_data, multi_containers=True)

# Dit toont het bord en laat je slepen
sorted_data = sort_items(kanban_data, multi_containers=True)

# --- LOGICA: TAGS TOEVOEGEN BIJ VERPLAATSING ---
# Hier kijken we of er iets veranderd is door het slepen
# Dit is een simpele weergave. Voor volledige data-integriteit bij slepen
# is meer complexe code nodig, maar dit werkt visueel voor je MVP.

st.write("---")
st.caption("Details van je leads:")

# Laat de ruwe data zien (zodat je telefoonnummers etc kunt lezen)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("Te benaderen")
    for lead in st.session_state['leads_data']['Te benaderen']:
        with st.expander(lead['name']):
            st.write(f"👤 {lead['contact']}")
            st.write(f"📞 {lead['phone']}")
            st.write(f"📧 {lead.get('email', '-')}")
            st.write(f"📝 {lead.get('notes', '-')}")

with col2:
    st.subheader("Opgevolgd")
    # Hier kun je eventueel knoppen maken om de status (Mail/Bel) aan te passen
    for i, lead in enumerate(st.session_state['leads_data']['Opgevolgd']):
        with st.expander(f"{lead['name']}"):
            st.write(f"Huidige tag: {lead.get('tag', 'Geen')}")
            if st.button("Markeer als GEBELD", key=f"bel_{i}"):
                lead['tag'] = "BEL"
                st.rerun()
            if st.button("Markeer als MAIL", key=f"mail_{i}"):
                lead['tag'] = "MAIL"
                st.rerun()

with col3: 
    st.subheader("Geland 🎉")
    for lead in st.session_state['leads_data']['Geland']:
        st.write(f"✅ {lead['name']}")

with col4:
    st.subheader("Geen interesse")
    for lead in st.session_state['leads_data']['Geen interesse']:
        st.write(f"❌ {lead['name']}")

# --- UPDATE LOGICA (Synchronisatie) ---
# Dit stukje code zorgt dat als je sleept, de visualisatie klopt.
# Let op: Omdat 'slepen' in Streamlit lastig te koppelen is aan de volledige database
# objecten, is dit script vooral visueel.
# Voor de échte werking moeten we de 'sorted_data' (de nieuwe volgorde)
# terugvertalen naar je database objecten. Dat is stap 2.
