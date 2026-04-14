import os
from functools import lru_cache
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate

load_dotenv()

PDF_FOLDER = "data/pdfs"

app = FastAPI(title="PDF Conversational RAG API")


class QuestionRequest(BaseModel):
    question: str


def load_all_pdfs(folder_path: str):
    documents = []

    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    for file in os.listdir(folder_path):
        if file.lower().endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(folder_path, file))
            documents.extend(loader.load())

    if not documents:
        raise ValueError(f"No PDF files found in {folder_path}")

    return documents


def build_rag_system(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.05,
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a highly accurate assistant.

Rules:
- Answer ONLY using the provided context.
- If the answer is not in the context, say: "I don't know".
- Be concise and precise.
- Do not invent information.

Context:
{context}

Question:
{question}

Answer:
""",
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="question",
        output_key="answer",
    )

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
    )

    return qa_chain


@lru_cache(maxsize=1)
def get_qa_chain():
    docs = load_all_pdfs(PDF_FOLDER)
    return build_rag_system(docs)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        qa_chain = get_qa_chain()
        result = qa_chain.invoke({"question": request.question})

        sources = []
        seen = set()

        for doc in result["source_documents"]:
            source = os.path.basename(doc.metadata.get("source", "Unknown file"))
            page = doc.metadata.get("page_label", doc.metadata.get("page", "Unknown"))
            key = (source, page)
            if key not in seen:
                seen.add(key)
                sources.append({"file": source, "page": page})

        return {
            "answer": result["answer"].strip(),
            "sources": sources,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))