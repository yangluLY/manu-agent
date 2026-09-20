from sentence_transformers import SentenceTransformer

DEFAULT_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DIM = 512

# BGE 中文检索模型推荐给查询文本增加的检索指令
QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


class Embedder:
    """
    RAG Embedding 模型封装。

    负责：
    1. 将知识库 Chunk 转换为向量
    2. 将用户查询转换为向量

    当前使用：
    BAAI/bge-small-zh-v1.5
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: str | None = None,
    ):
        self.model_name = model_name

        self.model = SentenceTransformer(
            model_name,
            device=device,
        )

        dimension = self.model.get_sentence_embedding_dimension()

        if dimension != EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: "
                f"expected {EMBEDDING_DIM}, got {dimension}"
            )

    def embed_documents(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> list[list[float]]:
        """
        将知识库文档文本批量转换成 Embedding。

        文档本身不添加 query instruction。
        """

        if not texts:
            return []

        cleaned_texts = [
            self._validate_text(text)
            for text in texts
        ]

        embeddings = self.model.encode(
            cleaned_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return [
            embedding.tolist()
            for embedding in embeddings
        ]

    def embed_query(
        self,
        query: str,
    ) -> list[float]:
        """
        将用户查询转换为 Embedding。

        BGE 检索时给 query 添加检索 instruction。
        """

        query = self._validate_text(query)

        query_with_instruction = (
            f"{QUERY_INSTRUCTION}{query}"
        )

        embedding = self.model.encode(
            query_with_instruction,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return embedding.tolist()

    @staticmethod
    def _validate_text(text: str) -> str:
        """
        对输入文本进行最基本校验。
        """

        if not isinstance(text, str):
            raise TypeError("text must be a string")

        text = text.strip()

        if not text:
            raise ValueError("text cannot be empty")

        return text