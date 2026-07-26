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
# 2. PROMPTS
# ============================================================

PROMPT_TRIAJE = """
Eres el especialista de triaje del Banco Digital OpenMint.

Tu trabajo es clasificar la pregunta del usuario. Devuelve ÚNICAMENTE un JSON válido con esta estructura:

{
  "decision": "AUTO_RESOLVER" | "PEDIR_INFO" | "ABRIR_TICKET" | "OUT_OF_SCOPE",
  "urgencia": "BAJA" | "MEDIANA" | "ALTA",
  "campos_faltantes": []
}

### Reglas de decisión (sigue este orden de prioridad):

1. **AUTO_RESOLVER** (prioridad alta):
   - Preguntas sobre productos del banco (cuentas de ahorro, depósitos, créditos, staking, etc.)
   - Preguntas sobre montos mínimos, tasas de interés, comisiones, plazos, condiciones
   - Preguntas sobre privacidad de datos, seguridad, uso de información personal
   - Preguntas sobre políticas, reglamentos, términos y condiciones, contratos
   - Cualquier pregunta que pueda responderse con la documentación interna del banco

2. **PEDIR_INFO**:
   - Solo cuando la pregunta es extremadamente vaga (ej. "necesito ayuda", "tengo un problema")
   - O cuando falta un dato crítico e imprescindible para poder buscar en los documentos

3. **ABRIR_TICKET**:
   - El usuario pide explícitamente abrir un ticket, reporta un error técnico, o solicita una excepción/autorización especial

4. **OUT_OF_SCOPE**:
   - Preguntas que no tienen ninguna relación con el banco (clima, capitales de países, recetas, etc.)

### Importante:
- Si la pregunta menciona "cuenta de ahorro", "interés", "monto mínimo", "privacidad", "datos personales", "seguridad" → casi siempre es AUTO_RESOLVER.
- "campos_faltantes" solo úsalo cuando realmente sea PEDIR_INFO, y pon nombres cortos (ej. ["tipo de cuenta", "monto aproximado"]).

Responde SOLO con el JSON, sin texto adicional.
"""

