"""
Example of using pgvector with py-pglite for a simple RAG application.

This test demonstrates how to:
1. Enable the `pgvector` extension.
2. Create a table for storing text chunks and their embeddings.
3. Insert documents and their vector embeddings.
4. Perform a similarity search to find the most relevant document chunk.
5. Use the retrieved chunk to answer a question.
"""

from typing import TYPE_CHECKING

import psycopg
import pytest

from py_pglite import PGliteManager
from py_pglite.config import PGliteConfig

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray
    from pgvector.psycopg import register_vector

# Try to import optional dependencies, or skip tests
try:
    import numpy as np
    from pgvector.psycopg import register_vector
except ImportError:
    np = None
    register_vector = None


@pytest.mark.skipif(
    not np or not register_vector, reason="numpy or pgvector not available"
)
def test_pgvector_rag_example():
    """Demonstrates a simple RAG workflow using pgvector."""
    # --- 1. Setup: Documents and a mock embedding function ---

    documents = {
        "doc1": "The sky is blue.",
        "doc2": "The sun is bright.",
        "doc3": "The cat walks on the street.",
    }

    # A mock function to simulate generating embeddings (e.g., from an API)
    def get_embedding(text: str) -> "NDArray":
        assert np is not None
        # In a real app, this would be a call to an embedding model
        if "sky" in text:
            return np.array([0.1, 0.9, 0.1])
        if "sun" in text:
            return np.array([0.8, 0.2, 0.1])
        if "cat" in text:
            return np.array([0.1, 0.1, 0.8])
        return np.array([0.0, 0.0, 0.0])

    # --- 2. Database Setup: Enable pgvector and create schema ---

    config = PGliteConfig(extensions=["pgvector"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            assert register_vector is not None
            register_vector(conn)

            conn.execute(
                """
                CREATE TABLE documents (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding vector(3)
                )
                """
            )

            # --- 3. Ingestion: Store documents and embeddings ---

            for content in documents.values():
                embedding = get_embedding(content)
                conn.execute(
                    "INSERT INTO documents (content, embedding) VALUES (%s, %s)",
                    (content, embedding),
                )

            # --- 4. RAG Workflow: Ask a question and retrieve context ---

            question = "What color is the sky?"
            question_embedding = get_embedding(question)

            # Find the most similar document chunk
            result = conn.execute(
                "SELECT content FROM documents ORDER BY embedding <-> %s LIMIT 1",
                (question_embedding,),
            ).fetchone()

            assert result is not None
            retrieved_context = result[0]

            # --- 5. Generation: Use the context to answer the question ---

            # A mock generation step
            def generate_answer(context: str, question: str) -> str:
                if "sky" in question and "blue" in context:
                    return "Based on the context, the sky is blue."
                return "I cannot answer the question based on the provided context."

            answer = generate_answer(retrieved_context, question)

            # --- 6. Verification ---

            print(f"\nQuestion: {question}")
            print(f"Retrieved Context: '{retrieved_context}'")
            print(f"Answer: {answer}")

            assert "The sky is blue" in retrieved_context
            assert "the sky is blue" in answer.lower()
