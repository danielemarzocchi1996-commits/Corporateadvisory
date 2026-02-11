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

# --- 2. DIAGNOSTICA MODELLI (La parte nuova) ---
st.sidebar.title("🔧 Diagnostica")
valid_model_name = ""

try:
    # Chiediamo a Google: "Cosa posso usare?"
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
    
    st.sidebar.success(f"Chiave OK! Trovati {len(available_models)} modelli.")
    st.sidebar.code("\n".join(available_models))

    # Cerchiamo il modello migliore disponibile
    if "models/gemini-1.5-flash" in available_models:
        valid_model_name = "models/gemini-1.5-flash"
    elif "models/gemini-1.5-flash-latest" in available_models:
        valid_model_name = "models/gemini-1.5-flash-latest"
    elif "models/gemini-1.5-pro" in available_models:
        valid_model_name = "models/gemini-1.5-pro"
    elif "models/gemini-pro" in available_models:
        valid_model_name = "models/gemini-pro" # Fallback vecchio
    else:
        st.error("Nessun modello Gemini trovato per questa chiave.")
    
    if valid_model_name:
        st.sidebar.info(f"Usando il modello: {valid_model_name}")

except Exception as e:
    st.sidebar.error(f"Errore lista modelli: {e}")

# --- 3. IL SYSTEM PROMPT ---
SYSTEM_INSTRUCTION = """
Sei un Senior Private Banker. Analizza il PDF (Scheda Azimut) e estrai un JSON.
REGOLE: Score 0-100 (0=Bassa priorità, 100=Alta).
OUTPUT JSON:
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
    # Usa il modello trovato dalla diagnostica
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
    return response.text.replace("```json", "").replace("```", "")

# --- 4. INTERFACCIA ---
st.title("🏦 Azimut Corporate Advisor AI")

if not valid_model_name:
    st.warning("⚠️ Impossibile procedere: nessun modello compatibile trovato. Controlla la sidebar.")
else:
    uploaded_file = st.file_uploader("Carica PDF Scheda Azimut", type="pdf")

    if uploaded_file is not None:
        with st.spinner(f'Analisi in corso con {valid_model_name}...'):
            try:
                json_str = analizza_pdf(uploaded_file, valid_model_name)
                # Tentativo di pulizia extra per JSON sporchi
                if "{" in json_str:
                    json_str = json_str[json_str.find("{"):json_str.rfind("}")+1]
                
                data = json.loads(json_str)
                
                # Visualizzazione
                c1, c2, c3 = st.columns(3)
                c1.metric("Azienda", data['anagrafica'].get('ragione_sociale', 'N/A'))
                c2.metric("Fatturato", data['anagrafica'].get('fatturato', 'N/A'))
                c3.metric("MORE Score", data['anagrafica'].get('more_score', 'N/A'))
                st.divider()
                
                for item in data['scorecard']:
                    with st.container():
                        col_a, col_b = st.columns([3, 1])
                        col_a.subheader(f"{item['area']}")
                        col_a.caption(f"KPI: {item['kpi']} | Note: {item['dettaglio']}")
                        
                        score = item['score']
                        col_b.metric("Priority Score", f"{score}/100")
                        if item['colore'] == 'red':
                            col_b.error("ALTA")
                        elif item['colore'] == 'yellow':
                            col_b.warning("MEDIA")
                        else:
                            col_b.success("BASSA")
                        st.divider()
                
                st.info(f"💡 **Sintesi:** {data['sintesi']}")

            except Exception as e:
                st.error(f"Errore: {e}")
