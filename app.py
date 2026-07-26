from typing import TypedDict, Optional, Literal, List, Dict
from pydantic import BaseModel, Field
import os
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. ESTADO Y MODELOS
# ============================================================

class AgentState(TypedDict, total=False):
    pregunta: str
    triaje: dict
    respuesta: Optional[str]
    citaciones: Optional[list]
    rag_exito: bool
    accion_final: str
    motivo_no_respuesta: Optional[Literal["NO_DOCUMENTS_FOUND", "LLM_COULD_NOT_ANSWER", None]]


class TriajeOut(BaseModel):
    decision: Literal["AUTO_RESOLVER", "PEDIR_INFO", "ABRIR_TICKET", "OUT_OF_SCOPE"]
    urgencia: Literal["BAJA", "MEDIANA", "ALTA"]
    campos_faltantes: List[str] = Field(default_factory=list)


# ============================================================
# 2. PROMPTS RE-ENCUADRADOS
# ============================================================

PROMPT_TRIAJE = """
Eres el especialista de triaje del Banco Digital OpenMint.
Tu única tarea es clasificar el mensaje del usuario y devolver SOLO un JSON válido con esta estructura:

{
  "decision": "AUTO_RESOLVER" | "PEDIR_INFO" | "ABRIR_TICKET" | "OUT_OF_SCOPE",
  "urgencia": "BAJA" | "MEDIANA" | "ALTA",
  "campos_faltantes": []
}

Reglas de decisión:

- AUTO_RESOLVER: Preguntas claras sobre políticas, reglamentos, procedimientos, comisiones, condiciones de productos, staking, mora, congelamientos, contratos inteligentes o cualquier documento interno del banco.
- PEDIR_INFO: Mensajes vagos, incompletos o sin suficiente contexto para identificar el tema (ej. "necesito ayuda con una política", "tengo un problema").
- ABRIR_TICKET: Solicitudes de excepción, autorización especial, problemas de acceso, fallos técnicos o cuando el usuario pide explícitamente abrir un ticket.
- OUT_OF_SCOPE: Preguntas que no tienen ninguna relación con el banco, sus productos o sus políticas (ej. capitales de países, clima, recetas, etc.).

Analiza el mensaje y elige la decisión más adecuada. No inventes información.
"""

PROMPT_RAG_SYSTEM = """
Eres el asistente oficial de políticas y documentación del Banco Digital OpenMint.

Reglas estrictas:
1. Responde ÚNICAMENTE basándote en el contexto que se te proporciona.
2. Si el contexto contiene la información necesaria, responde de forma clara, profesional y en español.
3. Si el contexto NO contiene la información suficiente para responder con seguridad, responde exactamente con esta frase:
   "No poseo la información suficiente en la documentación disponible para responder a tu pregunta."
4. Nunca inventes datos, cifras, plazos ni condiciones.
5. No menciones que eres un modelo de lenguaje ni que usas RAG.
6. No digas "según el contexto" ni frases similares; responde de forma natural.
"""

# ============================================================
# 3. LLM
# ============================================================

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import SystemMessage, HumanMessage

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=os.environ.get("GROQ_API_KEY")
)

prompt_rag = ChatPromptTemplate.from_messages([
    ("system", PROMPT_RAG_SYSTEM),
    ("human", "Contexto:\n{context}\n\nPregunta del empleado:\n{input}")
])

document_chain = create_stuff_documents_chain(llm, prompt_rag)
chain_de_triaje = llm.with_structured_output(TriajeOut)


def triaje(mensaje: str) -> Dict:
    salida: TriajeOut = chain_de_triaje.invoke([
        SystemMessage(content=PROMPT_TRIAJE),
        HumanMessage(content=mensaje)
    ])
    return salida.model_dump()


# ============================================================
# 4. CARGA DE DOCUMENTOS
# ============================================================

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
import pandas as pd

docs = []

# PDFs
for documentos in Path("./content/").glob("*.pdf"):
    try:
        loader = PyMuPDFLoader(str(documentos))
        docs.extend(loader.load())
        print(f"Archivo cargado: {documentos.name}")
    except Exception as e:
        print(f"Error cargando archivo: {documentos.name}: {e}")

print(f"Total de documentos PDF cargados: {len(docs)}")

# CSVs
csv_docs = []
for csv_file in Path("./content/").glob("*.csv"):
    try:
        df = pd.read_csv(csv_file, sep=';')
        for index, row in df.iterrows():
            row_content = ", ".join([f"{col}: {str(row[col])}" for col in df.columns])
            csv_docs.append(Document(
                page_content=row_content,
                metadata={
                    "file_path": str(csv_file),
                    "row_number": index,
                    "source_type": "csv",
                    "periodo": row.get('Periodo'),
                    "anio": row.get('Anio'),
                    "mes": row.get('Mes')
                }
            ))
        print(f"Archivo CSV cargado: {csv_file.name}")
    except Exception as e:
        print(f"Error cargando archivo CSV: {csv_file.name}: {e}")