PROMPT_RAG_SYSTEM = """
Eres el asistente oficial de políticas y productos del Banco Digital OpenMint.

Tu objetivo es responder de forma clara, útil y profesional basándote ÚNICAMENTE en el contexto proporcionado.

### Reglas de respuesta:

1. **Responde lo que sí está documentado**
   - Si la pregunta tiene varias partes, responde primero todas las que sí puedas contestar con el contexto.
   - Sé concreto y usa la información de los documentos.

2. **Sé honesto con lo que falta**
   - Si algún dato específico no aparece en el contexto (por ejemplo un monto mínimo exacto o una tasa precisa), dilo claramente.
   - Ejemplo de frase: "La documentación actual no especifica el monto mínimo exacto ni la tasa de interés vigente."

3. **Nunca inventes cifras, tasas ni condiciones**
   - No asumas montos, porcentajes ni plazos que no estén en el contexto.

4. **Sé orientativo y comercial (cuando sea natural)**
   - Si el usuario pregunta por ahorro, puedes mencionar las ventajas de los depósitos a plazo fijo (mejores tasas / APY preferencial) si el contexto lo permite.
   - Si pregunta por liquidez o necesidades de dinero, puedes orientar hacia las líneas de crédito disponibles (tradicional o con colateral cripto) cuando la documentación lo soporte.
   - No seas agresivo ni fuerces la venta. Solo orienta de forma útil.

5. **Estructura recomendada de respuesta** (cuando la pregunta es múltiple):
   - Primero responde lo que sí tienes.
   - Luego indica qué información no está disponible en la documentación actual.
   - Cierra con una orientación útil o invitación a contactar soporte / revisar el tarifario actualizado si hace falta.

6. **Tono**
   - Profesional, claro, cercano y confiable.
   - Habla en español natural.
   - No menciones que eres un modelo de lenguaje ni que usas RAG.

Responde siempre basándote en el contexto. Si el contexto está vacío o no es relevante, indica que no posees la información suficiente en la documentación disponible.
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

chain_de_triaje = llm.with_structured_output(
    TriajeOut,
    method="json_mode"
)


def triaje(mensaje: str) -> Dict:
    try:
        salida: TriajeOut = chain_de_triaje.invoke([
            SystemMessage(content=PROMPT_TRIAJE),
            HumanMessage(content=mensaje)
        ])
        return salida.model_dump()
    except Exception as e:
        print(f"[ERROR TRIAJE] {e}")
        # Fallback seguro: tratamos la pregunta como válida del banco
        return {
            "decision": "AUTO_RESOLVER",
            "urgencia": "BAJA",
            "campos_faltantes": []
        }


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
# 5. SPLITTING + EMBEDDINGS + FAISS
# ============================================================

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
chunks = splitter.split_documents(docs)

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
rebuild_faiss = False   # Cambia a False si quieres reutilizar el índice existente

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
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
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
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
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
            "respuesta": "No poseo la información suficiente en la documentación disponible para responder a tu pregunta.",
            "citaciones": [],
            "documentos_encontrados": False,
            "motivo_no_respuesta": "NO_DOCUMENTS_FOUND"
        }

    answer = document_chain.invoke({
        "input": pregunta,
        "context": documentos_relacionados
    })

    answer_clean = answer.strip().lower()

    # Solo consideramos fallo total si el modelo dice explícitamente que no tiene nada
    if (
        "no poseo la información suficiente" in answer_clean
        and "documentación actual no especifica" not in answer_clean
        and len(answer_clean) < 120
    ):
        return {
            "respuesta": answer,
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

    # Si venimos de un fallo parcial del RAG, preferimos devolver la respuesta parcial
    # en lugar de pedir más información genérica
    if state.get("respuesta") and state.get("accion_final") == "FALLO_RAG":
        return {
            "respuesta": state["respuesta"],
            "citaciones": state.get("citaciones", []),
            "accion_final": "AUTO_RESOLVER_PARCIAL"
        }

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
# 8. ARISTAS DE DECISIÓN
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
    else:
        return "out_of_scope"


def arista_decision_rag(state: AgentState) -> str:
    """
    Lógica menos agresiva:
    - Si el RAG tuvo éxito → ok
    - Si falló pero la pregunta parece del dominio del banco → info
      (el nodo pedir_info devolverá la respuesta parcial si existe)
    - Solo out_of_scope cuando claramente no tiene relación con OpenMint
    """
    print("Decidiendo el flujo después del nodo 'auto_resolver'...")

    if state.get("rag_exito"):
        print("RAG exitoso → finalizando.")
        return "ok"

    pregunta = state.get("pregunta", "").lower()

    KEYWORDS_DOMINIO = [
        "cuenta", "ahorro", "corriente", "depósito", "plazo fijo", "interés", "tasa",
        "crédito", "prestamo", "préstamo", "financiamiento", "colateral", "garantía",
        "staking", "rendimiento", "apy", "yield",
        "retiro", "transferencia", "comisión", "tarifa", "límite",
        "exchange", "cripto", "bitcoin", "ethereum", "stablecoin", "usdt", "usdc",
        "política", "privacidad", "datos personales", "seguridad", "fraude",
        "kyc", "aml", "lavado", "mora", "tolerancia", "ticket", "soporte",
        "congelamiento", "volatilidad", "custodia", "billetera",
        "reglamento", "términos", "condiciones", "contrato", "documento"
    ]

    es_dominio_banco = any(keyword in pregunta for keyword in KEYWORDS_DOMINIO)
    motivo = state.get("motivo_no_respuesta")

    if es_dominio_banco:
        print(f"RAG falló pero la pregunta es del dominio del banco. Motivo: {motivo} → info")
        return "info"

    if motivo in ["NO_DOCUMENTS_FOUND", "LLM_COULD_NOT_ANSWER"]:
        print("RAG falló y la pregunta no parece del dominio del banco → out_of_scope")
        return "out_of_scope"

    print("Caso no clasificado → info")
    return "info"


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
    "info": "pedir_info",
    "out_of_scope": "out_of_scope"
})

workflow.add_edge("pedir_info", END)
workflow.add_edge("abrir_ticket", END)
workflow.add_edge("out_of_scope", END)

grafo = workflow.compile()