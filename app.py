import streamlit as st
import google.generativeai as genai
import json
import os

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Corporate Advisor IA", layout="wide")

# --- CUSTOM CSS (GRAFICA) ---
st.markdown("""
    <style>
    /* 1. Sfondo generale dell'applicazione (Azzurrino Chiaro) */
    .stApp {
        background-color: #F0F8FF;
    }
    
    /* 2. FORZA TESTO NERO SU TUTTO */
    h1, h2, h3, h4, h5, h6, p, li, span, div, label {
        color: #000000 !important;
    }

    /* 3. Eccezioni per mantenere leggibili i box colorati (Alert/Warning/Error) */
    /* Qui lasciamo che Streamlit gestisca il colore, altrimenti non si legge su sfondo scuro */
    div[data-testid="stAlert"] div, div[data-testid="stAlert"] p {
        color: inherit !important;
    }

    /* 4. Stile delle CARD (Sfondo bianco + Bordo + Ombra) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }
    
    /* 5. Fix specifico per le METRICHE (Numeri grandi) */
    div[data-testid="stMetricValue"] {
        color: #000000 !important; /* Numero nero */
    }
    div[data-testid="stMetricLabel"] {
        color: #333333 !important; /* Etichetta grigio scuro quasi nero */
    }
    /* La freccetta (Delta) la lasciamo colorata (Rosso/Verde) per capire il trend */
    div[data-testid="stMetricDelta"] svg {
        /* Non forziamo il nero qui, altrimenti perdiamo l'info su crescita/decrescita */
    }
    </style>
    """, unsafe_allow_html=True)

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
    
    default_index = 0
    for i, name in enumerate(model_list):
        if "flash" in name and "1.5" in name:
            default_index = i
            break
            
    selected_model = st.sidebar.selectbox("Modello AI:", model_list, index=default_index)

except Exception as e:
    st.sidebar.error(f"Errore caricamento modelli: {e}")
    st.stop()

