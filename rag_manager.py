# rag_manager.py
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


class RAGManager:
    def __init__(self, model_name="moka-ai/m3e-base"):
        """
        初始化RAG管理器。
        - model_name: 选择一个合适的嵌入模型。m3e-base 是一个优秀的中英文模型。
        """
        print("正在加载嵌入模型，请稍候...")
        self.embedding_model = SentenceTransformer(model_name)
        print("嵌入模型加载完毕。")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50
        )
        self.index = None
        self.doc_chunks = []

    def load_and_index_documents(self, file_paths: list[str]) -> str:
        """
        加载文档，将其分割成块，并创建向量索引。
        """
        print(f"开始加载 {len(file_paths)} 个文档...")
        all_docs = []
        for path in file_paths:
            try:
                if path.lower().endswith(".pdf"):
                    loader = PyPDFLoader(path)
                    all_docs.extend(loader.load())
                elif path.lower().endswith(".txt"):
                    loader = TextLoader(path, encoding="utf-8")
                    all_docs.extend(loader.load())
                else:
                    print(f"不支持的文件类型: {path}")
            except Exception as e:
                print(f"加载文件失败 {path}: {e}")

        if not all_docs:
            return "未能加载任何文档。"

        print("文档加载完毕，开始切分文本...")
        self.doc_chunks = self.text_splitter.split_documents(all_docs)

        if not self.doc_chunks:
            return "文档内容为空或切分失败。"

        print(f"文本切分完毕，共 {len(self.doc_chunks)} 个区块。开始生成向量...")
        # 从 Document 对象中提取文本内容
        chunk_texts = [chunk.page_content for chunk in self.doc_chunks]
        embeddings = self.embedding_model.encode(chunk_texts, show_progress_bar=True)

        print("向量生成完毕，开始构建FAISS索引...")
        embedding_dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.index.add(np.array(embeddings, dtype=np.float32))

        status_message = f"RAG准备就绪：已索引 {len(self.doc_chunks)} 个区块。"
        print(status_message)
        return status_message

    def is_ready(self) -> bool:
        """检查RAG索引是否已构建"""
        return self.index is not None

    def retrieve_and_augment_prompt(self, query: str, k: int = 3) -> str:
        """
        接收用户问题，检索相关文档块，并构建增强后的提示词。
        """
        if not self.is_ready():
            return query  # 如果RAG未就绪，返回原始问题

        print(f"正在为问题进行RAG检索: '{query[:30]}...'")
        query_embedding = self.embedding_model.encode([query])

        # 在FAISS中搜索最相似的k个向量
        distances, indices = self.index.search(
            np.array(query_embedding, dtype=np.float32), k
        )

        # 获取相关文档块的文本
        retrieved_chunks = [self.doc_chunks[i].page_content for i in indices[0]]

        # 构建上下文
        context = "\n\n---\n\n".join(retrieved_chunks)

        # 构建增强后的提示词 (Prompt)
        augmented_prompt = (
            f"请根据以下提供的上下文信息来回答问题。\n\n"
            f"--- 上下文 ---\n"
            f"{context}\n"
            f"--- 上下文结束 ---\n\n"
            f"问题: {query}"
        )

        print("提示词已增强。")
        return augmented_prompt
