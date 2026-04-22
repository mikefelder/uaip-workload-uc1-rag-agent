# Use Case 1 — RAG Knowledge Assistant

## What this is

A customised fork of the [Chat with your data Solution Accelerator](https://github.com/Azure-Samples/chat-with-your-data-solution-accelerator), adapted for Litware Energy's Unified AI Platform PoC.

The assistant answers natural language questions by pulling relevant content from internal knowledge sources — contracts, safety reports, operational documents — using retrieval-augmented generation. The emphasis isn't on the chat experience itself; it's on proving the observability, guardrails, and governance capabilities around it.

## Architecture

Python backend with a React/TypeScript frontend. Azure OpenAI handles inference, Azure AI Search handles document retrieval.

```
+------------------+
|  React Frontend  |
|  (TypeScript)    |
+--------+---------+
         |
+--------v---------+
|  Azure API Mgmt  |   AI Gateway: rate limiting, failover, token tracking
+--------+---------+
         |
+--------v------------------------------------------+
|         Python Backend (App Service)               |
|                                                    |
|  +-------------+  +------------------------+      |
|  | Orchestrator |  | Azure Content Safety   |      |
|  | (SK/LC/OAI)  |  | (guardrails)           |      |
|  +------+------+  +------------------------+      |
|         |                                          |
|  +------v------+  +------------------------+      |
|  | Azure OpenAI|  | Azure AI Search        |      |
|  | (LLM)       |  | (retriever)            |      |
|  +-------------+  +------------------------+      |
|                                                    |
|  OpenTelemetry SDK --> Azure Monitor / App Insights|
+----------------------------------------------------+
```

### Components

| Component | What it does |
|-----------|-------------|
| React Frontend | Chat UI with document upload, speech-to-text, and conversation history |
| Python Backend | RAG orchestration via Semantic Kernel, LangChain, or OpenAI Functions |
| Azure OpenAI | LLM inference (GPT-4.1) |
| Azure AI Search | Document indexing and retrieval |
| Azure Document Intelligence | PDF/document text extraction |
| Azure API Management | AI gateway — rate limiting, failover, token tracking |
| Azure Content Safety | Prompt injection detection and content filtering |
| PostgreSQL | Chat history and per-department access control |
| OpenTelemetry | Distributed tracing, exported to Azure Monitor |

## What we changed from the base accelerator

This fork adds the following, aligned to the PoC evaluation criteria:

1. **OpenTelemetry instrumentation** — distributed tracing across the full RAG pipeline:
   - `code/app.py` — configures Azure Monitor + optional OTLP exporter (dual-export to UC3 governance collector)
   - `code/backend/batch/utilities/orchestrator/orchestrator_base.py` — `rag.pipeline` root span wrapping the entire orchestration cycle
   - `code/backend/batch/utilities/tools/question_answer_tool.py` — `rag.retrieval` and `rag.generation` child spans with token/chunk attributes
   - `code/backend/batch/utilities/helpers/llm_helper.py` — `llm.chat`, `llm.completion`, `llm.embedding` spans with model/deployment attributes
   - Auto-instrumented HTTP calls via `opentelemetry-instrumentation-httpx`

2. **Azure API Management AI gateway** — 3-way routing in `llm_helper.py`:
   - **Gateway mode** (`AZURE_APIM_GATEWAY_URL` + `AZURE_APIM_SUBSCRIPTION_KEY` set) — all LLM calls route through APIM; APIM authenticates to AI Foundry via managed identity; UC1 authenticates to APIM with subscription key
   - **API key mode** — direct to Azure OpenAI with key-based auth (original behaviour)
   - **RBAC mode** — direct to Azure OpenAI with `DefaultAzureCredential` (managed identity)
   - Routing applies to all client creation paths: `get_llm()`, `get_streaming_llm()`, `get_chat_llm()`, `get_embedding_llm()`

3. Content Safety guardrails — prompt injection detection and content filtering via Azure Content Safety
4. LLM-as-Judge evaluation pipeline — automated scoring for correctness, relevance, and groundedness
5. Governance and access control — Entra ID auth with AI Search security filters for per-department data scoping
6. Cost management dashboards — token usage tracking, estimated spend, budget alerts

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite |
| Backend | Python 3.11+, Flask |
| Orchestration | Semantic Kernel / LangChain / OpenAI Functions |
| LLM | Azure OpenAI (GPT-4.1) |
| Search | Azure AI Search |
| Document processing | Azure Document Intelligence |
| Database | PostgreSQL (default) or Cosmos DB |
| Observability | OpenTelemetry, exported to Azure Monitor / Application Insights |
| AI gateway | Azure API Management |
| Infrastructure | Bicep, deployed via `azd` |

## Azure AI Landing Zone — additional resources required

The [AVM AI/ML Landing Zone](https://github.com/Azure/terraform-azurerm-avm-ptn-aiml-landing-zone) Terraform module provisions the platform layer but does **not** include the app-level compute needed to run this solution. The following resources must be added to the landing zone (via Terraform or manually) before deployment:

### What the landing zone provides

| Resource | Example name | Purpose |
|----------|-------------|---------|
| Container App Environment | `ai-alz-container-app-env-k76l` | Hosting platform for containerised apps |
| Container Registry (ACR) | `genaicrk76l` | Private Docker image registry |
| AI Services (OpenAI) | `ai-foundry-k76l` | GPT-4.1 and embedding model inference |
| AI Search | `ai-alz-ks-ai-search-k76l` | Document indexing and retrieval |
| Storage Account | `genaisak76l` | Blob storage for documents and queues |
| PostgreSQL Flexible Server | `ai-alz-pg-k76l` | Chat history and access control |
| Key Vault | `genai-kv-k76l` | Secrets management |
| Application Insights | `ai-alz-appinsights-k76l` | Telemetry and tracing |
| API Management | `ai-alz-apim-k76l` | AI gateway (rate limiting, token tracking) |
| AI Foundry Project | `ai-foundry-k76l/project-1` | Model management and evaluation |

### What must be added

Three Container Apps need to be created in the existing Container App Environment:

| Container App | Role | Ingress | Docker context |
|---------------|------|---------|----------------|
| `web` | Main frontend + API (Flask/uwsgi) | External (public) | `docker/Frontend.Dockerfile` |
| `adminweb` | Admin UI (Streamlit) | External or internal | `docker/Admin.Dockerfile` |
| `function` | Batch processor (Azure Functions) | Internal only | `docker/Backend.Dockerfile` |

Each Container App also requires:

- **ACR pull access** — system-assigned managed identity with `AcrPull` role on `genaicrk76l`
- **Managed identity RBAC** — each app's identity needs access to Key Vault, Storage, AI Services, and AI Search
- **Environment variables** — injected from the existing landing zone resources (OpenAI keys, Search endpoint, Storage connection strings, App Insights connection string, PostgreSQL host)

The Terraform outputs should expose:
- `SERVICE_WEB_RESOURCE_NAME` — name of the web Container App
- `SERVICE_ADMINWEB_RESOURCE_NAME` — name of the admin Container App
- `SERVICE_FUNCTION_RESOURCE_NAME` — name of the function Container App
- `AZURE_CONTAINER_REGISTRY_ENDPOINT` — ACR login server

These outputs are referenced by `azure.yaml` during `azd deploy`.

### Other landing zone issues encountered

| Issue | Resolution |
|-------|-----------|
| Key Vault secret creation returned 403 | Deploying identity needed Secret Get/Set/List in the vault's access policy (or `Key Vault Secrets Officer` role if using RBAC mode) |
| AzureBastionSubnet blocked by `RequestDisallowedByPolicy` | Azure Policy on the subscription denied Bastion subnet creation; required a policy exemption or disabling the jump VM module |
| `enable_rbac_authorization` deprecation warning | Renamed to `rbac_authorization_enabled` (required before azurerm v5.0) |
| `multiplier` attribute deprecated on private DNS zones | 83 instances; cosmetic warning, does not block deployment |

## Getting started

### Prerequisites

- Azure subscription with [Azure OpenAI access](https://learn.microsoft.com/en-us/azure/ai-services/openai/overview#how-do-i-get-access-to-azure-openai)
- Sufficient [Azure OpenAI quota](./docs/QuotaCheck.md) in your target region
- Python 3.11+
- Node.js 18+
- The AI Landing Zone deployed with the additional Container App resources (see above)

### Local development

Follow the [local development setup guide](./docs/LocalDevelopmentSetup.md) to run the app on your machine.

If you're not using devcontainers, see [NON_DEVCONTAINER_SETUP.md](./docs/NON_DEVCONTAINER_SETUP.md).

### Deploy to Azure

The solution deploys to Container Apps in the AI Landing Zone. The infrastructure (Container App Environment, ACR, and the three Container Apps) must already exist via Terraform.

1. Generate your `.env` from the deployed resources:
   ```bash
   ./scripts/generate_env.sh -g <RESOURCE_GROUP>
   ```

2. Build and push Docker images to ACR:
   ```bash
   az acr login --name genaicrk76l
   docker build -f docker/Frontend.Dockerfile -t genaicrk76l.azurecr.io/uc1-web:latest .
   docker build -f docker/Admin.Dockerfile -t genaicrk76l.azurecr.io/uc1-admin:latest .
   docker build -f docker/Backend.Dockerfile -t genaicrk76l.azurecr.io/uc1-function:latest .
   docker push genaicrk76l.azurecr.io/uc1-web:latest
   docker push genaicrk76l.azurecr.io/uc1-admin:latest
   docker push genaicrk76l.azurecr.io/uc1-function:latest
   ```

3. Update the Container Apps to use the pushed images (via `az containerapp update` or `azd deploy`).

See the [deployment guide](./docs/LOCAL_DEPLOYMENT.md) for more details including database selection (PostgreSQL or Cosmos DB).

#### Supported regions

- Australia East
- East US 2
- Japan East
- UK South

### AI Gateway environment variables

The following variables control APIM gateway routing. When both are set, all LLM calls
route through APIM instead of calling Azure OpenAI directly. See `.env.sample` for details.

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_APIM_GATEWAY_URL` | For gateway mode | APIM gateway base URL (e.g. `https://ai-alz-apim-fp3g.azure-api.net`) |
| `AZURE_APIM_SUBSCRIPTION_KEY` | For gateway mode | APIM subscription key (primary or secondary) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | OTLP gRPC endpoint for UC3 governance collector (e.g. `http://localhost:4317`) |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Yes (in Azure) | Azure Monitor connection string for traces |

### After deployment

1. [Set up authentication](./docs/azure_app_service_auth_setup.md).
2. Open the admin site to upload documents.
3. Start chatting via the web app URL.

Sample contract data is in the [data/](./data/) directory.

## Sample data

The `data/contract_data/` directory has sample documents for a contract review and summarisation scenario — showing how the RAG assistant can help people query a collection of contract documents.

For more details:
- [Contract Assistance](docs/contract_assistance.md)
- [Employee Assistance](docs/employee_assistance.md)

Some of the sample data was generated using AI and is for illustrative purposes only.

## Further reading

| Topic | Link |
|-------|------|
| Local Deployment | [LOCAL_DEPLOYMENT.md](docs/LOCAL_DEPLOYMENT.md) |
| PostgreSQL Setup | [postgreSQL.md](docs/postgreSQL.md) |
| Conversation Flow Options | [conversation_flow_options.md](docs/conversation_flow_options.md) |
| Supported File Types | [supported_file_types.md](docs/supported_file_types.md) |
| Speech-to-Text | [speech_to_text.md](docs/speech_to_text.md) |
| Teams Extension | [teams_extension.md](docs/teams_extension.md) |
| Troubleshooting | [TroubleShootingSteps.md](docs/TroubleShootingSteps.md) |
| Model Configuration | [model_configuration.md](docs/model_configuration.md) |
| Best Practices | [best_practices.md](docs/best_practices.md) |

## Licensing

This repository is licensed under the [MIT License](LICENSE.md).

The data set under `/data` is licensed under the [CDLA-Permissive-2 License](CDLA-Permissive-2.md).