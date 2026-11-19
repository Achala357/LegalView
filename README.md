

\# LegalView



\### AI-Powered Legal Contract Analysis and Auditing System



LegalView is a full-stack legal technology project designed to assist with contract analysis, clause extraction, risk assessment, evidence-grounded question answering, and tamper-evident audit logging.



The system integrates Natural Language Processing (NLP), Retrieval-Augmented Generation (RAG), and blockchain-based Merkle-root anchoring.



\## Key Features



\### 1. Contract Analysis

\- Upload and manage legal documents.

\- Extract relevant contractual clauses.

\- Identify contract types and analyze clause-level information.

\- Generate structured analysis results.



\### 2. Risk Assessment

\- Machine-learning-based clause risk classification.

\- Clause-level and document-level risk assessment.

\- Explainability information supporting risk findings.



\### 3. Dual Retrieval-Augmented Generation

\- FAISS-based retrieval of relevant contract evidence.

\- Separate retrieval of legal case-law evidence.

\- Structured context from contract analysis results.

\- OpenAI-powered question answering.

\- Upload-specific retrieval to reduce cross-document information leakage.



\### 4. Blockchain Audit System

\- Hash-linked audit records.

\- Merkle-root generation and anchoring using Solidity.

\- Retrieval and verification of audit records.

\- Merkle inclusion proofs for anchored records.

\- Owner-restricted anchoring and permanent freezing.



\## Technology Stack



| Layer | Technologies |

|---|---|

| Frontend | React, Vite, Tailwind CSS |

| Backend | Python, FastAPI, Pydantic |

| NLP | Hugging Face Transformers, PyTorch |

| Retrieval | FAISS, Sentence Transformers |

| LLM | OpenAI API |

| Database | SQLite, SQLAlchemy |

| Blockchain | Solidity, Hardhat, ethers.js |

| Testing | Hardhat, Chai |



\## System Architecture



The React frontend communicates with the FastAPI backend.



The backend coordinates:

\- Document processing and contract analysis

\- Clause extraction and risk assessment

\- Contract-specific and case-law retrieval

\- OpenAI-based answer generation

\- Audit logging and integrity verification



The blockchain component provides smart-contract functionality for anchoring Merkle roots associated with audit records.



The system stores document information and audit data off-chain rather than recording complete legal documents directly on the blockchain.



\## Repository Structure



```text

LegalView/

├── frontend/

│   ├── src/

│   ├── package.json

│   └── vite.config.mjs

├── backend/

│   ├── audit/

│   ├── routers/

│   ├── services/

│   │   └── rag/

│   ├── main.py

│   ├── requirements.txt

│   └── .env.example

├── blockchain/

│   ├── contracts/

│   │   └── AuditAnchor.sol

│   ├── scripts/

│   ├── test/

│   └── hardhat.config.ts

└── README.md

```



\## Local Setup



\### Frontend



From the `frontend` directory:



```bash

npm ci

npm run dev

```



For a production build:



```bash

npm run build

```



\### Backend



Use a compatible Python environment, with Python 3.10 used during local verification.



From the `backend` directory, create and activate a virtual environment:



```bash

python -m venv venv

```



Windows activation:



```cmd

venv\\Scripts\\activate

```



Install dependencies after installing a compatible PyTorch build for your CPU or CUDA environment:



```bash

pip install -r requirements.txt

```



See the official PyTorch installation instructions for platform-specific installation.



Copy `.env.example` to `.env` and configure the necessary environment variables.



Start FastAPI:



```bash

python -m uvicorn main:app --reload

```



API documentation is available at:



`http://127.0.0.1:8000/docs`



\### Required Model Artifacts



The application relies on local trained models and FAISS indexes that are excluded from Git because of their size and data-management requirements.



The following paths are expected relative to `backend/`:



```text

models/

├── span\_extractor/

├── legalbert\_risk\_classifier/

└── rag/

&#x20;   ├── contract/

&#x20;   │   ├── contracts\_15k\_merged.faiss.index

&#x20;   │   └── contracts\_15k\_merged.metadata.jsonl

&#x20;   └── case\_law/

&#x20;       ├── case\_law.faiss.index

&#x20;       └── case\_law.metadata.jsonl

```



The retrieval pipeline also uses the embedding model `intfloat/e5-base-v2`.



The backend requires these artifacts at startup. The complete NLP application cannot be run using repository source files alone.



\### Environment Variables



See `backend/.env.example`.



\- `OPENAI\_API\_KEY`: Required for LLM-generated answers.

\- `UPLOAD\_EMBED\_MODEL`: Embedding model for uploaded contracts.

\- `UPLOAD\_FAISS\_DIR`: Local directory for generated upload indexes.



Do not commit actual credentials or local document data.



\### Blockchain



From the `blockchain` directory:



```bash

npm ci

npx hardhat compile

npx hardhat test

```



The Solidity contract `AuditAnchor.sol` supports owner-controlled Merkle-root anchoring, anchor retrieval, and irreversible freezing.



Blockchain deployment and anchoring scripts are provided under `blockchain/scripts/`.



\## API Overview



\### Document Management

\- `POST /api/upload`

\- `GET /api/uploads`

\- `GET /api/file/{filename}`

\- `DELETE /api/uploads/{filename}`



\### Contract Analysis and Q\&A

\- `POST /api/contracts/analyze`

\- `GET /api/qa/health`

\- `POST /api/qa/ask`



\### Audit and Integrity Verification

\- `POST /api/audit/log`

\- `GET /api/audit/verify`

\- `GET /api/audit/chain`

\- `GET /api/audit/anchors`

\- `GET /api/audit/proof/{block\_index}`

\- `GET /api/audit/verify-inclusion/{block\_index}`



Full endpoint specifications are available through FastAPI's interactive documentation.



\## Verification



The following checks have been completed locally:



\- React/Vite production build: successful.

\- Frontend production dependency audit: zero reported vulnerabilities.

\- Python backend syntax check: passed.

\- FastAPI startup with configured local model artifacts: successful.

\- Dual RAG health endpoint: returned `dual\_rag\_ready: true`.

\- Hardhat Solidity compilation: successful.

\- AuditAnchor smart-contract tests: 9 passed.

\- Existing Hardhat starter tests: 9 passed.

\- Blockchain production dependency audit: zero reported vulnerabilities.



These checks do not constitute full end-to-end validation of contract analysis, LLM question answering, or blockchain deployment.



Additional development-tool dependency advisories remain in the Hardhat toolchain.



\## Security and Limitations



\- API credentials are excluded from version control.

\- Local databases, uploaded documents, and generated FAISS indexes are excluded.

\- Trained model weights are not included.

\- OpenAI-based functionality requires an independently configured API key.

\- The blockchain component requires appropriate network configuration for deployment.

\- The application is an academic software project and is not a substitute for professional legal advice.



\## Project Context



LegalView was developed as a final-year Computer Science project, exploring the integration of NLP, intelligent information retrieval, explainable risk assessment, and tamper-evident audit mechanisms for legal contract management.
