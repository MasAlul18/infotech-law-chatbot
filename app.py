import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# ====================================================
# LOAD ENVIRONMENT
# ====================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ API Key Gemini tidak ditemukan. Pastikan file .env sudah benar.")
    st.stop()

genai.configure(api_key=api_key)

# ====================================================
# SYSTEM INSTRUCTION
# ====================================================

SYSTEM_INSTRUCTION = """
Kamu adalah Infotech Law Bot.

Kamu merupakan asisten AI yang ahli di bidang:

- Hukum Teknologi Informasi Indonesia
- UU ITE
- Perlindungan Data Pribadi (UU PDP)
- Cyber Law
- Forensik Digital
- Hukum Administrasi Negara
- Hukum Tata Negara
- Regulasi Digital Indonesia

Aturan menjawab:

- Gunakan bahasa Indonesia yang sopan.
- Berikan jawaban edukatif.
- Sertakan dasar hukum bila memungkinkan.
- Jangan membuat informasi palsu.
- Jika tidak yakin, katakan bahwa informasi perlu diverifikasi.
- Jelaskan secara mudah dipahami masyarakat umum.
"""

# ====================================================
# MODEL GEMINI
# ====================================================
# Beberapa nama model yang umum tersedia di API v1beta saat ini.
# Kode akan mencoba satu per satu sampai ada yang berhasil dibuat,
# supaya tidak gampang error 404 hanya karena nama model berubah.

CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
]

def build_model():
    last_error = None
    for name in CANDIDATE_MODELS:
        try:
            m = genai.GenerativeModel(
                model_name=name,
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config={
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                },
            )
            # Uji kecil supaya kita tahu modelnya benar-benar valid,
            # bukan cuma berhasil dibuat objeknya.
            m.generate_content("ping", generation_config={"max_output_tokens": 5})
            return m, name
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(
        f"Tidak ada model kandidat yang berhasil dipakai. Error terakhir: {last_error}"
    )

if "model" not in st.session_state or "model_name" not in st.session_state:
    try:
        model, used_model_name = build_model()
        st.session_state.model = model
        st.session_state.model_name = used_model_name
    except Exception as e:
        st.error(
            "❌ Tidak bisa membuat model Gemini apa pun dari daftar kandidat.\n\n"
            f"Detail error: {e}\n\n"
            "Jalankan perintah berikut secara terpisah untuk melihat model apa saja "
            "yang benar-benar tersedia untuk API key-mu:\n\n"
            "```python\n"
            "import google.generativeai as genai\n"
            "genai.configure(api_key='API_KEY_KAMU')\n"
            "for m in genai.list_models():\n"
            "    print(m.name, m.supported_generation_methods)\n"
            "```\n\n"
            "Lalu ganti isi CANDIDATE_MODELS di kode ini dengan nama model yang muncul di sana."
        )
        st.stop()

model = st.session_state.model

# ====================================================
# STREAMLIT CONFIG
# ====================================================

st.set_page_config(
    page_title="Infotech Law Chatbot",
    page_icon="⚖️",
    layout="centered",
)

st.title("⚖️ Infotech Law Chatbot")

st.caption(
    "Asisten AI Edukatif mengenai Hukum Teknologi Informasi, "
    "UU ITE, Perlindungan Data Pribadi, Cyber Law, "
    "dan Regulasi Digital Indonesia."
)

st.caption(f"Model aktif: `{st.session_state.model_name}`")

st.divider()

# ====================================================
# SIDEBAR
# ====================================================

with st.sidebar:

    st.header("Tentang")

    st.info(
        """
Bot ini menggunakan Google Gemini API.

Fitur:
- UU ITE
- UU PDP
- Cyber Law
- Hukum Digital
- Hukum Administrasi Negara
- Regulasi Teknologi Informasi
        """
    )

    st.divider()

    st.subheader("Cara Menggunakan")

    st.markdown("""
1. Ketik pertanyaan.
2. Tekan Enter.
3. Tunggu jawaban AI.
    """)

    if st.button("🗑️ Hapus Riwayat Chat"):
        st.session_state.chat_history = []
        st.rerun()

# ====================================================
# SESSION STATE
# ====================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ====================================================
# MENAMPILKAN HISTORY
# ====================================================

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["text"])

# ====================================================
# INPUT USER
# ====================================================

user_input = st.chat_input("Tanyakan sesuatu tentang hukum digital...")

if user_input:

    # tampilkan pesan user
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.chat_history.append(
        {
            "role": "user",
            "text": user_input,
        }
    )

    # membuat context dari riwayat chat
    conversation = ""

    for msg in st.session_state.chat_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation += f"{role}: {msg['text']}\n"

    with st.chat_message("assistant"):

        with st.spinner("⚖️ Sedang menganalisis aspek hukum..."):

            try:

                response = model.generate_content(conversation)

                bot_reply = response.text

                st.markdown(bot_reply)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "text": bot_reply,
                    }
                )

            except Exception as e:

                st.error(f"Terjadi kesalahan:\n\n{e}")