docs.extend(csv_docs)
print(f"Total de documentos (PDFs + CSVs) cargados: {len(docs)}")

# ============================================================
# 5. SPLITTING + EMBEDDINGS + FAISS  (versión corregida)
# ============================================================ 

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings   # ← versión nueva (recomendado)
from langchain_community.vectorstores import FAISS

splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
chunks = splitter.split_documents(docs)

# Embedding multilingual (mejor para español)
modelo_embeddings = HuggingFaceEmbeddings(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

FAISS_PATH = "faiss_index"
FAISS_TIMESTAMP_FILE = "faiss_index_timestamp.txt"


def get_latest_source_mod_time() -> datetime.datetime:
    latest_mtime = datetime.datetime.min
    source_files = list(Path("./content/").glob("*.pdf")) + list(Path("./content/").glob("*.csv"))
    if not source_files:
        return datetime.datetime.min

    for file_path in source_files:
        try:
            mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime > latest_mtime:
                latest_mtime = mtime
        except FileNotFoundError:
            print(f"Advertencia: Archivo no encontrado: {file_path}")
    return latest_mtime


current_sources_mod_time = get_latest_source_mod_time()
rebuild_faiss = True          # ← forzamos reconstrucción siempre la primera vez

# Si quieres que solo reconstruya cuando cambien los PDFs, cambia a False
# y borra manualmente la carpeta faiss_index cuando cambies de modelo.

if os.path.exists(FAISS_PATH) and os.path.exists(FAISS_TIMESTAMP_FILE) and not rebuild_faiss:
    try:
        with open(FAISS_TIMESTAMP_FILE, 'r') as f:
            last_faiss_build_time_str = f.read().strip()
            if last_faiss_build_time_str:
                last_faiss_build_time = datetime.datetime.fromisoformat(last_faiss_build_time_str)
            else:
                rebuild_faiss = True

        if not rebuild_faiss and current_sources_mod_time > last_faiss_build_time:
            print("Los archivos fuente son más nuevos. Reconstruyendo...")
            rebuild_faiss = True
        elif not rebuild_faiss:
            print("Cargando vectorstore FAISS existente...")
            vectorstore = FAISS.load_local(
                FAISS_PATH,
                modelo_embeddings,
                allow_dangerous_deserialization=True
            )
            # === CAMBIO CLAVE: usamos similarity (top-k) en lugar de score_threshold ===
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            )
            print("Vectorstore FAISS cargado.")
    except Exception as e:
        print(f"Error al cargar FAISS: {e}. Forzando reconstrucción...")
        rebuild_faiss = True
else:
    rebuild_faiss = True

if rebuild_faiss:
    print("Construyendo nuevo vectorstore FAISS con embedding multilingual...")
    vectorstore = FAISS.from_documents(chunks, modelo_embeddings)
    
    # === CAMBIO CLAVE ===
    retriever = vectorstore.as_retriever(
        search_type="similarity",          # top-k puro (más fiable)
        search_kwargs={"k": 4}
    )
    
    vectorstore.save_local(FAISS_PATH)
    with open(FAISS_TIMESTAMP_FILE, 'w') as f:
        f.write(current_sources_mod_time.isoformat())
    print("Vectorstore FAISS creado y guardado correctamente.")

# ============================================================
# 6. FUNCIÓN RAG
# ============================================================

def busqueda_de_respuestas_RAG(pregunta: str) -> Dict:
    documentos_relacionados = retriever.invoke(pregunta)

    if not documentos_relacionados:
        return {
            "respuesta": "La respuesta a tu pregunta está fuera de los límites de mi documentación empresarial.",
            "citaciones": [],
            "documentos_encontrados": False,
            "motivo_no_respuesta": "NO_DOCUMENTS_FOUND"
        }

    answer = document_chain.invoke({
        "input": pregunta,
        "context": documentos_relacionados
    })

    # Detección robusta de fallo del LLM
    answer_clean = answer.strip().lower()
    if (
        "no poseo la información suficiente" in answer_clean
        or answer_clean in ["no lo sé", "no lo se", "no sé", "no se"]
    ):
        return {
            "respuesta": "No poseo la información suficiente en la documentación disponible para responder a tu pregunta.",
            "citaciones": [],
            "documentos_encontrados": False,
            "motivo_no_respuesta": "LLM_COULD_NOT_ANSWER"
        }

    return {
        "respuesta": answer,
        "citaciones": documentos_relacionados,
        "documentos_encontrados": True,
        "motivo_no_respuesta": None
    }


