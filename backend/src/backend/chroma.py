import os
import uuid
from typing import List, Dict, Any
from backend.document_parser import parse_pdf
import chromadb
from openai import AsyncOpenAI
from backend.models import File


FILE_COLLECTION_NAME = "files"


async def get_chromadb_client():
    client = chromadb.HttpClient(host="chroma", port=8000)
    return client


async def add_file_to_chromadb(file: File, file_path: str):
    """
    Add a file to ChromaDB for vector search

    Args:
        file: The File object from the database
        file_path: Path to the file on disk
    """
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    chroma_client = await get_chromadb_client()
    collection = chroma_client.get_or_create_collection(FILE_COLLECTION_NAME)

    # Read the file content
    with open(file_path, "rb") as f:
        file_content = f.read()

    # Parse the document
    parsed = None
    if file.content_type == "application/pdf":
        parsed = await parse_pdf(
            file_content
        )  # HOMEWORK: Try and compare page-level chunks vs. block-level chunks
    else:
        # For non-PDF files, we can add support later
        return

    # Process in batches for better performance
    batch_size = 100
    batched_ids = []
    batched_embeddings = []
    batched_documents = []
    batched_metadata = []

    for i, chunk in enumerate(parsed.chunks):
        # Get embedding from OpenAI
        embedding_response = await openai_client.embeddings.create(
            input=chunk.embed,  # HOMEWORK: Try and compare using chunk.embed vs. chunk.content
            model="text-embedding-3-small",
        )
        embedding_vector = embedding_response.data[0].embedding

        # Create metadata
        metadata = {
            "file_id": str(file.id),
            "file_name": file.name,
            "page_number": chunk.metadata.get("page_num", 0),
            "user_id": str(file.user_id),
        }

        batched_ids.append(f"{file.id}_{i}")
        batched_embeddings.append(embedding_vector)
        batched_documents.append(chunk.content)
        batched_metadata.append(metadata)

        # Add in batches
        if len(batched_ids) >= batch_size or i == len(parsed.chunks) - 1:
            collection.add(
                ids=batched_ids,
                embeddings=batched_embeddings,
                documents=batched_documents,
                metadatas=batched_metadata,
            )
            # Clear batches
            batched_ids = []
            batched_embeddings = []
            batched_documents = []
            batched_metadata = []


async def delete_file_from_chromadb(file_id: uuid.UUID):
    chroma_client = await get_chromadb_client()
    collection = chroma_client.get_or_create_collection(FILE_COLLECTION_NAME)
    collection.delete(where={"file_id": str(file_id)})


async def search_vector_db(
    query: str, top_k: int = 5, user_id: uuid.UUID = None
) -> List[Dict[str, Any]]:
    """
    Search the vector database for relevant chunks

    Args:
        query: The search query
        top_k: Number of results to return
        user_id: If provided, only search files belonging to this user

    Returns:
        List of relevant chunks with metadata
    """
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    chroma_client = await get_chromadb_client()
    collection = chroma_client.get_or_create_collection(FILE_COLLECTION_NAME)

    # HOMEWORK: Try query enrichment techniques

    # Get embedding for the query
    embedding_response = await openai_client.embeddings.create(
        input=query, model="text-embedding-3-small"
    )
    query_embedding = embedding_response.data[0].embedding

    # Search the collection
    where_clause = {"user_id": str(user_id)} if user_id else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_clause,
    )

    # Format the results
    formatted_results = []
    if results and results.get("documents"):
        for i, doc in enumerate(results["documents"][0]):
            formatted_results.append(
                {
                    "content": doc,
                    "metadata": (
                        results["metadatas"][0][i] if results.get("metadatas") else {}
                    ),
                    "distance": (
                        results["distances"][0][i] if results.get("distances") else None
                    ),
                }
            )

    return formatted_results
