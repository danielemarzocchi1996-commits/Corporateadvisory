import streamlit as st
import google.generativeai as genai
import json
import os

st.set_page_config(page_title="Azimut Advisor - Priorità Commerciale", layout="wide")

# --- 1. GESTIONE CHIAVE ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("Manca la API Key nei Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. SELETTORE MODELLO ---
st.sidebar.title("⚙️ Configurazione")
try:
    model_list = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            model_list.append(m.name)
    
    # Preselezione intelligente
    default_index = 0
    for i, name in enumerate(model_list):
        if "flash" in name and "1.5" in name:
            default_index = i
            break
            
    selected_model = st.sidebar.selectbox("Modello AI:", model_list, index=default_index)

except Exception as e:
    st.sidebar.error(f"Errore caricamento modelli: {e}")
    st.stop()

# --- 3. IL NUOVO CERVELLO (PROMPT AGGIORNATO) ---
SYSTEM_INSTRUCTION = """
Sei un Senior Private Banker di Azimut. Il tuo obiettivo è analizzare il PDF allegato per identificare OPPORTUNITÀ COMMERCIALI.

**IMPORTANTE - LOGICA DELLO SCORE (PRIORITÀ DI VISITA):**
Lo score (0-100) indica L'URGENZA di fissare un appuntamento con l'imprenditore.
- **0-30 (Bassa Priorità):** Azienda statica, sana, senza bisogni evidenti. Non c'è urgenza.
- **31-70 (Media Priorità):** Ci sono spunti di discussione (es. ottimizzazione).
- **71-100 (ALTA PRIORITÀ - ACTION):** C'è un bisogno latente critico o un'opportunità enorme. (Es. Troppa liquidità ferma, Debito a breve eccessivo, Passaggio generazionale a rischio).

**STRUTTURA OUTPUT JSON (Rispetta rigorosamente):**
{
  "anagrafica": { 
    "ragione_sociale": "String", 
    "fatturato_ultimo": "String", 
    "trend_fatturato": "Crescente/Decrescente/Stabile",
    "more_score": "String" 
  },
  "scorecard": [
    { 
      "area": "Gestione Tesoreria", 
      "priorita_score": 0, 
      "colore": "rosso/giallo/verde", 
      "kpi_elenco": ["Liquidità: ...", "Ciclo cassa: ..."], 
      "analisi_consulente": "Spiega perché la priorità è alta o bassa in 2 frasi."
    },
    { 
      "area": "Debito Corporate", 
      "priorita_score": 0, 
      "colore": "rosso/giallo/verde", 
      "kpi_elenco": ["PFN/EBITDA: ...", "Debiti Breve: ...", "Eligible DL: Si/No"], 
      "analisi_consulente": "..."
    },
    { 
      "area": "Assetti Proprietari", 
      "priorita_score": 0, 
      "colore": "rosso/giallo/verde", 
      "kpi_elenco": ["Holding: Si/No", "Età Soci Key: ..."], 
      "analisi_consulente": "..."
    },
    { 
      "area": "Wealth Planning", 
      "priorita_score": 0, 
      "colore": "rosso/giallo/verde", 
      "kpi_elenco": ["Utile Netto: ...", "Riserve/PN: ..."], 
      "analisi_consulente": "..."
    },
    { 
      "area": "TFR e Previdenza", 
      "priorita_score": 0, 
      "colore": "rosso/giallo/verde", 
      "kpi_elenco": ["Stock TFR: ...", "Num Dipendenti: ..."], 
      "analisi_consulente": "..."
    }
  ],
  "sintesi_executive": "Frase finale per il consulente: 'Chiama il cliente proponendo [Prodotto] perché [Motivo]'."
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
        "Genera il JSON di prioritizzazione."
    ]
    response = model.generate_content(prompt_parts)
    return response.text

# --- 4. INTERFACCIA GRAFICA (NUOVO LAYOUT) ---
st.title("🚀 Azimut Priority Advisor")
st.markdown("Analisi automatica delle opportunità commerciali basata su Bilancio Riclassificato.")

uploaded_file = st.file_uploader("Carica PDF Scheda Azimut", type="pdf")

if uploaded_file is not None:
    with st.spinner(f'L\'Intelligenza Artificiale sta valutando le priorità...'):
        try:
            raw_response = analizza_pdf(uploaded_file, selected_model)
            
            # Pulizia JSON
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            if "{" in clean_json:
                clean_json = clean_json[clean_json.find("{"):clean_json.rfind("}")+1]
            
            data = json.loads(clean_json)
            
            # --- HEADER AZIENDA ---
            anag = data.get('anagrafica', {})
            with st.container():
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Azienda", anag.get('ragione_sociale', 'N/A'))
                c2.metric("Fatturato", anag.get('fatturato_ultimo', 'N/A'), delta=anag.get('trend_fatturato'))
                c3.metric("Rating MORE", anag.get('more_score', 'N/A'))
                c4.markdown("#### Sintesi Action")
                # Un piccolo badge per la sintesi
                st.info(f"💡 {data.get('sintesi_executive', '')}")
            
            st.divider()
            st.subheader("📊 Scorecard delle Priorità")

            # --- LE 5 AREE (Layout a Schede) ---
            scorecard = data.get('scorecard', [])
            
            # Creiamo 2 colonne per disporre le schede (griglia)
            col_sx, col_dx = st.columns(2)
            
            for i, item in enumerate(scorecard):
                # Alterniamo le colonne per layout a griglia
                with (col_sx if i % 2 == 0 else col_dx):
                    
                    # Box bordato per ogni area
                    with st.container(border=True):
                        # Header della scheda: Titolo e Score
                        head_c1, head_c2 = st.columns([3, 1])
                        head_c1.markdown(f"### {item.get('area')}")
                        
                        score = item.get('priorita_score', 0)
                        
                        # Colore e Testo della Priorità
                        if score >= 71:
                            priorita_txt = "ALTA"
                            priorita_color = "red"
                            head_c2.error(f"{score}/100\n{priorita_txt}")
                        elif score >= 31:
                            priorita_txt = "MEDIA"
                            priorita_color = "orange"
                            head_c2.warning(f"{score}/100\n{priorita_txt}")
                        else:
                            priorita_txt = "BASSA"
                            priorita_color = "green"
                            head_c2.success(f"{score}/100\n{priorita_txt}")
                        
                        # KPI in evidenza (lista puntata pulita)
                        st.markdown("**KPI Rilevati:**")
                        kpis = item.get('kpi_elenco', [])
                        # Se è una lista, stampali uno per uno
                        if isinstance(kpis, list):
                            for k in kpis:
                                st.markdown(f"- {k}")
                        else:
                            st.markdown(f"- {kpis}")
                            
                        # Box Commento dedicato
                        st.markdown("---")
                        st.markdown("**📝 Analisi Consulente:**")
                        st.info(item.get('analisi_consulente', 'Nessuna nota specifica.'))

        except Exception as e:
            st.error(f"Si è verificato un errore: {e}")
            with st.expander("Dettagli tecnici (per debug)"):
                st.code(raw_response)
