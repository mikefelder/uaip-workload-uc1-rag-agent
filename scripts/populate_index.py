#!/usr/bin/env python3
"""Populate the AI Search index with mock Worley engineering documents.

Usage:
    export AZURE_AI_SEARCH_ENDPOINT=https://ai-alz-ks-ai-search-i40e.search.windows.net
    export AZURE_AI_SEARCH_INDEX=worley-engineering-docs
    python populate_index.py
"""

import json
import os

import httpx
from azure.identity import DefaultAzureCredential

SEARCH_ENDPOINT = os.environ.get("AZURE_AI_SEARCH_ENDPOINT", "https://ai-alz-ks-ai-search-i40e.search.windows.net")
INDEX_NAME = os.environ.get("AZURE_AI_SEARCH_INDEX", "worley-engineering-docs")
API_VERSION = "2024-07-01"

# Mock engineering documents for the PoC
DOCUMENTS = [
    {
        "id": "doc-001",
        "title": "Project Alpha — Valve Specification Matrix",
        "category": "EPC Specification",
        "source": "SP-MECH-VAL-001 Rev 3",
        "content": """Project Alpha Valve Specification Matrix — SP-MECH-VAL-001 Rev 3

1. SCOPE
This specification covers the minimum requirements for the selection, design, manufacturing, inspection, testing, and supply of all valves for Project Alpha, a greenfield LNG processing facility located in Western Australia.

2. APPLICABLE STANDARDS
- ASME B16.34: Valves — Flanged, Threaded, and Welding End
- API 6D: Pipeline and Piping Valves
- API 600: Steel Gate Valves
- API 602: Compact Steel Gate Valves
- API 598: Valve Inspection and Testing
- API 607: Fire Test for Quarter-Turn Valves
- ISO 10497: Testing of valves — Fire type-testing requirements
- NACE MR0175: Metallic Materials for Oilfield Equipment

3. MATERIAL REQUIREMENTS
3.1 Body and Bonnet: ASTM A352 LCC for cryogenic service, ASTM A216 WCB for standard service
3.2 Trim: Stellite 6 overlay on seating surfaces for gate and globe valves
3.3 Gaskets: Spiral wound with inner ring, graphite filler, 316SS winding
3.4 All wetted parts shall comply with NACE MR0175 for sour service applications

4. DESIGN REQUIREMENTS
4.1 Gate Valves: Full bore, outside screw and yoke (OS&Y), bolted bonnet
4.2 Globe Valves: Bolted bonnet, plug disc type
4.3 Ball Valves: Full bore, trunnion mounted for 6" and above, floating for below 6"
4.4 Check Valves: Dual plate wafer type for sizes 2" to 24", swing check for larger
4.5 Butterfly Valves: Double offset (high performance) for isolation service

5. TESTING REQUIREMENTS
5.1 All valves shall be hydrostatically tested per API 598
5.2 ESD valves shall be fire-tested per API 607 / ISO 10497
5.3 Cryogenic valves shall be tested per BS 6364 at -196°C
5.4 Fugitive emissions testing per ISO 15848-1 Class BH for all valves in VOC service

6. SIL REQUIREMENTS
6.1 All Emergency Shutdown (ESD) valves shall be SIL 2 rated per IEC 61508
6.2 Proof test intervals: maximum 12 months for SIL 2 valves
6.3 Partial stroke testing (PST) capability required for all ESD valves > 8"
""",
    },
    {
        "id": "doc-002",
        "title": "Project Alpha — Safety Compliance Report Q4 2025",
        "category": "Safety Report",
        "source": "SR-HSE-Q4-2025-001",
        "content": """Project Alpha — Quarterly Safety Compliance Report Q4 2025

1. EXECUTIVE SUMMARY
Project Alpha maintained a Total Recordable Incident Rate (TRIR) of 0.42 for Q4 2025, below the target of 0.50. Zero lost time injuries were recorded. One near-miss involving a pressure relief valve was investigated and closed.

2. REGULATORY COMPLIANCE STATUS
2.1 OSHA 1910.119 Process Safety Management: COMPLIANT
    - All P&IDs reviewed and updated per MOC-2025-087
    - PHA (Process Hazard Analysis) revalidation completed for Module 3
2.2 EPA Risk Management Plan: COMPLIANT
    - Worst-case release scenarios updated for new refrigerant inventory
2.3 State Environmental License: COMPLIANT — renewed through Dec 2026

3. SAFETY CRITICAL EQUIPMENT STATUS
3.1 Emergency Shutdown Valves (ESD)
    - 247 ESD valves in service, 100% proof tested in Q4
    - 3 valves failed partial stroke test — replaced within 72 hours
    - SIL verification completed per IEC 61511 for all new installations
3.2 Pressure Relief Valves (PRV)
    - 189 PRVs in service, all within calibration period
    - Near-miss NM-2025-142: PRV-3042 lifted prematurely during startup — root cause: incorrect set pressure. Corrective action: re-calibrated and procedure updated.
3.3 Fire & Gas Detection
    - All 1,247 detectors functional, quarterly bump-tested

4. COMPLIANCE AUDIT FINDINGS
4.1 Internal Audit IA-2025-Q4-003: Valve tagging inconsistency on Module 5 pipework
    - Finding: 12 valves missing permanent tags per SP-MECH-VAL-001
    - Corrective action: Tags installed, procedure reminder issued
    - Status: CLOSED

5. KEY METRICS
| Metric | Q4 Target | Q4 Actual | Status |
|--------|-----------|-----------|--------|
| TRIR | <0.50 | 0.42 | ✓ |
| ESD Proof Test | 100% | 100% | ✓ |
| MOC Closure Rate | >90% | 94% | ✓ |
| Training Compliance | >95% | 97% | ✓ |
""",
    },
    {
        "id": "doc-003",
        "title": "Worley Standard — Piping Material Specification",
        "category": "Engineering Standard",
        "source": "WS-PIP-MAT-002 Rev 7",
        "content": """Worley Standard — Piping Material Specification WS-PIP-MAT-002 Rev 7

1. PURPOSE
This standard defines the piping material classes for use on all Worley-managed EPC projects in the energy and resources sector. It ensures consistent material selection aligned with process conditions, corrosion allowances, and regulatory requirements.

2. MATERIAL CLASSES

Class A1 — Carbon Steel, Standard Service
- Material: ASTM A106 Gr.B (seamless pipe), ASTM A234 WPB (fittings)
- Temperature range: -29°C to +427°C
- Pressure rating: ANSI 150 to ANSI 600
- Application: General process, utility, and off-site piping
- Corrosion allowance: 3.0 mm

Class B2 — Low Temperature Carbon Steel
- Material: ASTM A333 Gr.6 (pipe), ASTM A420 WPL6 (fittings)
- Temperature range: -46°C to +343°C
- Application: Cryogenic and cold service piping (LNG, propane refrigerant)
- Impact testing: Charpy V-notch at -50°C, minimum 27J

Class C3 — Duplex Stainless Steel
- Material: ASTM A790 UNS S31803 (pipe), ASTM A182 F51 (fittings)
- Temperature range: -50°C to +315°C
- Application: Seawater cooling, high-chloride environments
- Pitting Resistance Equivalent (PREN) ≥ 34

Class D4 — Alloy 625 (Inconel)
- Material: ASTM B444 UNS N06625
- Temperature range: -196°C to +760°C
- Application: High-temperature, highly corrosive environments (acid gas, flue gas)

3. VALVE MATERIAL COMPATIBILITY
All valves shall use materials compatible with the piping class. Refer to SP-MECH-VAL-001 for specific valve material requirements. Mixed metallurgy at valve-pipe connections requires galvanic isolation per WS-COR-GAL-001.

4. WELDING REQUIREMENTS
4.1 All welding per ASME IX and project-specific WPS
4.2 PWHT required for carbon steel > 19mm wall thickness
4.3 PMI (Positive Material Identification) required for all alloy materials
""",
    },
    {
        "id": "doc-004",
        "title": "Project Alpha — Master Services Agreement",
        "category": "Contract",
        "source": "MSA-PA-2024-001",
        "content": """Project Alpha — Master Services Agreement MSA-PA-2024-001

PARTIES: Worley Limited (Contractor) and Alpha Energy Pty Ltd (Client)

1. SCOPE OF SERVICES
Worley shall provide Engineering, Procurement, and Construction Management (EPCm) services for the Project Alpha LNG Processing Facility, including:
- Front End Engineering Design (FEED)
- Detailed Engineering Design
- Procurement and Expediting
- Construction Management and Commissioning Support
- HSE Management throughout project lifecycle

2. CONTRACT VALUE AND PAYMENT
2.1 Estimated Total Value: AUD 2.4 billion
2.2 Payment basis: Reimbursable with target cost incentive
2.3 Target cost: AUD 2.1 billion (savings/overrun shared 50/50)
2.4 Fee: 12% of allowable costs
2.5 Performance bonus: Up to AUD 24M based on KPIs (safety, schedule, quality)

3. KEY PERFORMANCE INDICATORS
3.1 Safety: TRIR < 0.50, zero fatalities
3.2 Schedule: Mechanical completion within 36 months of FEED approval
3.3 Quality: < 2% rework rate on installed work
3.4 Local content: Minimum 60% Australian content by value

4. INTELLECTUAL PROPERTY
4.1 All project-specific deliverables are owned by the Client
4.2 Worley retains rights to its pre-existing IP and standard designs
4.3 Joint IP for any innovations developed during the project

5. LIABILITY AND INSURANCE
5.1 Worley's aggregate liability: 100% of fees earned
5.2 Professional indemnity: AUD 100M per occurrence
5.3 Public liability: AUD 250M per occurrence
""",
    },
    {
        "id": "doc-005",
        "title": "Project Alpha — Instrument Data Sheet: ESD Valve XV-3042",
        "category": "Instrument Data Sheet",
        "source": "DS-INS-XV3042 Rev 2",
        "content": """Instrument Data Sheet — Emergency Shutdown Valve XV-3042

TAG NUMBER: XV-3042
SERVICE: HP Separator Gas Outlet Isolation
P&ID REFERENCE: PID-PA-PR-003 Rev 8
LOCATION: Module 3, HP Separator Area

1. PROCESS DATA
- Fluid: Natural gas (sweet, dehydrated)
- Design pressure: 105 barg
- Operating pressure: 82 barg
- Design temperature: -29°C to +80°C
- Operating temperature: 35°C
- Line size: 12" / DN300
- Piping class: B2 (LTCS per WS-PIP-MAT-002)

2. VALVE SPECIFICATION
- Type: Ball valve, trunnion mounted, full bore
- Size: 12" / DN300, ANSI 600
- Body material: ASTM A352 LCC
- Ball material: ASTM A182 F316 + ENP coating
- Seat material: PEEK with Viton O-rings
- Fire safe: Certified per API 607 7th Ed.
- Fugitive emissions: ISO 15848-1 Class BH

3. ACTUATOR
- Type: Scotch-yoke, spring-return fail-close
- Supply pressure: 5.5 barg instrument air
- Stroke time: Open ≤ 5 seconds, Close ≤ 3 seconds (fail action)
- Solenoid: ASCO 327 series, ATEX Ex d IIC T6
- Position feedback: 4-20mA + HART, NAMUR proximity switches

4. SAFETY INTEGRITY
- SIL Rating: SIL 2 per IEC 61508
- Proof test interval: 12 months maximum
- Diagnostic coverage: 78% (with PST capability)
- Partial stroke test: Automated monthly, 10% travel
- Target PFDavg: ≤ 1.0 × 10⁻²

5. NOTES
- Valve replaced 2025-Q4 due to PST failure (ref: WO-2025-4891)
- Actuator spring set verified at 6.2 barg for fail-close
""",
    },
    {
        "id": "doc-006",
        "title": "Worley UAIP — AI Model Governance Policy",
        "category": "Governance Policy",
        "source": "POL-UAIP-GOV-001 Rev 1",
        "content": """Worley UAIP — AI Model Governance Policy POL-UAIP-GOV-001 Rev 1

1. PURPOSE
This policy establishes the governance framework for all AI models consumed through the Worley Unified AI Platform (UAIP), covering Azure OpenAI, AWS Bedrock, and OCI Generative AI.

2. MODEL APPROVAL PROCESS
2.1 All AI models must be registered in the UAIP Model Registry before use
2.2 New model requests require approval from:
    - Business unit AI Champion
    - Enterprise Architecture team
    - Information Security (for data classification review)
2.3 Approval SLA: 5 business days for standard models, 15 days for custom/fine-tuned

3. USAGE MONITORING
3.1 All model interactions are logged via the APIM AI Gateway
3.2 Token consumption tracked per business unit, project, and user
3.3 Monthly cost reports generated by the UC3 Governance Hub
3.4 Alerts triggered when spend exceeds 80% of allocated budget

4. CONTENT SAFETY
4.1 Azure Content Safety enabled for all Azure-hosted model interactions
4.2 Prompt injection detection via APIM policies
4.3 Output filtering for PII, safety-critical misinformation, and IP leakage
4.4 Human review required for any AI-generated content in safety-critical documents

5. DATA GOVERNANCE
5.1 No customer data processed through third-party models without classification review
5.2 All data in transit encrypted (TLS 1.3)
5.3 Data residency: Australian region (ap-southeast-2 for AWS, australiaeast for Azure)
5.4 Retention: Model interaction logs retained for 2 years per regulatory requirements

6. CROSS-CLOUD FEDERATION
6.1 All cross-cloud calls authenticated via OIDC federation (Entra ID ↔ AWS IAM)
6.2 No static credentials — managed identity or federated tokens only
6.3 Trace propagation: W3C traceparent headers mandatory on all cross-cloud calls
""",
    },
]


