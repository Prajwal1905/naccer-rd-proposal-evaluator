import json
import logging
import os
import re

import chromadb
from chromadb.utils import embedding_functions

from app.config import get_settings

logger = logging.getLogger(__name__)

PAST_PROPOSALS_COLLECTION = "past_proposals"
GUIDELINES_COLLECTION = "st_guidelines"
PRIORITY_AREAS_COLLECTION = "priority_areas"

# Sections of a past proposal we embed individually for section-level novelty matching
PROPOSAL_SECTION_FIELDS = ["abstract", "objectives", "methodology"]


def get_chroma_client():
    settings = get_settings()
    os.makedirs(settings.chroma_dir, exist_ok=True)
    return chromadb.PersistentClient(path=settings.chroma_dir)


def get_embedding_function():
    settings = get_settings()
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.embedding_model
    )


def _get_or_create_collection(client, name: str):
    ef = get_embedding_function()
    return client.get_or_create_collection(name=name, embedding_function=ef)


def chunk_markdown(text: str, max_chars: int = 1000) -> list[str]:
    
    sections = re.split(r"\n(?=#{2,3}\s)", text)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= max_chars:
            chunks.append(section)
        else:
            paragraphs = section.split("\n\n")
            current = ""
            for para in paragraphs:
                if len(current) + len(para) + 2 <= max_chars:
                    current = f"{current}\n\n{para}" if current else para
                else:
                    if current:
                        chunks.append(current)
                    current = para
            if current:
                chunks.append(current)
    return chunks


def build_past_proposals_collection(client) -> int:
    
    settings = get_settings()
    path = os.path.join(settings.reference_proposals_dir, "past_proposals.json")
    with open(path, "r", encoding="utf-8") as f:
        proposals = json.load(f)

    collection = _get_or_create_collection(client, PAST_PROPOSALS_COLLECTION)
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

    documents, metadatas, ids = [], [], []
    for proposal in proposals:
        for field in PROPOSAL_SECTION_FIELDS:
            text = proposal.get(field, "")
            if not text.strip():
                continue
            doc_id = f"{proposal['id']}::{field}"
            documents.append(text)
            metadatas.append({
                "proposal_id": proposal["id"],
                "title": proposal["title"],
                "research_area": proposal["research_area"],
                "year": proposal["year"],
                "institution": proposal["institution"],
                "section": field,
                "approved": proposal["approved"],
            })
            ids.append(doc_id)

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    logger.info("Indexed %d section embeddings from %d past proposals.", len(ids), len(proposals))
    return len(ids)


def build_guidelines_collection(client) -> int:
    settings = get_settings()
    path = os.path.join(settings.guidelines_dir, "st_funding_guidelines.md")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    collection = _get_or_create_collection(client, GUIDELINES_COLLECTION)
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

    chunks = chunk_markdown(text)
    documents, metadatas, ids = [], [], []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        heading_match = re.match(r"#{2,3}\s+(.*)", chunk)
        heading = heading_match.group(1).strip() if heading_match else f"Chunk {i}"
        metadatas.append({"source": "st_funding_guidelines", "heading": heading, "chunk_index": i})
        ids.append(f"guideline::{i}")

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    logger.info("Indexed %d chunks from S&T guidelines.", len(ids))
    return len(ids)


def build_priority_areas_collection(client) -> int:
    settings = get_settings()
    path = os.path.join(settings.priority_areas_dir, "cil_moc_priority_areas.md")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    collection = _get_or_create_collection(client, PRIORITY_AREAS_COLLECTION)
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

    chunks = chunk_markdown(text)
    documents, metadatas, ids = [], [], []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        heading_match = re.match(r"#{2,3}\s+(.*)", chunk)
        heading = heading_match.group(1).strip() if heading_match else f"Chunk {i}"
        metadatas.append({"source": "cil_moc_priority_areas", "heading": heading, "chunk_index": i})
        ids.append(f"priority::{i}")

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    logger.info("Indexed %d chunks from CIL/MoC priority areas.", len(ids))
    return len(ids)


def build_all_collections():
    logging.basicConfig(level=logging.INFO)
    client = get_chroma_client()
    n1 = build_past_proposals_collection(client)
    n2 = build_guidelines_collection(client)
    n3 = build_priority_areas_collection(client)
    print(f"Done. past_proposals={n1} chunks, st_guidelines={n2} chunks, priority_areas={n3} chunks")


if __name__ == "__main__":
    build_all_collections()