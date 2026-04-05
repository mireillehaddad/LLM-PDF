import os
os.environ.pop("SSLKEYLOGFILE", None)

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA

load_dotenv()

PDF_FOLDER = "data/pdfs"

def load_all_pdfs(folder_path: str):
    documents = []

    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    pdf_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        raise ValueError(f"No PDF files found in {folder_path}")

    for pdf_file in pdf_files:
        loader = PyPDFLoader(pdf_file)
        documents.extend(loader.load())

    return documents

def build_qa_chain(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = text_splitter.split_documents(documents)
    print(f"Loaded {len(documents)} pages")
    print(f"Created {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    return qa_chain

def main():
    print("Loading PDF files...")
    documents = load_all_pdfs(PDF_FOLDER)

    print("Building QA system...")
    qa_chain = build_qa_chain(documents)

    print("\nPDF Question Answering system is ready.")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Ask a question about your PDFs: ")

        if query.lower() == "exit":
            print("Goodbye.")
            break

        result = qa_chain.invoke({"query": query})

        print("\nAnswer:")
        print(result["result"])

        print("\nSources:")
        for i, doc in enumerate(result["source_documents"], start=1):
            source = doc.metadata.get("source", "Unknown source")
            page = doc.metadata.get("page", "Unknown page")
            print(f"{i}. File: {source}, Page: {page}")

        print("\n" + "-" * 60 + "\n")

if __name__ == "__main__":
    main()