def create_index(endpoint: str, index_name: str, token: str) -> None:
    """Create the search index with semantic configuration."""
    url = f"{endpoint}/indexes/{index_name}?api-version={API_VERSION}"

    index_def = {
        "name": index_name,
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
            {"name": "title", "type": "Edm.String", "searchable": True, "filterable": True, "retrievable": True},
            {"name": "content", "type": "Edm.String", "searchable": True, "retrievable": True},
            {"name": "category", "type": "Edm.String", "searchable": True, "filterable": True, "facetable": True, "retrievable": True},
            {"name": "source", "type": "Edm.String", "searchable": True, "filterable": True, "retrievable": True},
        ],
        "semantic": {
            "configurations": [
                {
                    "name": "default",
                    "prioritizedFields": {
                        "titleField": {"fieldName": "title"},
                        "contentFields": [{"fieldName": "content"}],
                        "keywordsFields": [{"fieldName": "category"}, {"fieldName": "source"}],
                    },
                }
            ]
        },
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.put(url, json=index_def, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        if resp.status_code in (200, 201):
            print(f"✓ Index '{index_name}' created/updated")
        else:
            print(f"✗ Index creation failed ({resp.status_code}): {resp.text[:200]}")
            resp.raise_for_status()


def upload_documents(endpoint: str, index_name: str, token: str, docs: list) -> None:
    """Upload documents to the search index."""
    url = f"{endpoint}/indexes/{index_name}/docs/index?api-version={API_VERSION}"

    batch = {"value": [{"@search.action": "mergeOrUpload", **doc} for doc in docs]}

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=batch, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        if resp.status_code in (200, 207):
            results = resp.json().get("value", [])
            success = sum(1 for r in results if r.get("status"))
            print(f"✓ Uploaded {success}/{len(docs)} documents")
        else:
            print(f"✗ Upload failed ({resp.status_code}): {resp.text[:200]}")
            resp.raise_for_status()


def main():
    credential = DefaultAzureCredential()
    token = credential.get_token("https://search.azure.com/.default").token

    print(f"Using search endpoint: {SEARCH_ENDPOINT}")
    print(f"Index name: {INDEX_NAME}")
    print(f"Documents to upload: {len(DOCUMENTS)}")
    print()

    create_index(SEARCH_ENDPOINT, INDEX_NAME, token)
    upload_documents(SEARCH_ENDPOINT, INDEX_NAME, token, DOCUMENTS)

    print()
    print("Done! The index is ready for the UC1 RAG agent.")


if __name__ == "__main__":
    main()
