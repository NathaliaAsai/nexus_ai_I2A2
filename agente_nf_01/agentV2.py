# utf-8 
# pip install google-generativeai
# pip install streamlit
# pip install pypdf2
# pip install langchain
# pip install -U langchain-community

# o streamlit deve ser executado pelo terminal com o comando:
# streamlit run agentV2.py

import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from config_template import Config

config = Config()
genai.configure(api_key=config.GOOGLE_API_KEY) 

def get_text_from_text(uploaded_files):
    text=""
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name.lower()
        content = uploaded_file.read()

        if file_name.endswith('.pdf'):
            pdf_reader = PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        elif file_name.endswith('.xml'):
            try:
                from xml.etree import ElementTree as ET
                root = ET.fromstring(content)
                text += ET.tostring(root, encoding='unicode')
            except ET.ParseError as e:
                text += f"Erro ao ler XML: {e}\n"

        elif file_name.endswith('.csv'):
            import pandas as pd
            try:
                df = pd.read_csv(uploaded_file)
                text += df.to_string(index=False)
            except Exception as e:
                text += f"Erro ao ler CSV: {e}\n"

        else:
            text += f"Arquivo não suportado: {file_name}\n"
    return  text


def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks


def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(
        model = "models/embedding-001",
        google_api_key=config.GOOGLE_API_KEY)
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")


def get_conversational_chain():

    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model=config.LLM_MODEL,
                             temperature=0.3)

    prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain


def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    
    new_db = FAISS.load_local("faiss_index", embeddings,allow_dangerous_deserialization=True) #Apenas porque sabemos a origem do arquivo! Tomar cuidado com arquivos maliciosos
    docs = new_db.similarity_search(user_question)

    chain = get_conversational_chain()

    
    response = chain(
        {"input_documents":docs, "question": user_question}
        , return_only_outputs=True)

    print(response)
    st.write("Reply: ", response["output_text"])


def main():
    st.set_page_config("Chat PDF")
    st.header("Converse com seus arquivos de Notas Fiscais usando o Gemini💁")

    user_question = st.text_input("Faça perguntas sobre os arquivos carregados:")

    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader(
            "Faça upload de arquivos pdf, xml ou csv", 
            type=["pdf", "xml", "csv"],
            accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_text_from_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Done")



if __name__ == "__main__":
    main()