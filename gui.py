import streamlit as st
from app import grafo  # Ajusta el import si tu archivo se llama diferente

# ============================================================
# CONFIGURACIÓN
# ============================================================
st.set_page_config(
    page_title="OpenMint | Asistente Institucional",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ESTADO GLOBAL
# ============================================================
if "page" not in st.session_state:
    st.session_state.page = "bienvenida"
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "lang" not in st.session_state:
    st.session_state.lang = "es"
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# ============================================================
# TEXTOS (idioma completo)
# ============================================================
TEXTS = {
    "es": {
        "nav_welcome": "Bienvenida",
        "nav_docs": "Documentos",
        "nav_chat": "Chat IA",
        "nav_corporate": "Corporate Login",
        "nav_visitor": "Visitor Access",
        "title_welcome": "Bienvenido a OpenMint",
        "subtitle_welcome": "Nuestro agente de IA avanzado gestiona el triaje de RAG para políticas internas, contratos y reportes bancarios institucionales.",
        "btn_chat": "Acceso Chat IA",
        "btn_reports": "Explorar Reportes",
        "title_docs": "Centro de Documentación",
        "subtitle_docs": "Acceda de forma segura a los activos legales, técnicos y operativos de su institución.",
        "btn_upload": "Subir Documento",
        "btn_audit": "Explorar Auditorías",
        "chat_placeholder": "Escribe tu pregunta sobre políticas o procesos del banco...",
        "chat_title": "OpenMint AI Assistant",
        "rag_online": "RAG Engine Online",
        "sources": "Fuentes consultadas",
        "switch_role": "Cambiar Rol",
        "docs_loaded": "Documentos cargados",
        "quick_nav": "Navegación rápida",
        "card1_title": "Hybridización Bancaria",
        "card1_desc": "Gestione cuentas tradicionales e integración nativa de activos cripto.",
        "card1_tag": "Ecosistema Unificado",
        "card2_title": "RAG Triaging",
        "card2_desc": "Análisis profundo de documentos internos y contratos inteligentes.",
        "card2_tag": "98.2% Index Coverage",
        "card3_title": "Acceso Institucional",
        "card3_desc": "Protocolos de seguridad de grado bancario con validación HSM.",
        "card3_tag": "HSM Protocols Active",
        "doc_card1": "Políticas Institucionales",
        "doc_card1_desc": "Normativas de KYC, AML y gobernanza de tesorería.",
        "doc_card1_tag": "12 Documentos",
        "doc_card2": "Contratos Inteligentes",
        "doc_card2_desc": "Repositorio de smart contracts auditados.",
        "doc_card2_tag": "45 Despliegues",
        "doc_card3": "Auditorías y Reportes",
        "doc_card3_desc": "Pruebas de reserva (PoR) y estados financieros.",
        "doc_card3_tag": "Ver Último Reporte",
        "reset": "Reiniciar App",
        "consulting": "Consultando documentación...",
    },
    "en": {
        "nav_welcome": "Welcome",
        "nav_docs": "Documents",
        "nav_chat": "AI Chat",
        "nav_corporate": "Corporate Login",
        "nav_visitor": "Visitor Access",
        "title_welcome": "Welcome to OpenMint",
        "subtitle_welcome": "Our advanced AI agent manages RAG triage for internal policies, contracts and institutional banking reports.",
        "btn_chat": "Access AI Chat",
        "btn_reports": "Explore Reports",
        "title_docs": "Documentation Center",
        "subtitle_docs": "Securely access the legal, technical and operational assets of your institution.",
        "btn_upload": "Upload Document",
        "btn_audit": "Explore Audits",
        "chat_placeholder": "Ask about bank policies or processes...",
        "chat_title": "OpenMint AI Assistant",
        "rag_online": "RAG Engine Online",
        "sources": "Consulted sources",
        "switch_role": "Switch Role",
        "docs_loaded": "Loaded documents",
        "quick_nav": "Quick navigation",
        "card1_title": "Banking Hybridization",
        "card1_desc": "Manage traditional accounts and native crypto asset integration.",
        "card1_tag": "Unified Ecosystem",
        "card2_title": "RAG Triaging",
        "card2_desc": "Deep analysis of internal documents and smart contracts.",
        "card2_tag": "98.2% Index Coverage",
        "card3_title": "Institutional Access",
        "card3_desc": "Bank-grade security protocols with HSM validation.",
        "card3_tag": "HSM Protocols Active",
        "doc_card1": "Institutional Policies",
        "doc_card1_desc": "KYC, AML regulations and treasury governance.",
        "doc_card1_tag": "12 Documents",
        "doc_card2": "Smart Contracts",
        "doc_card2_desc": "Repository of audited smart contracts.",
        "doc_card2_tag": "45 Deployments",
        "doc_card3": "Audits & Reports",
        "doc_card3_desc": "Proof of Reserves (PoR) and financial statements.",
        "doc_card3_tag": "View Latest Report",
        "reset": "Reset App",
        "consulting": "Consulting documentation...",
    }
}

t = TEXTS[st.session_state.lang]

# ============================================================
# TEMA Y COLORES
# ============================================================
def get_theme():
    if st.session_state.theme == "dark":
        return {
            "bg": "#0e0e0f",
            "surface": "#1c1b1c",
            "surface2": "#201f20",
            "primary": "#cfbdff",
            "primary_container": "#6200ee",
            "secondary": "#7dffa2",
            "text": "#e5e2e3",
            "text_muted": "#cbc3d9",
            "border": "rgba(148, 141, 162, 0.25)",
            "glass": "rgba(32, 31, 32, 0.8)",
            "user_bubble": "rgba(125, 255, 162, 0.12)",
            "ai_bubble": "rgba(98, 0, 238, 0.15)",
            "accent": "#e9c400",
        }
    else:
        return {
            "bg": "#fdf7ff",
            "surface": "#ffffff",
            "surface2": "#f8f1ff",
            "primary": "#4800b2",
            "primary_container": "#6200ee",
            "secondary": "#006e2a",
            "text": "#1d1a25",
            "text_muted": "#494456",
            "border": "rgba(122, 116, 136, 0.25)",
            "glass": "rgba(255, 255, 255, 0.9)",
            "user_bubble": "rgba(0, 110, 42, 0.10)",
            "ai_bubble": "rgba(98, 0, 238, 0.08)",
            "accent": "#705d00",
        }

theme = get_theme()

# ============================================================
# CSS
# ============================================================
def inject_css():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background-color: {theme["bg"]} !important;
            color: {theme["text"]} !important;
        }}

        section[data-testid="stSidebar"] {{
            background-color: {theme["surface"]} !important;
            border-right: 1px solid {theme["border"]} !important;
        }}

        section[data-testid="stSidebar"] * {{
            color: {theme["text"]} !important;
        }}

        .main .block-container {{
            background-color: {theme["bg"]} !important;
            color: {theme["text"]} !important;
            padding-top: 1.5rem;
        }}

        h1, h2, h3, h4, h5, h6, p, span, div, label {{
            color: {theme["text"]} !important;
        }}

        .stButton > button {{
            background-color: {theme["primary_container"]} !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease;
        }}
        .stButton > button:hover {{
            filter: brightness(1.12);
            transform: translateY(-1px);
        }}

        .om-card {{
            background: {theme["glass"]} !important;
            border: 1px solid {theme["border"]} !important;
            border-radius: 16px;
            padding: 1.4rem;
            margin-bottom: 1rem;
            color: {theme["text"]} !important;
        }}

        .om-title {{
            font-size: 2.1rem;
            font-weight: 700;
            color: {theme["primary"]} !important;
            margin-bottom: 0.4rem;
        }}

        .om-subtitle {{
            color: {theme["text_muted"]} !important;
            font-size: 1.05rem;
            line-height: 1.5;
        }}

        .user-bubble {{
            background: {theme["user_bubble"]} !important;
            border: 1px solid {theme["border"]} !important;
            border-radius: 16px 16px 4px 16px;
            padding: 1rem 1.2rem;
            margin: 0.7rem 0;
            color: {theme["text"]} !important;
        }}

        .ai-bubble {{
            background: {theme["ai_bubble"]} !important;
            border: 1px solid {theme["border"]} !important;
            border-radius: 16px 16px 16px 4px;
            padding: 1rem 1.2rem;
            margin: 0.7rem 0;
            color: {theme["text"]} !important;
        }}

        .pdf-item {{
            padding: 0.35rem 0;
            color: {theme["text_muted"]} !important;
            font-size: 0.9rem;
        }}

        header {{
            background-color: transparent !important;
        }}

        #MainMenu, footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

