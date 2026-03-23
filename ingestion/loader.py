from langchain_community.document_loaders import PyPDFDirectoryLoader

def load_documents(file_path):

    loader = PyPDFDirectoryLoader(file_path)

    docs = loader.load()

    return docs