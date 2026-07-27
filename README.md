# 🏦 Banco OpenMint - Agente Inteligente (RAG)

Este repositorio contiene el código fuente de un Agente Inteligente basado en la arquitectura de **Generación Aumentada por Recuperación (RAG)**, desarrollado como proyecto para Alura. El agente está diseñado para interactuar con los usuarios y responder preguntas precisas extrayendo información directamente de documentos proporcionados (PDF o CSV).

🔗 **Enlace de la Aplicación Desplegada:** [Banco OpenMint Agentic RAG en Streamlit](https://banco-openmint-agentic-rag.streamlit.app/)

---

## 📖 Descripción General del Proyecto

El objetivo principal de este proyecto es brindar un asistente virtual capaz de procesar y comprender documentos institucionales o financieros del "Banco OpenMint". A través de una interfaz amigable, el agente recibe las consultas del usuario, busca el contexto relevante dentro de los documentos procesados y genera una respuesta coherente, natural y fundamentada en los datos reales suministrados, evitando alucinaciones.

---

## 🏗️ Arquitectura de la Solución

El sistema está diseñado utilizando una separación clara entre la lógica del agente y la interfaz de usuario:

1. **Interfaz de Usuario (Frontend):** Gestionada a través de `gui.py` utilizando Streamlit, proporcionando una experiencia interactiva donde el usuario puede cargar documentos (PDF/CSV) y chatear con el agente.
2. **Lógica del Agente (Backend & Orquestación):** Concentrada en `app.py`, donde se utiliza **LangGraph** para estructurar el flujo de razonamiento y recuperación de información del agente.
3. **Procesamiento y Recuperación (RAG):**
   * **Lectura de Documentos:** El sistema extrae el texto de archivos PDF o CSV.
   * **Embeddings:** Se utiliza el modelo `paraphrase-multilingual-MiniLM-L12-v2` para transformar los fragmentos de texto en vectores matemáticos de alta precisión, optimizados para múltiples idiomas (incluyendo español).
   * **Base de Datos Vectorial:** Los vectores se almacenan (ej. usando FAISS) para realizar búsquedas de similitud cuando el usuario hace una pregunta.
4. **Generación de Respuesta:** El contexto recuperado se envía a un modelo de lenguaje de gran tamaño (LLM) a través de la API de **Groq**, el cual sintetiza la respuesta final.

---

## 🛠️ Tecnologías y Herramientas Utilizadas

* **Python:** Lenguaje de programación principal.
* **Streamlit:** Framework para el desarrollo de la interfaz gráfica y el despliegue web.
* **LangGraph / LangChain:** Herramientas para la orquestación del flujo de trabajo del agente y el pipeline RAG.
* **Groq API:** Proveedor de inferencia ultrarrápida para el modelo de lenguaje (LLM).
* **HuggingFace (`paraphrase-multilingual-MiniLM-L12-v2`):** Modelo utilizado para la generación de embeddings de texto.
* **Git & GitHub:** Control de versiones y alojamiento del repositorio público.

---

## 📂 Estructura del Repositorio

El repositorio está organizado de la siguiente manera para facilitar su comprensión y mantenimiento:

```text
Banco_OpenMint_Proyecto_Alura/
│
├── app.py                 # Lógica principal del agente RAG y orquestación con LangGraph
├── gui.py                 # Interfaz de usuario construida con Streamlit
├── requirements.txt       # Dependencias necesarias para ejecutar el proyecto
├── .gitignore             # Archivos y carpetas ignorados por Git (ej. .env, __pycache__)
├── /faiss_index/          # Directorio para el almacenamiento de la base de datos vectorial
└── /evidence/             # Carpeta que contiene las imágenes y evidencias del funcionamiento

🚀 Instrucciones para Ejecutar el Proyecto (Local)
Si deseas clonar y ejecutar este proyecto en tu propia máquina, sigue estos pasos:

Clonar el repositorio:

Bash
git clone [https://github.com/AEnocRs/Banco_OpenMint_Proyecto_Alura.git](https://github.com/AEnocRs/Banco_OpenMint_Proyecto_Alura.git)
cd Banco_OpenMint_Proyecto_Alura
Crear un entorno virtual (Recomendado):

Bash
python -m venv venv
source venv/bin/activate  # En Windows usa: venv\Scripts\activate
Instalar las dependencias:

Bash
pip install -r requirements.txt
Configurar las Variables de Entorno:
Crea un archivo .env en la raíz del proyecto y agrega tu clave de API de Groq:

Fragmento de código
GROQ_API_KEY=tu_clave_de_groq_aqui
Ejecutar la aplicación:

Bash
streamlit run gui.py
💬 Ejemplos de Interacción con el Agente
Una vez cargado un documento de ejemplo (como las políticas de cuentas del Banco OpenMint), el agente es capaz de responder preguntas específicas basándose únicamente en ese contexto.

Ejemplo 1:

Usuario (Pregunta): "¿Cuáles son los requisitos obligatorios para abrir una Cuenta de Ahorro Premium?"

Agente (Respuesta): "Según el documento proporcionado, para abrir una Cuenta de Ahorro Premium se requiere: 1) Documento de identidad vigente, 2) Comprobante de domicilio no mayor a 3 meses, y 3) Un depósito inicial mínimo de $500.00."

Ejemplo 2:

Usuario (Pregunta): "¿Cuál es la tasa de interés anual para los préstamos personales?"

Agente (Respuesta): "El archivo CSV de tasas indica que la tasa de interés anual (TEA) para préstamos personales varía entre el 12% y el 15.5%, dependiendo de la evaluación crediticia del cliente."

📸 Evidencia del Deploy y Funcionamiento
A continuación, se muestra la aplicación funcionando correctamente en producción dentro de Streamlit Cloud, demostrando la capacidad del agente inteligente.

(La interfaz principal del agente desplegado)

(Ejemplo de carga de documento y respuesta del RAG)

Proyecto desarrollado con dedicación para el Challenge de Alura.