# Use Case 1 — RAG Knowledge Agent

## What this is

A retrieval-augmented generation (RAG) agent built on the **Microsoft Agent Framework SDK** that answers natural language questions using Worley's internal engineering document corpus. It searches Azure AI Search for relevant documents and generates contextual, cited responses using Azure OpenAI (gpt-4.1).

The agent serves the **OpenAI Responses API** protocol and is deployed as a Container App behind Azure API Management. It integrates with the UC2 Supervisor Agent as the `search_knowledge` tool.

## Architecture

```
APIM (/uc1/responses)
  │
  ▼
Container App (Agent Framework SDK — ResponsesHostServer on port 8088)
  │
  ├── OpenAIChatClient → Azure OpenAI (gpt-4.1)
  │
  └── FunctionTools:
        ├── search_engineering_docs  → Azure AI Search (hybrid semantic search)
        │     └── Index: worley-engineering-docs
        │          ├── EPC valve specifications
        │          ├── Safety compliance reports
        │          ├── Piping material standards
        │          ├── Instrument data sheets
        │          ├── Contract documents
        │          └── AI governance policies
        │
        └── answer_from_document    → Follow-up QA on specific documents
```

### Azure Services

| Service | Purpose |
|---------|---------|
| Azure Container Apps | Hosts the RAG agent |
| Azure OpenAI (gpt-4.1) | LLM for response generation |
| Azure AI Search | Document indexing and hybrid semantic search |
| Azure API Management | AI Gateway — routing, rate limiting, trace injection |
| Azure Application Insights | Observability and OTEL telemetry |

## API

```
POST /responses    — OpenAI Responses API (query the knowledge base)
GET  /readiness    — Health check
```

### Example Request

```json
{
  "input": "What are the valve specifications for Project Alpha?"
}
```

### Example Response

The agent searches the engineering knowledge base, retrieves relevant documents (valve specification matrix, instrument data sheets), and generates a cited response with ASME/API/IEC standards references.

## Knowledge Base

The AI Search index `worley-engineering-docs` contains mock engineering documents for the PoC:

| Document | Category | Source |
|----------|----------|--------|
| Project Alpha — Valve Specification Matrix | EPC Specification | SP-MECH-VAL-001 Rev 3 |
| Project Alpha — Safety Compliance Report Q4 2025 | Safety Report | SR-HSE-Q4-2025-001 |
| Worley Standard — Piping Material Specification | Engineering Standard | WS-PIP-MAT-002 Rev 7 |
| Project Alpha — Master Services Agreement | Contract | MSA-PA-2024-001 |
| Instrument Data Sheet: ESD Valve XV-3042 | Instrument Data Sheet | DS-INS-XV3042 Rev 2 |
| Worley UAIP — AI Model Governance Policy | Governance Policy | POL-UAIP-GOV-001 Rev 1 |

Documents are populated via `scripts/populate_index.py`.

## Project Structure

```
services/rag-agent/
  main.py              # Agent Framework entrypoint (ResponsesHostServer)
  agent.yaml           # Foundry deployment descriptor
  Dockerfile           # Container image (port 8088)
  requirements.txt     # Dependencies
  tools/
    search.py          # AI Search hybrid semantic search tool
    document_qa.py     # Document-specific follow-up QA tool

infra/                 # Terraform deployment
  main.container_app.tf   # Container App (port 8088, /readiness probes)
  main.apim.tf            # APIM routes (/responses, /readiness)
  main.identity.tf        # UAMI + RBAC (OpenAI User, AcrPull, Search Reader)
  main.monitor.tf         # Application Insights
  data.tf                 # Data sources for ALZ resources
  terraform.tfvars.msdn   # MSDN PoC values

scripts/
  populate_index.py    # Create AI Search index and upload mock documents
```

## Deployment

```bash
# Populate AI Search index (requires public access or VPN)
python3 scripts/populate_index.py

# Build image
az acr build --registry genaicri40e --image uc1-rag-agent:latest \
  --file services/rag-agent/Dockerfile services/rag-agent \
  --platform linux/amd64

# Deploy infrastructure
cd infra
terraform init
terraform plan -var-file=terraform.tfvars.msdn -out=tfplan
terraform apply tfplan
```

## Integration with UC2 Supervisor

The UC2 Supervisor Agent invokes UC1 via the `search_knowledge` FunctionTool, which calls `POST /uc1/responses` through APIM. This enables the supervisor to incorporate knowledge retrieval into multi-agent workflows.

## Reference Architecture Alignment

| Pattern | Implementation |
|---------|---------------|
| RAG Pipeline | Azure AI Search (hybrid semantic) + Azure OpenAI generation |
| Knowledge Layer | Document index with EPC specs, safety reports, contracts |
| Agent Protocol | OpenAI Responses API via Agent Framework SDK |
| Observability | OTEL traces via Agent Framework + App Insights |
| Security | Managed identity for Search + OpenAI, no API keys in code |
