# Copyright (c) Worley. All rights reserved.
# UAIP UC1 — RAG Knowledge Agent (Microsoft Agent Framework SDK)

"""Entry point for the UC1 RAG Knowledge Agent.

Uses Azure AI Search as a native tool for retrieval-augmented generation
over Worley's engineering document corpus. Serves the OpenAI Responses API.
"""

import logging
import os

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from dotenv import load_dotenv

from tools.search import search_engineering_docs
from tools.document_qa import answer_from_document

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("uaip.rag-agent")

RAG_AGENT_INSTRUCTIONS = """You are Worley's Knowledge Assistant for the Unified AI Platform (UAIP).

You help engineers, project managers, and compliance teams find and understand
information from Worley's internal engineering document corpus.

## Your Capabilities

You have access to these tools:
- **search_engineering_docs** — Search the engineering knowledge base for EPC
  documents, valve specifications, safety reports, contracts, and project data.
  Returns the most relevant document excerpts with citations.
- **answer_from_document** — Answer a specific question using context from a
  retrieved document. Use this for follow-up questions about a specific document.

## Guidelines

1. **Always search first**: Use `search_engineering_docs` before answering any
   question about Worley projects, engineering specs, or compliance.
2. **Cite sources**: Always reference the document name and section when
   providing information from the knowledge base.
3. **Be precise**: Engineers need exact specifications, standards references,
   and actionable data — not general advice.
4. **Acknowledge limitations**: If the knowledge base doesn't contain relevant
   information, say so clearly rather than guessing.
5. **Safety first**: Flag any safety-critical information with appropriate
   warnings and reference the relevant standards.
"""


def _get_credential():
    """Return ManagedIdentityCredential in production, DefaultAzureCredential locally."""
    client_id = os.environ.get("AZURE_CLIENT_ID", "")
    if client_id:
        return ManagedIdentityCredential(client_id=client_id)
    return DefaultAzureCredential()


def main():
    credential = _get_credential()

    client = OpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        model=os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1"),
        credential=credential,
    )

    agent = Agent(
        client=client,
        instructions=RAG_AGENT_INSTRUCTIONS,
        tools=[
            search_engineering_docs,
            answer_from_document,
        ],
        default_options={"store": False},
    )

    logger.info("Starting UAIP RAG Knowledge Agent on port 8088")
    server = ResponsesHostServer(agent)
    server.run()


if __name__ == "__main__":
    main()