# ============================================================
# 7. NODOS DEL GRAFO
# ============================================================

def nodo_triaje(state: AgentState) -> AgentState:
    print("Ejecutando nodo de 'triaje'...")
    return {"triaje": triaje(state["pregunta"])}


def nodo_auto_resolver(state: AgentState) -> AgentState:
    print("Ejecutando nodo 'auto_resolver'...")
    respuesta_RAG = busqueda_de_respuestas_RAG(state["pregunta"])

    update = {
        "respuesta": respuesta_RAG["respuesta"],
        "citaciones": respuesta_RAG["citaciones"],
        "rag_exito": respuesta_RAG["documentos_encontrados"],
        "motivo_no_respuesta": respuesta_RAG.get("motivo_no_respuesta"),
        "accion_final": "AUTO_RESOLVER" if respuesta_RAG["documentos_encontrados"] else "FALLO_RAG"
    }
    return update


def nodo_pedir_info(state: AgentState) -> AgentState:
    print("Ejecutando nodo 'pedir_info'...")
    return {
        "respuesta": f"Necesito mayor información sobre tu solicitud: «{state['pregunta']}». ¿Puedes darme más detalles?",
        "citaciones": [],
        "accion_final": "PEDIR_INFO"
    }


def nodo_abrir_ticket(state: AgentState) -> AgentState:
    print("Ejecutando nodo 'abrir_ticket'...")
    tri = state["triaje"]
    return {
        "respuesta": f"Se ha abierto un ticket con urgencia {tri['urgencia']}. Pedido: {state['pregunta']}.",
        "citaciones": [],
        "accion_final": "ABRIR_TICKET"
    }


def nodo_out_of_scope(state: AgentState) -> AgentState:
    print("Ejecutando nodo 'out_of_scope'...")
    return {
        "respuesta": "La respuesta a tu pregunta está fuera de los límites de mi documentación empresarial. Te recomiendo consultar fuentes externas.",
        "citaciones": [],
        "accion_final": "OUT_OF_SCOPE"
    }


# ============================================================
# 8. ARISTAS DE DECISIÓN (LÓGICA CORREGIDA)
# ============================================================

def arista_decision_triaje(state: AgentState) -> str:
    print("Decidiendo el flujo después del nodo 'triaje'...")
    decision = state["triaje"]["decision"]

    if decision == "AUTO_RESOLVER":
        return "rag"
    elif decision == "PEDIR_INFO":
        return "info"
    elif decision == "ABRIR_TICKET":
        return "ticket"
    else:  # OUT_OF_SCOPE
        return "out_of_scope"


def arista_decision_rag(state: AgentState) -> str:
    """
    Lógica simplificada y robusta:
    - Si el RAG tuvo éxito → terminar
    - Si el RAG falló → out_of_scope (ya no dependemos de keywords frágiles)
    """
    print("Decidiendo el flujo después del nodo 'auto_resolver'...")

    if state.get("rag_exito"):
        print("RAG exitoso → finalizando.")
        return "ok"

    print(f"RAG falló. Motivo: {state.get('motivo_no_respuesta')}")
    # Cualquier fallo de RAG se considera fuera de alcance documental
    return "out_of_scope"


# ============================================================
# 9. CONSTRUCCIÓN DEL GRAFO
# ============================================================

from langgraph.graph import START, END, StateGraph

workflow = StateGraph(AgentState)

workflow.add_node("triaje", nodo_triaje)
workflow.add_node("auto_resolver", nodo_auto_resolver)
workflow.add_node("pedir_info", nodo_pedir_info)
workflow.add_node("abrir_ticket", nodo_abrir_ticket)
workflow.add_node("out_of_scope", nodo_out_of_scope)

workflow.add_edge(START, "triaje")

workflow.add_conditional_edges("triaje", arista_decision_triaje, {
    "rag": "auto_resolver",
    "info": "pedir_info",
    "ticket": "abrir_ticket",
    "out_of_scope": "out_of_scope"
})

workflow.add_conditional_edges("auto_resolver", arista_decision_rag, {
    "ok": END,
    "out_of_scope": "out_of_scope"
})

workflow.add_edge("pedir_info", END)
workflow.add_edge("abrir_ticket", END)
workflow.add_edge("out_of_scope", END)

grafo = workflow.compile()


# ============================================================
# 10. se procede a dar relebo a backend para pruebas de flujo
# ============================================================