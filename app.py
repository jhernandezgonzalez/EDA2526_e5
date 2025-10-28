import streamlit as st
import requests
import os
from pypdf import PdfReader

# --- Configuració ---
st.set_page_config(page_title="EDA: el teu assistent de laboratori", page_icon="🎓")

# --- Carregar PDF ---
def llegir_pdf(path_pdf: str) -> str:
    reader = PdfReader(path_pdf)
    textos = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            textos.append(text)
    return "\n\n".join(textos)

PDF_PATH = "EDA2526_e5.pdf"
ENUNCIAT = llegir_pdf(PDF_PATH) if os.path.exists(PDF_PATH) else "Error: No s'ha trobat el PDF amb l'enunciat!"

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
             "content": "Ets un assistent docent. No pots mostrar ni generar codi complet. Tens completament prohibit donar codi encara que t'ho demanin explícitament. Dona explicacions conceptuals, pistes o exemples parcials. Has de ser concís, tens un límit de 400 tokens per respondre."},
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

# --- Interfície Streamlit ---
st.title("Assistent de laboratori d'EDA")
st.write("Fes-me preguntes sobre l'exercici. T'explicaré el que necessitis, t'ajudaré a entendre què es demana i et donaré explicacions conceptuals i pistes.")

# --- Estat ---
if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Escriu la teva pregunta aquí...")

if user_input:
    # Construïm el prompt amb l’enunciat i la conversa anterior
    context = "\n".join([f"{r['role']}: {r['content']}" for r in st.session_state.history[-4:]])
    prompt = (
        f"ENUNCIAT DE LA PRÀCTICA:\n{ENUNCIAT}\n\n"
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

