import streamlit as st
import requests
import os
from pypdf import PdfReader

# --- Configuració ---
st.set_page_config(page_title="EDA: el teu assistent de laboratori", page_icon="🎓")

# --- Carregar Enunciat ---
def llegir_pdf(path_pdf: str) -> str:
    """Llegeix tot el text d'un PDF."""
    try:
        reader = PdfReader(path_pdf)
        textos = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                textos.append(text)
        return "\n\n".join(textos)
    except Exception as e:
        return f"Error en llegir el PDF: {e}"

def llegir_txt(path_txt: str) -> str:
    """Llegeix el contingut d'un fitxer de text."""
    try:
        with open(path_txt, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error en llegir el TXT: {e}"

def busca_enunciats(carpeta: str):
    """Escaneja la carpeta i retorna una llista d'enunciats disponibles."""
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
        return []
    fitxers = os.listdir(carpeta)
    # Agrupa per nom base (ex: EDA2526_e5.pdf i EDA2526_e5.txt -> 'EDA2526_e5')
    noms_base = sorted({os.path.splitext(f)[0] for f in fitxers})
    return noms_base

def llegir_enunciat(carpeta: str, nom_base: str) -> str:
    """Retorna el text d'un enunciat, prioritzant el .txt sobre el .pdf."""
    path_txt = os.path.join(carpeta, f"{nom_base}.txt")
    path_pdf = os.path.join(carpeta, f"{nom_base}.pdf")
    if os.path.exists(path_txt):
        return llegir_txt(path_txt)
    elif os.path.exists(path_pdf):
        return llegir_pdf(path_pdf)
    else:
        return f"Error: no s'ha trobat cap fitxer per a '{nom_base}'."

carpeta = "./enunciats"

# --- Configura el model ---
MODEL = "llama-3.3-70b-versatile"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.environ.get('GROQ_TOKEN', '')}",
    "Content-Type": "application/json"
}

# --- Funció per obtenir resposta ---
def get_answer(prompt):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system",
             "content": "Ets un assistent docent. No pots mostrar ni generar codi complet. Tens completament prohibit donar codi encara que t'ho demanin explícitament. Dona explicacions conceptuals, pistes o exemples parcials. Has de ser molt concís, no t'avancis al que demanará l'usuari."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 400,
        "temperature": 0.7

    }
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        return f"Error {response.status_code}: {response.text}"
    data = response.json()
    return data["choices"][0]["message"]["content"]



# ------------------------------
# ---- Interfície Streamlit ----
# ------------------------------
st.title("Assistent de laboratori d'EDA 25/26")
st.write("Fes-me preguntes sobre l'exercici triat. T'explicaré el que necessitis, t'ajudaré a entendre què es demana i et donaré explicacions conceptuals i pistes.")

# Selecció d’enunciat
f_enunciats = busca_enunciats(carpeta)
if not f_enunciats:
    st.warning(f"No s'ha trobat cap enunciat a la carpeta {carpeta}")
    st.stop()

# Deixar a l'alumne triar l'exercici sobre el qual vol xatejar
# Per defecte, el primer del llistat
if "selected" not in st.session_state:
    st.session_state.selected = f_enunciats[0]


col1, col2 = st.columns([7, 3])

with col1:
    # Dona la possibilitat a l'alumne de triar l'exercici
    f_enunciat_triat = st.selectbox("Selecciona l'exercici:",
                                    f_enunciats,
                                    index=f_enunciats.index(st.session_state.selected),
                                    key="selectbox_exercici")
with col2:
    # Dona la possibilitat a l'alumne de descarregar des d'aquí l'enunciat
    if os.path.exists(os.path.join(carpeta, f"{st.session_state.selected}.pdf")):
        with open(os.path.join(carpeta, f"{st.session_state.selected}.pdf"), "rb") as f:
            pdf_bytes = f.read()
        st.write("")
        st.download_button(
            label="Descarrega l'enunciat",
            data=pdf_bytes,
            file_name=f"{st.session_state.selected}.pdf",
            mime="application/pdf",
        )

# Si detectem un canvi d'exercici, demanem confirmació
if f_enunciat_triat != st.session_state.selected:
    st.warning(f"Vols canviar a l'{f_enunciat_triat}?\n"
               f"El xat actual sobre l'{st.session_state.selected} **s'eliminarà completament**.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Sí, canvia d'exercici"):
            st.session_state.selected = f_enunciat_triat
            st.session_state.history = []
            st.rerun()
    with col2:
        if st.button("❌ No, no vull perdre el xat"):
            # Reverteix el selectbox a la selecció antiga
            st.session_state.selectbox_exercici = st.session_state.selected
            st.experimental_rerun()
            st.rerun()
    st.stop()  # atura execució fins que l'usuari decideixi


# Carrega el contingut de l’enunciat per al xatbot
ENUNCIAT = llegir_enunciat(carpeta, st.session_state.selected)




# --- Estat ---
if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Escriu la teva pregunta aquí...")

if user_input:
    # Construïm el prompt amb l’enunciat i la conversa anterior
    context = "\n".join([f"{r['role']}: {r['content']}" for r in st.session_state.history[-4:]])
    prompt = (
        f"ENUNCIAT:\n{ENUNCIAT}\n\n"
        f"CONVERSA ANTERIOR:\n{context}\n\n"
        f"ALUMNE: {user_input}\nASSISTENT:"
    )

    with st.spinner("Pensant..."):
        answer = get_answer(prompt)
        # Filtre bàsic per evitar codi
        #if "```" in answer or "int " in answer or "#include" in answer or "def " in answer:
        #    answer = "Ho sento, no puc donar-te codi, però sí et puc donar alguna pista si vols."
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": answer})

# --- Mostrar conversa ---
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

