"""
Etapas 4 y 5 del desafio: capa de recuperacion (RAG) + generacion/validacion de respuestas.

Recupera los chunks mas relevantes del PDF indexado y se los pasa a Gemini
para generar una respuesta que cita la fuente y evita alucinar cuando
no hay contexto suficiente.

Uso interactivo por terminal:
    python src/agente_rag.py
"""
import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from indexar_documentos import PERSIST_DIR, COLLECTION_NAME, build_vectorstore
from registro_ejecucion import registrar_interaccion

load_dotenv()

SYSTEM_PROMPT = """Eres el agente de soporte de NextSkill (Academia Online).
Responde UNICAMENTE con base en el CONTEXTO proporcionado, que proviene de
documentos internos oficiales (reglamento, reembolsos, FAQ, guia de uso, becas).

Reglas:
1. Si la respuesta esta en el contexto, respondela de forma clara y directa.
2. SIEMPRE indica de que seccion/documento sale la informacion (usa el metadato 'archivo_origen'
   y la seccion visible en el texto del contexto).
3. Si el contexto NO contiene informacion suficiente para responder, di explicitamente:
   "No encontre esta informacion en los documentos disponibles" y sugiere contactar
   a soporte@nextskill.academy. NUNCA inventes una respuesta.
4. Se conciso: respuestas de maximo 5-6 lineas salvo que la pregunta requiera mas detalle.

CONTEXTO:
{context}

PREGUNTA DEL USUARIO:
{question}
"""


def _formatear_contexto(documentos):
    partes = []
    for d in documentos:
        origen = d.metadata.get("archivo_origen", "documento")
        pagina = d.metadata.get("page", "?")
        partes.append(f"[Fuente: {origen}, pagina {pagina}]\n{d.page_content}")
    return "\n\n---\n\n".join(partes)


def get_rag_chain():
    # Si el indice vectorial no existe todavia (ej. primer arranque en la nube,
    # donde chroma_db/ no se sube a GitHub), lo construimos automaticamente.
    indice_existe = os.path.isdir(PERSIST_DIR) and len(os.listdir(PERSIST_DIR)) > 0
    if not indice_existe:
        print("Indice vectorial no encontrado. Construyendolo por primera vez...")
        build_vectorstore()

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR,
    )


def responder(pregunta: str):
    chain, retriever = get_rag_chain()
    inicio = time.time()
    documentos = retriever.invoke(pregunta)
    respuesta = chain.invoke(pregunta)
    duracion = round(time.time() - inicio, 2)

    fuentes = sorted({d.metadata.get("archivo_origen", "desconocido") for d in documentos})

    registrar_interaccion(
        pregunta=pregunta,
        contexto=[d.page_content[:200] for d in documentos],
        respuesta=respuesta,
        fuentes=fuentes,
        tiempo_respuesta_seg=duracion,
    )
    return respuesta, fuentes


if __name__ == "__main__":
    print("Agente NextSkill listo. Escribe 'salir' para terminar.\n")
    while True:
        pregunta = input("Tu pregunta: ").strip()
        if pregunta.lower() in {"salir", "exit", "quit"}:
            break
        respuesta, fuentes = responder(pregunta)
        print(f"\nRespuesta: {respuesta}")
        print(f"Fuentes: {', '.join(fuentes)}\n")
