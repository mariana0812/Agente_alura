"""
Etapas 2 y 3 del desafio: extraccion/procesamiento de contenido + indexacion vectorial.

Lee el PDF de data/, lo divide en chunks y genera embeddings con Gemini,
guardando el indice vectorial en ./chroma_db (persistente, no hay que
recrearlo cada vez que arranca la app).

Uso:
    python src/indexar_documentos.py
"""
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

PDF_PATH = "data/Documentacion_Academia_Online.pdf"
PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "nextskill_docs"


def build_vectorstore():
    if not os.environ.get("GOOGLE_API_KEY"):
        raise RuntimeError("Falta GOOGLE_API_KEY. Copia .env.example a .env y completa tu key.")

    print(f"Cargando PDF desde {PDF_PATH} ...")
    loader = PyPDFLoader(PDF_PATH)
    paginas = loader.load()
    print(f"  -> {len(paginas)} paginas cargadas")

    # Chunking por tamaño fijo con overlap (etapa 2 del material)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(paginas)

    # Metadatos adicionales (etapa 2: atribucion de metadatos)
    for chunk in chunks:
        chunk.metadata["categoria"] = "Plataforma Educativa"
        chunk.metadata["archivo_origen"] = "Documentacion_Academia_Online.pdf"

    print(f"  -> {len(chunks)} chunks generados")

    print("Generando embeddings e indexando en Chroma ...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR,
    )
    print(f"Indice vectorial guardado en ./{PERSIST_DIR}")
    return vectorstore


if __name__ == "__main__":
    build_vectorstore()