# --- 3. SYSTEM PROMPT ---
SYSTEM_INSTRUCTION = """
Sei un Senior Private Banker Corporate.
Analizza il PDF (Scheda Azimut) e restituisci un JSON per guidare l'azione commerciale.

**LOGICA SCORE (PRIORITÀ DI VISITA):**
Lo score (0-100) indica L'URGENZA.
- 0-30: Bassa Priorità (Azienda statica/sana).
- 31-70: Media Priorità (Spunti di miglioramento).
- 71-100: ALTA PRIORITÀ (Urgenza di intervento: eccesso liquidità, troppo debito breve, rischi soci).

**FORMATO JSON RICHIESTO:**
{
  "anagrafica": { 
    "ragione_sociale": "Nome completo azienda SRL/SPA", 
    "fatturato_milioni": "Es. € 4.8M (converti valore in Milioni)", 
    "trend_fatturato": "Crescente/Decrescente/Stabile"
  },
  "sintesi_executive": "Descrizione dettagliata (minimo 3 righe) delle azioni pratiche da fare. Esempio: 'Priorità massima sul TFR che sta crescendo troppo. Proporre subito Welfare o Fondo Pensione. Attenzione anche al debito a breve...'",
  "scorecard": [
    { 
      "area": "Gestione Tesoreria", 
      "priorita_score": 0, 
      "colore": "rosso/giallo/verde", 
      "kpi_elenco": ["Liquidità: € ...", "Ciclo cassa: ... giorni"], 
      "analisi_consulente": "Breve commento tecnico."
    },
    { 
      "area": "Debito Corporate", 
      "priorita_score": 0, 
      "colore": "rosso/giallo/verde", 
      "kpi_elenco": ["PFN/EBITDA: ...x", "Debiti Breve: € ..."], 
      "analisi_consulente": "Breve commento tecnico."
    },
    { 
      "area": "Assetti Proprietari", 
      "priorita_score": 0, 
      "colore": "rosso/giallo/verde", 
      "kpi_elenco": ["Holding: Si/No", "Età Soci Key: ..."], 
      "analisi_consulente": "Breve commento tecnico."
    },
    { 
      "area": "Wealth Planning", 
      "priorita_score": 0, 
      "colore": "rosso/giallo/verde", 
      "kpi_elenco": ["Utile Netto: € ...", "Riserve/PN: ..."], 
      "analisi_consulente": "Breve commento tecnico."
    },
    { 
      "area": "TFR e Previdenza", 
      "priorita_score": 0, 
      "colore": "rosso/giallo/verde", 
      "kpi_elenco": ["Stock TFR: € ...", "Num Dipendenti: ..."], 
      "analisi_consulente": "Breve commento tecnico."
    }
  ]
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
        "Genera il JSON."
    ]
    response = model.generate_content(prompt_parts)
    return response.text

# --- 4. INTERFACCIA GRAFICA ---
st.title("Corporate Advisor IA")
st.markdown("Carica la Scheda Azimut per generare il piano d'azione.")

uploaded_file = st.file_uploader("Carica PDF", type="pdf")

if uploaded_file is not None:
    with st.spinner(f'Analisi strategica in corso...'):
        try:
            raw_response = analizza_pdf(uploaded_file, selected_model)
            
            # Pulizia JSON
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            if "{" in clean_json:
                clean_json = clean_json[clean_json.find("{"):clean_json.rfind("}")+1]
            
            data = json.loads(clean_json)
            anag = data.get('anagrafica', {})

            # --- HEADER PRINCIPALE ---
            col_head_1, col_head_2 = st.columns([3, 1])
            
            with col_head_1:
                st.header(anag.get('ragione_sociale', 'Azienda non identificata'))
                st.caption("Analisi basata su Bilancio Riclassificato")
            
            with col_head_2:
                # LOGICA PER FRECCIA E COLORE DEL FATTURATO
                trend = anag.get('trend_fatturato', 'Stabile')
                delta_val = "Stabile"
                
                if "Decrescente" in trend or "calo" in trend.lower():
                    delta_val = "- In Calo" 
                elif "Crescente" in trend or "crescita" in trend.lower():
                    delta_val = "+ In Crescita"
                else:
                    delta_val = "Stabile"

                st.metric(
                    label="Fatturato (Ultimo Esercizio)", 
                    value=anag.get('fatturato_milioni', 'N/A'),
                    delta=delta_val
                )

            # --- BOX SINTESI AZIONI ---
            st.divider()
            st.subheader("⚡ Sintesi azioni da fare")
            st.warning(data.get('sintesi_executive', 'Nessuna azione specifica rilevata.'))
            st.divider()

            # --- SCORECARD ---
            st.subheader("📊 Analisi Priorità per Area")
            
            scorecard = data.get('scorecard', [])
            col_sx, col_dx = st.columns(2)
            
            for i, item in enumerate(scorecard):
                with (col_sx if i % 2 == 0 else col_dx):
                    
                    with st.container(border=True):
                        # Header Scheda
                        head_c1, head_c2 = st.columns([3, 1])
                        head_c1.markdown(f"### {item.get('area')}")
                        
                        score = item.get('priorita_score', 0)
                        
                        # Logica Colore Priorità (Rosso = Alta Urgenza)
                        if score >= 71:
                            priorita_txt = "ALTA"
                            head_c2.error(f"{score}\n{priorita_txt}")
                        elif score >= 31:
                            priorita_txt = "MEDIA"
                            head_c2.warning(f"{score}\n{priorita_txt}")
                        else:
                            priorita_txt = "BASSA"
                            head_c2.success(f"{score}\n{priorita_txt}")
                        
                        # KPI
                        st.markdown("**KPI Rilevati:**")
                        kpis = item.get('kpi_elenco', [])
                        if isinstance(kpis, list):
                            for k in kpis:
                                st.markdown(f"- {k}")
                        else:
                            st.markdown(f"- {kpis}")
                            
                        # Commento
                        st.markdown("---")
                        st.caption("📝 Note Consulente:")
                        st.info(item.get('analisi_consulente', ''))

        except Exception as e:
            st.error(f"Errore: {e}")
