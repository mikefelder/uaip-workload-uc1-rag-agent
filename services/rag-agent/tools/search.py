# Copyright (c) Worley. All rights reserved.
"""AI Search tool — hybrid vector+semantic search over engineering documents."""

import json
import os

import httpx
from agent_framework import tool
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from pydantic import Field
from typing_extensions import Annotated


def _get_search_token() -> str:
    """Get a bearer token for Azure AI Search using managed identity."""
    client_id = os.environ.get("AZURE_CLIENT_ID", "")
    credential = ManagedIdentityCredential(client_id=client_id) if client_id else DefaultAzureCredential()
    token = credential.get_token("https://search.azure.com/.default")
    return token.token


@tool(approval_mode="never_require")
def search_engineering_docs(
    query: Annotated[str, Field(description="Search query for Worley engineering documents (EPC specs, valve data, safety reports, contracts).")],
    top: Annotated[int, Field(description="Number of results to return (1-10).", ge=1, le=10)] = 5,
) -> str:
    """Search Worley's engineering knowledge base using hybrid vector + semantic search.

    Searches across EPC documents, valve specifications, safety compliance
    reports, contracts, and project documentation. Returns the most relevant
    excerpts with document citations.
    """
    search_endpoint = os.environ.get("AZURE_AI_SEARCH_ENDPOINT", "")
    index_name = os.environ.get("AZURE_AI_SEARCH_INDEX", "worley-engineering-docs")

    if not search_endpoint:
        return "AI Search not configured (AZURE_AI_SEARCH_ENDPOINT not set)."

    try:
        token = _get_search_token()

        # Use the REST API for hybrid search
        url = f"{search_endpoint}/indexes/{index_name}/docs/search?api-version=2024-07-01"

        body = {
            "search": query,
            "queryType": "semantic",
            "semanticConfiguration": "default",
            "top": top,
            "select": "title,content,source,category",
            "captions": "extractive",
            "answers": "extractive|count-3",
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                json=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("value", [])
        if not results:
            return f"No documents found matching: '{query}'"

        # Format results with citations
        formatted = []
        for i, doc in enumerate(results, 1):
            title = doc.get("title", "Untitled")
            source = doc.get("source", "Unknown")
            category = doc.get("category", "General")
            content = doc.get("content", "")[:500]  # Truncate for readability

            # Extract captions if available
            captions = doc.get("@search.captions", [])
            caption_text = captions[0].get("text", "") if captions else ""

            formatted.append(
                f"**[{i}] {title}**\n"
                f"Source: {source} | Category: {category}\n"
                f"{caption_text or content}\n"
            )

        # Include semantic answers if available
        answers = data.get("@search.answers", [])
        answer_text = ""
        if answers:
            answer_text = "\n**Direct Answer:** " + answers[0].get("text", "") + "\n\n"

        return answer_text + "\n---\n".join(formatted)

    except httpx.HTTPStatusError as e:
        return f"Search failed (HTTP {e.response.status_code}): {e.response.text[:200]}"
    except Exception as e:
        return f"Search unavailable: {e}"
