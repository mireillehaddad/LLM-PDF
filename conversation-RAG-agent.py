import os
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

# =========================
# 1. Load PDFs
# =========================
def load_all_pdfs(folder_path: str):
    documents = []

    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(folder_path, file))
            documents.extend(loader.load())

    return documents


# =========================
# 2. Build RAG system
# =========================
def build_rag_system(documents):

    #  Chunking
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )
    chunks = splitter.split_documents(documents)

    print(f"Chunks created: {len(chunks)}")

    #  Embeddings + Vector DB
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    #  Retriever (more candidates for reranking)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

    #  LLM (low temperature)
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.05
    )

    # =========================
    # 3. BETTER PROMPT (ANTI-HALLUCINATION)
    # =========================
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
"""
    )

    # =========================
    # 4. MEMORY (CONVERSATIONAL)
    # =========================
    memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    input_key="question",
    output_key="answer"
)

    # =========================
    # 5. CONVERSATIONAL RAG CHAIN
    # =========================
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    return qa_chain


# =========================
# 6. OPTIONAL: SIMPLE RERANKING
# =========================
def rerank_documents(docs, query, embeddings):
    query_vec = embeddings.embed_query(query)

    scored = []
    for doc in docs:
        doc_vec = embeddings.embed_query(doc.page_content)
        score = sum(q * d for q, d in zip(query_vec, doc_vec))
        scored.append((score, doc))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [doc for _, doc in scored[:4]]  # keep top 4


# =========================
# 7. MAIN LOOP
# =========================
def main():
    docs = load_all_pdfs(PDF_FOLDER)
    qa_chain = build_rag_system(docs)

    print("\nConversational RAG system ready (type 'exit')\n")

    while True:
        query = input("Ask a question about your PDFs: ")

        if query.lower() == "exit":
            break

        result = qa_chain.invoke({"question": query})

        print("\nAgent:", result["answer"])

        
        print("\nSources:")
        seen = set()

        for i, doc in enumerate(result["source_documents"], start=1):
            source = os.path.basename(doc.metadata.get("source", "Unknown file"))
            page = doc.metadata.get("page_label", doc.metadata.get("page", "Unknown"))

            key = (source, page)
            if key not in seen:
                seen.add(key)
                print(f"{len(seen)}. File: {source} | Page: {page}")

                print("\n" + "-"*50)


if __name__ == "__main__":
    main()