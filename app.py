import streamlit as st
import google.generativeai as genai
import json
import os

st.set_page_config(page_title="Azimut Advisor", layout="wide")

# --- 1. GESTIONE CHIAVE ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("Manca la API Key nei Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. SELETTORE MODELLO (SOLUZIONE DEFINITIVA) ---
st.sidebar.title("⚙️ Configurazione")

try:
    # Scarica la lista reale dei modelli disponibili per la tua chiave
    model_list = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            model_list.append(m.name)
    
    # Crea il menu a tendina
    # Cerca di preselezionare un modello "Flash" se esiste, altrimenti il primo
    default_index = 0
    for i, name in enumerate(model_list):
        if "flash" in name and "1.5" in name:
            default_index = i
            break
            
    selected_model = st.sidebar.selectbox("Seleziona Modello AI:", model_list, index=default_index)
    st.sidebar.success(f"Modello attivo: {selected_model}")

except Exception as e:
    st.sidebar.error(f"Errore caricamento modelli: {e}")
    st.stop()

# --- 3. IL SYSTEM PROMPT ---
SYSTEM_INSTRUCTION = """
Sei un Senior Private Banker. Analizza il PDF (Scheda Azimut) e estrai un JSON.
REGOLE: Score 0-100 (0=Bassa priorità, 100=Alta).
OUTPUT JSON ESATTO (senza markdown):
{
  "anagrafica": { "ragione_sociale": "String", "fatturato": "String", "more_score": "String" },
  "scorecard": [
    { "area": "Gestione Tesoreria", "score": 0, "colore": "green/yellow/red", "dettaglio": "String", "kpi": "String" },
    { "area": "Debito Corporate", "score": 0, "colore": "green/yellow/red", "dettaglio": "String", "kpi": "String" },
    { "area": "Assetti Proprietari", "score": 0, "colore": "green/yellow/red", "dettaglio": "String", "kpi": "String" },
    { "area": "Wealth Planning", "score": 0, "colore": "green/yellow/red", "dettaglio": "String", "kpi": "String" },
    { "area": "TFR e Previdenza", "score": 0, "colore": "green/yellow/red", "dettaglio": "String", "kpi": "String" }
  ],
  "sintesi": "Breve sintesi commerciale."
}
"""

def analizza_pdf(pdf_file, model_name):
    model = genai.GenerativeModel(model_name)
    prompt_parts = [
        SYSTEM_INSTRUCTION,
        {
            "mime_type": "application/pdf",
            "data": pdf_file.getvalue()
        },
        "Genera il JSON di analisi."
    ]
    response = model.generate_content(prompt_parts)
    return response.text

# --- 4. INTERFACCIA ---
st.title("🏦 Azimut Corporate Advisor AI")
st.markdown("Carica la **Scheda Azimut Direct** (PDF).")

uploaded_file = st.file_uploader("Carica PDF", type="pdf")

if uploaded_file is not None:
    # Usa il modello scelto dall'utente
    with st.spinner(f'Analisi in corso con {selected_model}...'):
        try:
            raw_response = analizza_pdf(uploaded_file, selected_model)
            
            # Pulizia JSON (Rimuove ```json e spazi)
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            # Cerca le parentesi graffe per sicurezza
            start = clean_json.find("{")
            end = clean_json.rfind("}") + 1
            if start != -1 and end != 0:
                clean_json = clean_json[start:end]
            
            data = json.loads(clean_json)
            
            # Visualizzazione
            c1, c2, c3 = st.columns(3)
            # Usa .get per evitare errori se mancano campi
            c1.metric("Azienda", data.get('anagrafica', {}).get('ragione_sociale', 'N/A'))
            c2.metric("Fatturato", data.get('anagrafica', {}).get('fatturato', 'N/A'))
            c3.metric("MORE Score", data.get('anagrafica', {}).get('more_score', 'N/A'))
            st.divider()
            
            scorecard = data.get('scorecard', [])
            for item in scorecard:
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    col_a.subheader(f"{item.get('area', 'Area')}")
                    col_a.caption(f"KPI: {item.get('kpi', '')} | Note: {item.get('dettaglio', '')}")
                    
                    score = item.get('score', 0)
                    col_b.metric("Priority Score", f"{score}/100")
                    
                    color = item.get('colore', 'green')
                    if color == 'red':
                        col_b.error("ALTA")
                    elif color == 'yellow':
                        col_b.warning("MEDIA")
                    else:
                        col_b.success("BASSA")
                    st.divider()
            
            st.info(f"💡 **Sintesi:** {data.get('sintesi', 'Nessuna sintesi disponibile.')}")

        except Exception as e:
            st.error(f"Errore durante l'elaborazione: {e}")
            st.warning("Dettaglio risposta grezza (per debug):")
            st.code(raw_response)