inject_css()


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 0.8rem 0 1.2rem 0;">
        <h2 style="color:{theme['primary']}; margin:0; font-weight:800;">OpenMint</h2>
        <p style="color:{theme['secondary']}; font-size:0.72rem; margin:0; letter-spacing:1px;">INSTITUTIONAL DEFI</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if st.button(f"🏠  {t['nav_welcome']}", use_container_width=True, key="side_welcome"):
        st.session_state.page = "bienvenida"
        st.rerun()
    if st.button(f"📄  {t['nav_docs']}", use_container_width=True, key="side_docs"):
        st.session_state.page = "documentos"
        st.rerun()
    if st.button(f"💬  {t['nav_chat']}", use_container_width=True, key="side_chat"):
        st.session_state.page = "chat"
        st.rerun()

    st.markdown("---")
    
    # Botones de Tema e Idioma movidos a la barra lateral para mayor limpieza visual
    col_theme, col_lang = st.columns(2)
    with col_theme:
        if st.button("🌙" if st.session_state.theme == "light" else "☀️", use_container_width=True, key="side_theme"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
    with col_lang:
        if st.button("ES ↔ EN", use_container_width=True, key="side_lang"):
            st.session_state.lang = "en" if st.session_state.lang == "es" else "es"
            st.rerun()

    st.markdown("---")
    st.caption(t["docs_loaded"])

    # Lista de PDFs (solo nombres, sin descarga ni vista)
    pdfs = [
        "Políticas de Préstamo.pdf",
        "Contratos Cripto 2024.pdf",
        "Reporte Trimestral.pdf",
        "Reglamento de Operaciones.pdf",
        "Política de Mora.pdf"
    ]
    for pdf in pdfs:
        st.markdown(f"<div class='pdf-item'>📄 {pdf}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.button(t["switch_role"], use_container_width=True, type="secondary", key="switch_role")

# ============================================================
# PÁGINAS
# ============================================================

# ---------- BIENVENIDA ----------
if st.session_state.page == "bienvenida":
    st.markdown(f"<div class='om-title'>{t['title_welcome']}</div>", unsafe_allow_html=True)
    st.markdown(f"<p class='om-subtitle'>{t['subtitle_welcome']}</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        if st.button(t["btn_chat"], use_container_width=True, key="btn_chat_main"):
            st.session_state.page = "chat"
            st.rerun()
    with c2:
        if st.button(t["btn_reports"], use_container_width=True, key="btn_reports_main"):
            st.session_state.page = "documentos"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="om-card">
            <h3 style="margin-top:0;">{t['card1_title']}</h3>
            <p style="opacity:0.85; font-size:0.9rem;">{t['card1_desc']}</p>
            <span style="color:{theme['secondary']}; font-size:0.8rem;">● {t['card1_tag']}</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="om-card">
            <h3 style="margin-top:0;">{t['card2_title']}</h3>
            <p style="opacity:0.85; font-size:0.9rem;">{t['card2_desc']}</p>
            <span style="color:{theme['primary']}; font-size:0.8rem;">{t['card2_tag']}</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="om-card">
            <h3 style="margin-top:0;">{t['card3_title']}</h3>
            <p style="opacity:0.85; font-size:0.9rem;">{t['card3_desc']}</p>
            <span style="color:{theme['accent']}; font-size:0.8rem;">{t['card3_tag']}</span>
        </div>
        """, unsafe_allow_html=True)

# ---------- DOCUMENTOS ----------
elif st.session_state.page == "documentos":
    st.markdown(f"<div class='om-title'>{t['title_docs']}</div>", unsafe_allow_html=True)
    st.markdown(f"<p class='om-subtitle'>{t['subtitle_docs']}</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.button(t["btn_upload"], use_container_width=True, key="btn_upload")
    with c2:
        st.button(t["btn_audit"], use_container_width=True, key="btn_audit")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="om-card">
            <h3>{t['doc_card1']}</h3>
            <p style="opacity:0.85; font-size:0.9rem;">{t['doc_card1_desc']}</p>
            <span style="color:{theme['secondary']};">{t['doc_card1_tag']}</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="om-card">
            <h3>{t['doc_card2']}</h3>
            <p style="opacity:0.85; font-size:0.9rem;">{t['doc_card2_desc']}</p>
            <span style="color:{theme['secondary']};">{t['doc_card2_tag']}</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="om-card">
            <h3>{t['doc_card3']}</h3>
            <p style="opacity:0.85; font-size:0.9rem;">{t['doc_card3_desc']}</p>
            <span style="color:{theme['primary']};">{t['doc_card3_tag']}</span>
        </div>
        """, unsafe_allow_html=True)

# ---------- CHAT IA ----------
elif st.session_state.page == "chat":
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:1.5rem;">
        <div style="width:42px; height:42px; background:{theme['primary_container']}; border-radius:12px;
                    display:flex; align-items:center; justify-content:center; font-size:1.3rem;">
            🤖
        </div>
        <div>
            <div style="font-weight:700; font-size:1.3rem; color:{theme['text']};">{t['chat_title']}</div>
            <div style="font-size:0.8rem; color:{theme['secondary']};">● {t['rag_online']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    for mensaje in st.session_state.mensajes:
        css_class = "user-bubble" if mensaje["rol"] == "user" else "ai-bubble"
        st.markdown(f"<div class='{css_class}'>{mensaje['contenido']}</div>", unsafe_allow_html=True)

    prompt = st.chat_input(t["chat_placeholder"])

    if prompt:
        st.session_state.mensajes.append({"rol": "user", "contenido": prompt})
        st.markdown(f"<div class='user-bubble'>{prompt}</div>", unsafe_allow_html=True)

        with st.spinner(t["consulting"]):
            try:
                respuesta = grafo.invoke({"pregunta": prompt})
                texto = respuesta.get("respuesta", "No se pudo generar una respuesta.")
                citaciones = respuesta.get("citaciones", [])

                st.session_state.mensajes.append({"rol": "assistant", "contenido": texto})
                st.markdown(f"<div class='ai-bubble'>{texto}</div>", unsafe_allow_html=True)

                if citaciones:
                    with st.expander(t["sources"]):
                        for i, doc in enumerate(citaciones):
                            archivo = doc.metadata.get("file_path", "Desconocido")
                            st.markdown(f"**Documento {i+1}:** `{archivo}`")
                            content = doc.page_content
                            st.info(content[:400] + "..." if len(content) > 400 else content)
            except Exception as e:
                st.error(f"Error: {e}")
                