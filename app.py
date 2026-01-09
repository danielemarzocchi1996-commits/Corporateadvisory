import streamlit as st
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

# Configurazione Pagina
st.set_page_config(page_title="Azimut Corporate Advisor", layout="wide")

# Carica API Key (da locale o da secrets di Streamlit Cloud)
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    # Fallback per quando sarai online
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        st.error("Manca la API Key di Google Gemini.")
        st.stop()

# Configura Gemini
genai.configure(api_key=api_key)

# --- IL SYSTEM PROMPT (Il "Cervello" del Banker) ---
SYSTEM_INSTRUCTION = """
Sei un Senior Private Banker e Analista Finanziario esperto in PMI italiane.
Il tuo compito è analizzare la "Scheda Azimut Direct" (PDF) fornita, estrarre i dati finanziari chiave e calcolare un "Priority Score" (da 0 a 100) per le aree di intervento.

REGOLE DI CALCOLO SCORE (0-100):
0-30: Bassa priorità. 31-70: Media. 71-100: Alta/Critica (Agire subito).

RESTITUISCI SOLO JSON IN QUESTO FORMATO:
{
  "anagrafica": {
    "ragione_sociale": "String",
    "partita_iva": "String",
    "more_score": "String",
    "fatturato_ultimo": "String"
  },
  "scorecard": [
    {
      "area": "Gestione Tesoreria",
      "score": 0,
      "colore": "red/yellow/green",
      "dettaglio": "Stringa breve motivazione",
      "kpi": "Liquidità vs Debiti Breve"
    },
    {
      "area": "Debito Corporate",
      "score": 0,
      "colore": "red/yellow/green",
      "dettaglio": "Stringa breve motivazione",
      "kpi": "PFN/EBITDA e Scadenze"
    },
    {
      "area": "Assetti Proprietari",
      "score": 0,
      "colore": "red/yellow/green",
      "dettaglio": "Stringa breve motivazione",
      "kpi": "Età soci / Holding"
    },
    {
      "area": "Wealth Planning",
      "score": 0,
      "colore": "red/yellow/green",
      "dettaglio": "Stringa breve motivazione",
      "kpi": "Utili non distribuiti / PN"
    },
    {
      "area": "TFR e Previdenza",
      "score": 0,
      "colore": "red/yellow/green",
      "dettaglio": "Stringa breve motivazione",
      "kpi": "Stock TFR e Dipendenti"
    }
  ],
  "sintesi": "Un paragrafo discorsivo di sintesi commerciale per il consulente."
}
"""

def analizza_pdf(pdf_file):
    model = genai.GenerativeModel("gemini-1.5-flash") # Modello veloce ed economico
    
    # Costruiamo la richiesta
    prompt_parts = [
        SYSTEM_INSTRUCTION,
        {
            "mime_type": "application/pdf",
            "data": pdf_file.getvalue()
        },
        "Analizza questo documento e genera il JSON."
    ]
    
    response = model.generate_content(prompt_parts)
    # Pulizia della risposta per avere solo JSON puro
    return response.text.replace("```json", "").replace("```", "")

# --- INTERFACCIA GRAFICA (Streamlit) ---
st.title("🏦 Azimut Corporate Advisor AI")
st.markdown("Carica la **Scheda Azimut Direct** (PDF) per ottenere l'analisi delle priorità commerciali.")

uploaded_file = st.file_uploader("Carica PDF", type="pdf")

if uploaded_file is not None:
    with st.spinner('L\'AI sta analizzando i dati finanziari...'):
        try:
            json_str = analizza_pdf(uploaded_file)
            data = json.loads(json_str)
            
            # 1. Header Azienda
            col1, col2, col3 = st.columns(3)
            col1.metric("Azienda", data['anagrafica']['ragione_sociale'])
            col2.metric("Fatturato", data['anagrafica']['fatturato_ultimo'])
            col3.metric("MORE Score", data['anagrafica']['more_score'])
            
            st.divider()
            
            # 2. Scorecard Visuale
            st.subheader("📊 Scorecard Priorità Commerciale")
            
            for item in data['scorecard']:
                with st.container():
                    c1, c2, c3 = st.columns([1, 3, 1])
                    c1.markdown(f"### {item['area']}")
                    
                    # Barra progresso colorata logicamente
                    bar_color = item['colore']
                    val = item['score']
                    c2.progress(val / 100, text=f"Score: {val}/100")
                    c2.caption(f"**KPI Key:** {item['kpi']} | **Analisi:** {item['dettaglio']}")
                    
                    if val > 70:
                        c3.error("ALTA PRIORITÀ")
                    elif val > 30:
                        c3.warning("DA MONITORARE")
                    else:
                        c3.success("BASSA PRIORITÀ")
                    
                    st.divider()

            # 3. Sintesi Finale
            st.info(f"💡 **Sintesi Strategica:** {data['sintesi']}")

        except Exception as e:
            st.error(f"Errore durante l'analisi: {e}")
