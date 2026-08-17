# SyncSphere: Enterprise AI Workflow Orchestration Platform
## VIVA Preparation Guide - Sections 1 to 4

### SECTION 1: PROJECT OVERVIEW

**What SyncSphere is:**
SyncSphere is an Enterprise AI Workflow Orchestration Platform. It acts as an intelligent middleware, enabling businesses to define, execute, and monitor multi-agent autonomous workflows. It inherently understands context through RAG, interacts dynamically with external services using the Model Context Protocol (MCP), and orchestrates tasks using a DAG (Directed Acyclic Graph) based Workflow Engine built on FastAPI.

**Why it was built:**
It was built to bridge the gap between unstructured LLM outputs and deterministic enterprise execution. Standard LLMs lack execution capabilities and direct access to enterprise data. SyncSphere gives AI "hands" (MCP connectors) and "memory" (RAG) within a governed, observable, and approval-gated framework.

**Enterprise problem it solves:**
Relying on ad-hoc API integrations for every new SaaS tool is an unscalable, O(N) complexity problem. SyncSphere solves this via MCP, unifying integrations into a standard protocol allowing AI models to dynamically discover tools. It solves the problem of "AI unreliability" by enforcing Human-in-the-Loop (HITL) approvals for destructive actions and maintaining a strict audit trail (Observability).

**Target users:**
- **AI Engineers & Developers:** Building and extending workflows and custom MCP tools.
- **Operations Managers:** Approving and monitoring workflow executions.
- **System Administrators:** Managing RBAC, security credentials, and tracing telemetry.

**Complete workflow:**
1. A user inputs a prompt (e.g., "Summarize recent Jira tickets and Slack the team").
2. The AI Planner analyzes the prompt against available MCP Connector Tools.
3. The Planner generates a Structured Plan.
4. The Workflow Compiler translates this plan into a DAG (Nodes = Tools/Logic, Edges = Data passing).
5. The Workflow Engine executes the DAG. If an approval node is hit, execution pauses for Human Approval.

**Complete execution lifecycle:**
Prompt Received → Embeddings Gen & RAG Fetch Context → AI Planner invoked via OpenRouter → JSON DAG Plan Generated → Workflow Engine Queues Root Nodes (Redis/Async tasks) → Connectors executed via MCP protocol → Results merged in context → Dependent nodes triggered → Final state saved to MongoDB → Dashboard Updated via SSE/React Query.

**End-to-end data flow:**
Client (Next.js) `POST /v1/planner/generate` 
→ FastAPI `v1_router` 
→ `PlanningService` 
→ `KnowledgeService` (Fetches Vector Context) 
→ `OpenRouterAdapter` (Generates JSON DAG) 
→ `WorkflowCompiler` (Transforms JSON to Executable Nodes) 
→ `ExecutionEngine` (Executes Nodes) 
→ `ConnectorRegistry` (Invokes external API) 
→ `MongoDB` (Saves state) 
→ Client (Polls/SSE for execution status).

**Module interaction:**
- `planner` consumes `knowledge` and `connectors`.
- `workflow` engine orchestrates `connectors`.
- `approval` interrupts `workflow`.
- `observability` passively records `workflow` and `planner`.

**Folder structure:**
- `backend/src/syncsphere/`: `ai`, `approval`, `connectors`, `core`, `identity`, `knowledge`, `observability`, `planner`, `runtime`, `workflow`.
- `frontend/app/`: `(dashboard)` containing pages.
- `frontend/features/`: domain specific components (`workflow`, `observability`, `tasks`).
- `frontend/shared/`: generic UI components (shadcn).

**High-level architecture:**
Decoupled Layered Architecture. Frontend (Next.js) ↔ REST API (FastAPI) ↔ Core Domain logic (Workflow/Planner) ↔ Infrastructure (MongoDB/Redis).

---

### SECTION 2: FRONTEND

**Why React?** Component-based architecture allows for reusable building blocks (e.g., nodes in workflow builder). Virtual DOM ensures performant updates for highly interactive graphing.
**Why Next.js?** App Router provides file-based routing, server components for heavy lifting, and automatic code splitting.
**Why TypeScript?** Strict typing eliminates entire classes of runtime errors, critical when passing complex DAG configurations between frontend and backend.
**Why Tailwind CSS?** Utility-first CSS prevents style bleed, enforces design system consistency, and allows ultra-fast development of custom UI components.
**Why React Query?** Server state management. Handles caching, background fetching, stale-time, pagination, and optimistic updates for execution logs automatically.
**Why Zustand?** Client global state. Used for highly active, non-persisted state like `workflowBuilderStore` (dragging nodes, zooming pane) where React Query isn't applicable.
**Why React Flow?** Industry standard library for building node-based graphical interfaces. Handles rendering DAGs, edge routing, and viewport transformations flawlessly.
**Why shadcn/ui?** Accessible, unstyled components that copy into our source. Full control over the DOM without dependency lock-in.


**How routing works:** Next.js App Router (`app/`). Folders define routes. `app/(dashboard)/workflow-builder/page.tsx` maps to `/workflow-builder`.
**How layouts work:** `layout.tsx` wraps pages. We use it to persist the Sidebar and Navbar across all dashboard routes without re-rendering them.
**How pages work:** `page.tsx` fetches initial data and renders feature components.
**How global state works:** Zustand stores define actions and state (e.g., `useWorkflowStore(state => state.nodes)`). Re-renders only components subscribing to that specific slice.
**How React Query fetches data:** `useQuery({ queryKey: ['executions'], queryFn: fetchExecutions })`.
**How optimistic updates work:** Before calling the API, `queryClient.setQueryData` mutates the cache to reflect the expected success, rolling back if the mutation fails.
**How React communicates with FastAPI:** Axios client with a global interceptor that injects Bearer JWTs and handles 401 refresh token logic.

**Explain every frontend page individually:**
- **Dashboard:** High-level metrics, recent executions, system health.
- **Workflow Builder:** The React Flow canvas. Drag-and-drop nodes, configure edges, save as JSON.
- **Tasks:** Input for natural language prompts triggering the AI Planner.
- **Executions:** Detailed list of past runs, showing successes, failures, and execution graphs.
- **Connectors:** OAuth and API key management for integrations (Slack, Gmail, etc).
- **Knowledge Base:** Upload documents, trigger embedding generation, view chunks.
- **Observability:** Telemetry, OpenRouter token usage, latency graphs, API metrics.
- **Authentication:** Login/registration via JWT.
- **Settings:** Profile management, API keys, organization details.

**Explain rendering lifecycle:** SSR (Server-Side Rendering) for initial HTML payload (Next.js server components) -> Hydration -> React Query fetches fresh client data -> React Flow calculates node positions in `useEffect`.

---

### SECTION 3: BACKEND

**Explain backend architecture in extreme detail.**
SyncSphere uses a Domain-Driven Design (DDD) inspired modular monolith architecture.
**Why Python?** De facto ecosystem for AI, ML, and Data Engineering. Essential for LangChain, OpenAI/OpenRouter SDKs, and data processing.
**Why FastAPI?** Built on ASGI (Starlette) and Pydantic. Provides native async support and auto-generates OpenAPI documentation. Extremely fast.
**Why async/await?** Workflow orchestration involves massive I/O bound operations (API calls, DB reads). Async prevents thread blocking, allowing a single worker to handle thousands of concurrent nodes.
**Why Pydantic?** Data validation at the boundary. Ensures JSON from frontend strictly matches expected schema before processing.
**Why modular architecture?** Separation of concerns. The `planner` shouldn't care how `approval` stores its data.

**Explain every folder:**
- `routers`: FastAPI endpoints grouping (e.g., `v1_planner.py`). Define request/response boundaries.
- `services`: Core business logic (e.g., `PlanningService`).
- `schemas`: Pydantic models for API validation.
- `models`: (Domain) Core objects, independent of DB.
- `connectors`: MCP client implementations, OAuth flows.
- `planner`: AI prompt decomposition, validation, LLM interfacing.
- `workflow`: Task queuing, DAG execution algorithms (Topological sort).
- `middleware`: Intercepts HTTP requests (Correlation ID, Logging, Tenant parsing).
- `core`: Config loading, exception handlers, DI container.
- `database`: MongoDB/Beanie initialization.

**Request lifecycle:** Client Request -> Middleware (Correlation ID/Log) -> Endpoint (Router) -> Pydantic Validation -> Service Layer (Business Logic) -> Infrastructure Layer (MongoDB/OpenRouter via Connectors) -> Response.
**Dependency Injection:** Passed via FastAPI `Depends`, reducing tight coupling (e.g., `def create_workflow(db: Database = Depends(get_db))`).
**Execution pipeline:** Workflow DAG is topologically sorted. Nodes with 0 in-degree are executed asynchronously. Output is explicitly passed iteratively to downstream nodes.
**Background tasks:** Used for non-blocking operations like writing trace logs or updating metrics to Observability without delaying the API response.

---

### SECTION 4: DATABASE

**Explain MongoDB in complete detail.**
**Why MongoDB?** Workflows and LLM outputs are inherently unstructured, highly variable JSON documents. Relational DB schemas are too rigid for arbitrary JSON outputs from diverse MCP tools.
**Why NoSQL?** High read/write throughput for execution logs, flexible schema for workflow DAGs.
**Why Beanie ODM?** Built natively on Motor (async MongoDB driver). Allows us to use Pydantic to define MongoDB documents seamlessly linking API schemas and DB schemas.

**Collections used:**
- `Users`: Auth, roles.
- `Workflows`: Saves the DAG (nodes, edges, config).
- `WorkflowExecutionLogDocument`: Traces each run's states.
- `ConnectorConfigurations`: Encrypted OAuth tokens and credentials.
- `PromptExecutionDocument`: Detailed tracking of OpenRouter API calls, prompt tokens, completion tokens, latency, cost.
- `KnowledgeDocumentDocument`: RAG source files metadata.
- `KnowledgeChunkDocument`: The vectorized chunks of text.

**CRUD operations:** Performed asynchronously via Beanie (e.g., `await WorkflowDocument.insert_one(doc)`).
**Indexes:** Critical for Observability metrics. Indexes placed on `tenant_id`, `execution_status`, `created_at` for Fast queries. Vector Indexes built for similarity search.
**Relationships:** Managed via `Link[]` in Beanie or ID referencing (embedding where appropriate, like putting node configurations inside the Workflow Document to avoid joins).
**How FastAPI connects to MongoDB:** Lifespan event in `main.py` calls `init_beanie`, passing the Motor AsyncIOMotorClient and the list of Document models.


# SyncSphere: Enterprise AI Workflow Orchestration Platform
## VIVA Preparation Guide - Sections 5 to 7

### SECTION 5: RAG (Retrieval Augmented Generation)

**Explain exactly how RAG is used.**
SyncSphere uses RAG to provide the AI Planner with specific organizational context that a base LLM wouldn't know. Before the OpenRouter LLM plans a workflow, the system searches the Knowledge Base for relevant SOPs, documentation, or historical execution graphs.

**Knowledge ingestion:** A user uploads a document (PDF, Text) to the frontend. Fastapi receives it and extracts raw text.
**Document chunking:** The text is split into smaller, semantically meaningful pieces (e.g., 500-token chunks with 50-token overlap) using a library like LangChain's RecursiveCharacterTextSplitter.
**Embedding generation:** Each chunk runs through an embedding model (e.g., `text-embedding-3-small` or local HuggingFace equivalent) converting text into dense fixed-size vectors (e.g., 1536 dimensions).
**Vector database:** Embeddings and chunk metadata are saved. SyncSphere uses MongoDB Atlas Vector Search natively (within `KnowledgeChunkDocument`) ensuring no extra infrastructure like Pinecone is needed.
**Metadata:** Chunks store `document_id`, `org_id`, and tags to allow pre-filtering before cosine similarity is calculated, improving accuracy and security.
**Similarity search:** When a user prompts the planner, the prompt itself is converted to an embedding. We query MongoDB Vector Search for the top K closest chunk vectors.
**Context retrieval & Prompt augmentation:** The raw text of the top K chunks is injected into the system prompt: `[EXTERNAL CONTEXT: <chunk text>]`.
**Hallucination reduction:** By forcing the LLM to rely on injected context over paramaterized weights, it prevents the AI from guessing how organizational processes should work.

### SECTION 6: EMBEDDINGS

**What embeddings are:** High-dimensional mathematical vector representations of semantic meaning. Words or sentences with similar meanings get mapped close together in this multi-dimensional space.
**How generated:** We pass text through a transformer model trained specifically to output vectors representing semantic clustering (e.g. BERT variants).
**How vectors are stored:** Stored in MongoDB as numerical arrays (e.g., `[0.012, -0.443, ...]`).
**Cosine similarity:** A mathematical equation measuring the angle between two vectors. An angle of 0 (cosine=1) implies exact semantic match. SyncSphere uses this to rank context chunks.
**Semantic search:** Unlike keyword search (which only matches exact words), semantic search finds meaning. e.g., A prompt asking "How do I fix the server" will match a document discussing "resolving backend outages".

### SECTION 7: MCP (Model Context Protocol)

**Explain Model Context Protocol in complete detail.**
**Why MCP exists:** It is an open standard designed to replace fragmented, vendor-specific API integrations for AI models. Without MCP, you write custom tool logic for OpenAI, anthropic, and Llama individually. MCP standardizes the protocol.
**Difference between MCP and REST APIs:** REST requires hardcoded endpoints and explicit client logic. MCP enables dynamic capability discovery—the AI queries the server to learn what tools it possesses at runtime.
**Difference between MCP and SDKs:** SDKs are language-specific. MCP uses language-agnostic JSON-RPC over standard transports.
**Difference between MCP and plugins:** Plugins are highly coupled. MCP servers run independently (often locally or containerized sidecars) maximizing security isolation.

**MCP Client:** In SyncSphere, the `ConnectorRegistry` acts as the MCP client, interrogating external MCP servers or local modules.
**MCP Server:** Abstracted modules exposing tools.
**MCP Resources:** Read-only data exposed (e.g., "Slack Channel History").
**MCP Tools:** Executable functions the AI can call (e.g., "Send Slack Message", "Update Jira Ticket"). The server returns an JSON Schema of the arguments required.
**Tool discovery:** SyncSphere sends a `tools/list` JSON-RPC request to the connected MCP server exposing all functions safely.

**Transport protocols:**
- **stdio:** Local execution where STDIN/STDOUT are piped. Secure, isolated.
- **SSE (Server-Sent Events):** Remote execution over HTTP allowing streaming updates.
- **HTTP:** Standard request/responses.

**How SyncSphere uses MCP:** SyncSphere is a Meta-MCP orchestrator. It registers various SaaS tools (Gmail, Github) as MCP Tool interfaces. The AI Planner queries the registry, discovers tools, and builds a DAG relying strictly on MCP standardized schemas. Instead of calling Gmail API directly, it generates an MCP Tool invocation.
**Why MCP is future-proof:** When a new LLM provider emerges, or a new SaaS tool comes out, SyncSphere requires exactly zero core architecture changes to integrate them, saving hundreds of engineering hours.


# SyncSphere: Enterprise AI Workflow Orchestration Platform
## VIVA Preparation Guide - Sections 8 to 11

### SECTION 8: OPENROUTER

**Why OpenRouter:** It dynamically routes requests across numerous AI models (OpenAI, Anthropic, Meta Llama) using a single, unified API. We avoid vendor lock-in and can use cheaper/faster models depending on task complexity.
**How OpenRouter works:** We send an OpenAI-format completion request with a `model` string (e.g. `anthropic/claude-3-opus`). OpenRouter proxies the payload securely to the target vendor.
**Request format:** Standard OpenAI format: `{"model": "...", "messages": [{"role": "user", "content": "..."}]}`.
**Response format:** Standard JSON with `choices` array, `message`, and token usage statistics.
**Model routing & Fallback:** If a model provider goes down (e.g., Anthropic API outage), OpenRouter auto-routes to a fallback model if we specify routing preferences.
**Token counting & Cost optimization:** Tokens (sub-word fragments) dictate cost. SyncSphere retrieves token counts from OpenRouter responses in the backend. We log this in `PromptExecutionDocument` to track per-tenant compute expenses accurately.
**Error handling / Retries & Rate Limiting:** We implement HTTP 429 Exponential Backoff in the `OpenRouterAdapter` service to retry failed requests automatically.

### SECTION 9: WORKFLOW ENGINE

**Explain complete workflow execution.**
**Prompt:** User inputs: "Get latest Jira ticket and draft Google Doc summary."
**-> Planner:** AI LLM (OpenRouter) decomposes it.
**-> Structured Plan:** AI outputs JSON matching MCP tools.
**-> Workflow Graph / Compiler:** SyncSphere transforms JSON to DAG (Directed Acyclic Graph) in React Flow format. Node 1: Jira Tool, Node 2: Google Doc Tool. Edge: Jira (Output) -> Google Doc (Input).
**-> Execution Queue:** FastAPI places nodes with 0 In-Degree on an async queue.
**-> Connectors:** `ConnectorRegistry` is invoked by the node.
**-> Result:** Data fetched is written to MongoDB.
**-> Dashboard:** SSE/Websockets push node visual status updates (Success/Failure) to the frontend.

**Workflow compiler:** Translates generic LLM plans into strict executable internal representations `WorkflowDocument`.
**DAG (Directed Acyclic Graph):** Mathematical model. Nodes execute *only* when all parent node dependencies resolve successfully. Acyclism prevents infinite loops.
**Node execution (Parallel / Sequential):** If Node B and Node C both depend on Node A, they run strictly sequentially after A. Node B and C are then executed perfectly parallel using Python's `asyncio.gather`.
**Retries / Rollback / Error Recovery:** If an API timeouts, the workflow engine automatically retries up to configured retry limit. If terminal failure, graph executes compensation nodes (Rollback) or pauses.
**Human approval:** A `system.approval` node halts the executor engine entirely. The state is serialized to MongoDB. When Human clicks 'Approve', a new execute worker starts, deserializes the workflow, and resumes.

### SECTION 10: CONNECTORS

**Connector architecture:** Built on standard Strategy Patterns and the MCP spec.
**BaseConnector:** Interface/Abstract Class defining core methods: `authenticate()`, `refresh_token()`, `execute_action()`, `get_schema()`.
**OAuth vs API connecters:** OAuth relies on redirect loops generating authorization codes, swapped for Access+Refresh tokens. API connectors just require statically securely stored strings.
**Connector registry:** A central singleton factory pattern resolving string IDs ("slack_connector") to Python class instances (`SlackConnector()`).
**Connector discovery & lifecycle:** During app lifespan startup, registry loads classes from `backend/src/connectors/`.
**Explain Gmail/Slack/GitHub...:** Each extends BaseConnector. Gmail relies on `google-auth-oauthlib`, parses thread IDs. Github executes GraphQL/REST based on MCP schema definitions, returning unified data arrays.
**OAuth flow:**
1. Setup URL requested `/v1/connectors/google/auth`
2. Client redirects to `accounts.google.com/?client_id=...`
3. Callback route receives `?code=xxxx`
4. Backend swaps code for Access/Refresh token.
5. Saves to `ConnectorConfigurations` encrypted.

### SECTION 11: FASTAPI

**FastAPI architecture:** Asynchronous web framework on Starlette/Pydantic. High performance driven by `uvloop`.
**Routers:** `APIRouter()` slices large applications into domain chunks (e.g. auth routes, workspace routes) avoiding massive `main.py` files.
**Dependency injection (`Depends`):** Exists to inject singletons (DB connection, OpenRouter clients, Redis Cache) into endpoints. Massively improves testability (easily mocked out).
**Pydantic:** Validates payload strictly. If frontend sends `age: "old"` instead of integer, Pydantic immediately throws a 422 Unprocessable Entity *before* it hits our code.
**OpenAPI / Swagger:** FastAPI uses Pydantic to auto-generate the interactive docs at `/docs`.
**Async:** Handled via `async def`. Underneath, runs on an event loop multiplexing network wait times.
**Background tasks:** Passed to endpoints (`BackgroundTasks`). Executes logic post-HTTP response (e.g., triggering the Execution Engine asynchronously after 'Save and Run' completes HTTP 201).
**Exception handlers & Lifespan:** Custom `@app.exception_handler` intercepts exceptions and formats unified JSON API errors. Lifespan explicitly connects/disconnects MongoDB and Redis ensuring clean boots/teardowns.


# SyncSphere: Enterprise AI Workflow Orchestration Platform
## VIVA Preparation Guide - Sections 12 to 15

### SECTION 12: API MANAGEMENT

**REST API design:** SyncSphere follows strict RESTful conventions using nouns, not verbs.
- **GET:** Safely retrieves data. Idempotent. (e.g., `GET /v1/workflows`)
- **POST:** Creates new documents. Non-idempotent. (e.g., `POST /v1/planner/generate`)
- **PUT:** Completely replaces an entire resource.
- **PATCH:** Partially updates properties without affecting others. (e.g., `PATCH /v1/workflows/{id}`)
- **DELETE:** Removes a resource entirely.

**Status codes:** Follows IETF standards strictly. 200 (Success), 201 (Created), 400 (Bad Request - schema mismatch), 401 (Unauthorized - missing token), 403 (Forbidden - RBAC fail), 404 (Not Found), 422 (Unprocessable Entity - validation error from FastAPI), 500 (Internal Server Error).
**Validation:** FastAPI relies on Pydantic to introspect schemas and types and validate payloads implicitly.
**Authentication/Authorization:** Verified via Global Middleware/Dependencies injecting stateless JWT tokens payload into request contexts.
**Rate limiting:** Prevents DDoS and resource exhaustion.
**Pagination, Filtering, Sorting:** Query parameters (e.g., `GET /v1/executions?skip=0&limit=50&sort=desc`). Handled via Motor/Beanie skip and limit queries for high performance datasets.
**Versioning:** All routes nested under `/v1/`. Allows non-breaking upgrades in the future by adding a `/v2/` router while keeping `/v1/` intact.

### SECTION 13: SECURITY

**JWT (JSON Web Tokens):** Cryptographically signed payload storing `user_id` and `roles`. Header, Payload (Base64), Signature (HMAC).
**Authentication flow:** User posts email/pass. Server validates against DB hash. Server signs an Access Token (15min expiry) and Refresh Token (7 days). Client stores Access Token in Memory/Auth bearer and Refresh Token in an HTTPOnly, Secure Cookie.
**Authorization:** RBAC (Role Based Access Control). A standard user cannot call an endpoint decorated with `Roles(["ADMIN"])`.
**Environment Variables & Secrets:** Stored securely outside VCS (Version Control Systems). Loaded via `pydantic-settings`.
**HTTPS & CORS:** Handled by Traefik/Nginx layer mapping certificates. CORS in FastAPI sets specific whitelists for Next.js endpoints preventing unauthorized cross-origin browser usage.
**Encryption & Hashing:** Passwords hashed using bcrypt. Sensitive Connector tokens (OAuth access codes stored in MongoDB) are encrypted using AES-256 Symmetric Key encryption at the application level before being saved, ensuring a DB dump alone is useless to hackers.

### SECTION 14: OBSERVABILITY

**Trace/Execution monitoring:** An enterprise orchestrator is a black box without observability. We track exactly *when* an AI changed a state, and *why*.
**Logs:** All system events run through structured JSON loggers mapped to Logstash/Datadog or stored internally in `StructuredLogDocument` MongoDB.
**Metrics & Telemetry:** Token usage aggregated via OpenRouter token counters in response objects, inserted heavily into `PromptExecutionDocument`.
**Dashboard:** The React frontend fetches real-time aggregations. E.g. "Total Connectors Called", "LLM Costs".
**Performance/Alerts:** Tracks DAG execution latency. Overruns trigger an alert if a DAG exceeds pre-set limits.

### SECTION 15: SCALABILITY

**Horizontal scaling:** The architecture is decoupled and strictly stateless. Because JWT is used, and sessions aren't bound to one server instance in memory, we can scale the FastAPI API layer from 1 instance to 10 instances identically.
**Redis / Queues:** While a single node is incredibly efficient, for true horizontal scale, the DAG workflow executor utilizes Redis streams or Celery as a distributed task queue allowing separate "worker nodes" to crunch through node executions parallel to the web tier.
**Workers vs API:** Separation of concerns. API handles fast HTTP requests. Heavy AI tasks get placed on message queues consumed by dedicated Worker clusters, preventing API degradation.
**Docker / Kubernetes:** Both Next.js and FastAPI run inside independent lightweight Docker containers. Kubernetes orchestration triggers Auto-Scaling based on CPU/RAM usage.
**Database Scalability:** MongoDB natively supports horizontal sharding over cluster sets, easily pushing data across multiple machines as the volume of tracing telemetry goes up.


# SyncSphere: Enterprise AI Workflow Orchestration Platform
## VIVA Preparation Guide - Section 16: Technology Breakdown

### React (Frontend UI)
1. **Why chosen:** Largest ecosystem, proven virtual DOM performance.
2. **Alternatives:** Vue, Angular, Svelte.
3. **Advantages:** Declarative UI, massive component library ecosystem.
4. **Disadvantages:** Complex state management scaling, high boilerplate.
5. **Where used:** Rendering view logic across every frontend page.
6. **Which files:** `frontend/app/**/*.tsx`, `frontend/features/**/*.tsx`.
7. **Module logic:** Used by the client browser engine.
8. **If fails:** Client-side crash (White Screen of Death).
9. **Error handling:** React Error Boundaries intercept errors and display fallback UIs.
10. **Future:** Server Components migration natively to reduce client bundle.

### Next.js (Full Stack Framework)
1. **Why chosen:** Native React support, file-based routing out-of-the-box.
2. **Alternatives:** Vite, Remix, Create React App.
3. **Advantages:** SSR (Server-Side Rendering), great SEO, out-of-box API routes if needed.
4. **Disadvantages:** Heavy, highly opinionated directory structures.
5. **Where used:** The overarching frontend orchestrator framing the React code.
6. **Which files:** `frontend/next.config.ts`, `app/layout.tsx`.
7. **Module logic:** Built and served by Node.js.
8. **If fails:** Server stops serving the UI; 502 Bad Gateway.
9. **Error handling:** Docker restart policies, PM2 auto-restart. Next.js native `error.tsx` pages.
10. **Future:** Transitioning API middleware into Edge functions for faster execution.

### FastAPI (Backend Framework)
1. **Why chosen:** Native Swagger/OpenAPI support, Pydantic integration, Async native execution.
2. **Alternatives:** Django, Flask, Express.js (Node).
3. **Advantages:** Type-safe API interfaces, extreme runtime performance (ASGI).
4. **Disadvantages:** Lacks built-in ORM/Auth components like Django provides.
5. **Where used:** Core backend API powering workflow execution.
6. **Which files:** `backend/src/syncsphere/main.py`, `routers/*.py`.
7. **Module logic:** Uvicorn ASGI server loads FastAPI instance.
8. **If fails:** HTTP 500 errors to frontend, breaking all functionalities.
9. **Error handling:** Global Exception Handlers translating internal Python errors to structured JSON API errors.
10. **Future:** GraphQL integration for specific data-heavy endpoints.

### MongoDB (Database)
1. **Why chosen:** Document-oriented NoSQL is perfect for variable JSON DAG graphs.
2. **Alternatives:** PostgreSQL (JSONB), DynamoDB, Cassandra.
3. **Advantages:** Highly flexible schemas, native Vector Search integration.
4. **Disadvantages:** Dropping ACID transactions in complex multi-document updates (though partially supported).
5. **Where used:** Storing all application state (Users, Workflows, Telemetry, Vectors).
6. **Which files:** `backend/src/syncsphere/core/database.py`, `documents/*.py`.
7. **Module logic:** Beanie ODM connects to Motor connecting to MongoDB Atlas.
8. **If fails:** Read/write failures stall all pipeline executions.
9. **Error handling:** Connection pooling, automatic reconnections, circuit breakers in API.
10. **Future:** Implement strictly sharded collections based on `org_id`.

### OpenRouter (AI Model Hub)
1. **Why chosen:** Standardizes multi-LLM access through one API.
2. **Alternatives:** Direct OpenAI API, Local LLama (Ollama), LangChain Hub.
3. **Advantages:** Instant redundancy across providers. Zero lock-in.
4. **Disadvantages:** Slight extra latency hops; third-party data privacy concerns.
5. **Where used:** Prompt decomposing inside Planner.
6. **Which files:** `backend/src/syncsphere/planner/services/llm_router.py` (simulated logic).
7. **Module logic:** OpenRouterAdapter invokes external internet API endpoints.
8. **If fails:** AI features degrade entirely (cannot plan workflows).
9. **Error handling:** Fallback model routing defined in headers, exponential backoff HTTP retries.
10. **Future:** Fine-tuned local models acting as primary router to eliminate external API costs.

### React Flow (Workflow graph UI)
1. **Why chosen:** Industry standard for node connections.
2. **Alternatives:** GoJS, JointJS, D3.js.
3. **Advantages:** Native React hooks, incredibly customizable.
4. **Disadvantages:** Graph calculations can lag with 1000+ nodes on screen.
5. **Where used:** Workflow Builder main interface.
6. **Which files:** `frontend/features/workflow-builder/components/FlowCanvas.tsx`.
7. **Module logic:** Reads Zustand state and parses into viewports.
8. **If fails:** Graph explodes or nodes misalign visually.
9. **Error handling:** Strict schema parsing before mounting nodes to ensure bounds check.
10. **Future:** WebGL rendering backend for performance.

### Beanie ODM (Object Document Mapper)
1. **Why chosen:** Motor native, merges FastApi Pydantic types directly to MongoDB documents.
2. **Alternatives:** MongoEngine, PyMongo (raw).
3. **Advantages:** Type hinting, async operations out of the box.
4. **Disadvantages:** Less mature ecosystem than SQLAlchemy.
5. **Where used:** Abstraction layer between Python code and DB.
6. **Which files:** `**/*/documents/*.py`
7. **Module logic:** Invoked by Service layer.
8. **If fails:** DB operations hit exceptions during serialization.
9. **Error handling:** Pydantic validation intercepting bad data before pushing to DB.
10. **Future:** Custom caching layer on top of Beanie links.


# SyncSphere: Enterprise AI Workflow Orchestration Platform
## VIVA Preparation Guide - Section 16: Viva Questions (Part 1)

### Architecture & Conceptual Questions (Q1 - Q25)
1. **Explain the overall architecture of SyncSphere.**
   *Ans:* SyncSphere uses a decoupled modular architecture. A React/Next.js frontend connects via a REST API to a FastAPI backend. The backend is split into domain modules (Planner, Workflow, Connectors, Knowledge, Identity). It uses MongoDB for operational and vector data, and external AI providers (OpenRouter) for LLM access.
2. **What problem does SyncSphere solve that a raw LLM cannot?**
   *Ans:* LLMs lack execution capabilities and direct context of enterprise data. SyncSphere gives AI the ability to execute tasks using MCP Connectors and provides enterprise context via RAG, all within a governed workflow approval system.
3. **What is a DAG and why is it used in the Workflow Engine?**
   *Ans:* Directed Acyclic Graph. It defines execution boundaries. Nodes have dependencies. Acyclism prevents infinite loops, ensuring workflows inevitably reach a terminal state.
4. **How do you handle cyclic tendencies generated by AI?**
   *Ans:* The Workflow Compiler explicitly parses generated graph edges and runs a cycle-detection algorithm (e.g., Kahn's Algorithm) rejecting or breaking cycles before saving the `WorkflowDocument`.
5. **Why build a modular monolith instead of microservices?**
   *Ans:* Microservices introduce massive operational overhead (network latency, distributed tracing, complex deployments). A modular monolith in FastAPI provides decoupling of domains at the code level but operates simply as one process, making it highly maintainable for an MVP-to-Growth stage system.
*(Proceeding with representative tough questions for brevity in part 1)*
6. **Explain the execution loop of a Workflow.**
   *Ans:* Trigger -> Fetch DAG -> Find nodes with in-degree 0 -> Send to workers -> Await results -> Pass outputs to child node inputs -> Decrement child in-degree -> Execute next nodes -> End when queue empty.
7. **What is the difference between an Orchestrator and a Choreographer in distributed systems?**
   *Ans:* SyncSphere is an orchestrator: central controller telling components what to do (the Engine executing connectors). Choreography relies on components subscribing to events independently without a central conductor.
8. **If the backend crashes mid-workflow, how do you recover state?**
   *Ans:* Execution states are persisted in MongoDB `WorkflowExecutionLogDocument` *before* a node executes, and *after*. On restart, a scavenger process finds "RUNNING" nodes that lost their worker lock and retries them, utilizing idempotency constraints.

### Frontend Questions (Q26 - Q50)
26. **Why use React Flow instead of writing custom DOM logic?**
    *Ans:* Managing SVG/Canvas transformations (pan/zoom) and computing recursive DAG visual layouts is mathematically complex. React Flow handles viewport states flawlessly.
27. **How does Zustand differ from React Context for the Workflow Builder?**
    *Ans:* Context triggers a re-render of all consuming components when state changes. Zustand allows selecting specific slices (e.g. `const nodes = useStore(s => s.nodes)`). In a highly active graph (dragging nodes 60fps), Context would cause crippling render lag; Zustand only re-renders the dragged node.
28. **Explain how optimisitic UI works on the executions dashboard.**
    *Ans:* When clicking 'Run', we instantly inject a pending execution object into the React Query cache using `queryClient.setQueryData`, making the UI instantly responsive. If the HTTP request fails, we roll back the cache `onMutate`.
29. **What is the hydration process in Next.js?**
    *Ans:* Next.js sends static HTML to the user. React boots up on the client side, attaches event listeners to this HTML, and "hydrates" it into a fully interactive Single Page Application.
30. **How do you manage complex form validation for Connectors?**
    *Ans:* We use React Hook Form integrated with Zod resolvers. Zod schemas exactly mirror our Backend Pydantic schemas, ensuring no malformed JSON ever leaves the client.

### Backend Details (Q51 - Q75)
51. **Why FastAPI over Flask?**
    *Ans:* Flask is WSGI (synchronous). FastAPI is ASGI (asynchronous). Workflow orchestration requires massive network I/O waiting (API calls to OpenRouter, Connectors). async/await in FastAPI allows one thread to handle thousands of concurrent waits, impossible in Flask without heavy threading.
52. **How does Dependency Injection work in FastAPI in SyncSphere?**
    *Ans:* We use `Depends(get_service)`. When a route is called, FastAPI resolves the dependencies in order, instantiating the Database connection, User Token, and Service classes before passing them as kwargs to the route function.
53. **What is Middleware doing in SyncSphere?**
    *Ans:* `CorrelationIdMiddleware` injects a UUID into the request state. `RequestLoggingMiddleware` grabs it to log start/end times. `TenantMiddleware` extracts the `X-Org-Id` mapping data isolation.
54. **Explain top-down error handling in the API.**
    *Ans:* A generic Python exception raised in a Service bubble up. A global `@app.exception_handler(Exception)` catches it, logs the traceback via Observability, and returns a sanitized HTTP 500 JSON response to the user, preventing sensitive stack traces from leaking.
55. **How do background tasks work in the workflow execution?**
    *Ans:* Instead of holding the HTTP request open while the DAG executes (which could take 5 minutes and timeout), we enqueue the DAG start via `BackgroundTasks` (or Redis) and instantly return a 201 Created and an Execution ID. The client then polls or opens an SSE stream using that ID.

### Database Questions (Q76 - Q100)
76. **How does MongoDB handle unstructured Workflow state?**
    *Ans:* Documents are stored as BSON. Workflows rely on deeply nested structures (`WorkflowDocument` -> `nodes[]` -> `config{}`). MongoDB allows varied `config` fields for a Slack node vs a Github node natively.
77. **Explain the impact of ObjectID vs UUIDs in SyncSphere.**
    *Ans:* We use MongoDB's native ObjectId. It has a timestamp embedded inherently, acting as a chronological sorting mechanism out of the box, useful for execution logs.
78. **What is the risk of deeply nesting node configs in a single document?**
    *Ans:* 16MB document size limit in MongoDB. For extremely large DAGs with massive data payloads stored purely in nodes, it will fail. Workaround: Store large payloads in `MemoryDocument` and pass reference IDs between nodes in the workflow.
79. **How do you ensure data isolation between organizations?**
    *Ans:* A hardcoded `tenant_id` field in every Beanie document. All service queries inject `.find({"tenant_id": current_tenant})`.
80. **Why use Beanie over direct Motor queries?**
    *Ans:* Motor returns raw dicts requiring manual parsing. Beanie maps Motor outputs directly into Pydantic models automatically verifying type safety and providing dot-notation access in Python code.


# SyncSphere: Enterprise AI Workflow Orchestration Platform
## VIVA Preparation Guide - Section 16: Viva Questions (Part 2)

### RAG and Embeddings (Q101 - Q125)
101. **What is the critical difference between fine-tuning and RAG?**
     *Ans:* Fine-tuning trains the model's parametric weights on new data (expensive, slow, hallucinates easily, hard to update). RAG injects non-parametric data into the prompt at runtime (cheap, real-time updatable, grounded citations).
102. **Explain the vector dimension requirement for MongoDB Atlas Search.**
     *Ans:* The index configuration must exactly match the output dimensions of the embedding model (e.g., 1536 for OpenAI `text-embedding-3-small`). A mismatch causes the similarity index to crash.
103. **How do you prevent context window exhaustion when injecting RAG?**
     *Ans:* We rank chunks via Cosine Similarity and explicitly limit injection to Top K chunks. We dynamically measure the token count of Top K; if it exceeds the model's safe context limit minus the original prompt size, we truncate the retrieved chunks.
104. **Why use Cosine Similarity instead of Euclidean Distance?**
     *Ans:* Cosine similarity measures the angle between vectors, normalizing for magnitude length. This means a long document and a short document with the same semantic meaning will match closely regardless of word count. Euclidean distance would penalize the length difference.
105. **How does SyncSphere parse PDFs for ingestion?**
     *Ans:* A Python pipeline uses libraries like PyPDF2 or Unstructured to strip binary formatting and extract raw UTF-8 strings before passing to the LangChain chunker.

### Model Context Protocol (MCP) (Q126 - Q150)
126. **What is the main limitation of traditional plugin architectures that MCP solves?**
     *Ans:* Traditional plugins require hardcoded client SDKs per model (OpenAI functions vs Anthropic tools). MCP acts as the intermediary. We write one MCP server. Claude, GPT4, and the SyncSphere orchestrator can all read it instantly.
127. **Describe the JSON-RPC lifecycle of an MCP tool invocation.**
     *Ans:* SyncSphere sends: `{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "send_slack", "arguments": {"msg": "hi"}}}`. The MCP server validates, executes the real API call, and returns `{..., "result": {"content": [{"type": "text", "text": "Success"}]}}`.
128. **How does SyncSphere securely manage MCP Tool dependencies?**
     *Ans:* The `ConnectorRegistry` isolates secrets. The AI NEVER sees the OAuth refresh token for Slack. It only sees the MCP schema for `send_slack`. The backend execution layer injects the token during execution.
129. **What happens if an MCP Connector server goes offline?**
     *Ans:* The workflow execution halts on that node marking it as `FAILED`. The orchestration engine retries based on policy. If permanent, the workflow gracefully fails, generating an alert in the Observability module.

### Observability & Telemetry (Q151 - Q175)
151. **Why is Observability critical in agentic workflows?**
     *Ans:* AI systems are non-deterministic. Without strict UI visualizations tracing how an AI made a decision, debugging an autonomous error in a 50-node enterprise workflow is impossible.
152. **How do you track open/failed workflow executions over time?**
     *Ans:* We record `status` (PENDING, RUNNING, COMPLETED, FAILED) in `WorkflowExecutionLogDocument`. The dashboard polls/listens to aggregations like `db.executions.count({status: "FAILED", created_at: {$gte: 24h_ago}})`.
153. **How does SyncSphere calculate LLM usage costs?**
     *Ans:* OpenRouter returns `usage: {prompt_tokens, completion_tokens}` in every response. SyncSphere maps this to known model pricing metrics (held in `AIModelDocument`) and aggregates it per tenant.
154. **What is the purpose of correlation IDs?**
     *Ans:* A `correlation_id` (UUID) is generated at the very start of the HTTP request. It is passed into logging contexts. If an error happens 3 modules deep in `planner.py`, we can grep the logs for the exact ID to trace the exact user request flow.

### Scalability, Security, & Architecture (Q176 - Q200)
176. **If traffic to SyncSphere spikes 1000x, where is the bottleneck?**
     *Ans:* 1. Database connection limits. 2. ASGI application worker limits. 3. CPU bound JSON serialization. Solution: Increase Kubernetes pods for FastAPI, scale MongoDB cluster tier, offload all executions to a RabbitMQ/Redis queue preventing API exhaustion.
177. **How do you secure API routes from Unauthorized access?**
     *Ans:* JWT tokens validated in a dependency `get_current_user`. The token contains `roles`. Another dependency `RequireRole("ADMIN")` checks the role before allowing route entry.
178. **What is an Idempotent workflow node?**
     *Ans:* A node that can execute multiple times yielding the exact same system state (e.g. updating a DB field to a set value, instead of incrementing it). Crucial for workflow retries safely without causing duplicate issues (like sending 5 identical Slack messages).
179. **How do you handle secrets for user connections (Connectors)?**
     *Ans:* Use Python `cryptography.fernet`. A master platform key encrypts user OAuth tokens before DB storage. If DB is exposed, tokens are unusable.
180. **What happens during a Pydantic Validation error?**
     *Ans:* 422 Unprocessable Entity. The frontend payload didn't match the strictly typed class structure. E.g., The frontend sent `{"user_input": 123}` but backend expected `user_input: str`.

### Scenario Based Questions (Expert Level) (Q201 - Q225)
201. **Scenario:** The AI planner generates a workflow that creates an infinite loop between two nodes. How does the system handle this?
     *Ans:* The `WorkflowCompiler` runs a topological sort before accepting the AI plan. It strictly enforces acyclic properties. The compilation fails, returning an error to the planner or user.
202. **Scenario:** The user triggers a workflow requiring human approval. They close their browser. What happens?
     *Ans:* The FastAPI engine parks the execution state in MongoDB as `status: WAITING_APPROVAL`. It uses zero CPU. When the user logs back in days later, they see a pending approval in their Dashboard and continue it.
203. **Scenario:** OpenRouter's primary model goes offline during high-load.
     *Ans:* Requests trigger `HTTP 502/503`. The `OpenRouterAdapter` catches `httpx.HTTPError`, implements exponential backoff, and eventually falls back to a secondary `fallback_model` string specified in the request headers natively supported by OpenRouter.
204. **Scenario:** The RAG system retrieves irrelevant documents, causing hallucinated plans.
     *Ans:* Vector search matches syntax but maybe not intent. We would implement an iterative RAG step. The LLM first analyzes the prompt, generates specific search queries, fetches chunks, and relies on an explicit instruction: 'If context is irrelevant, state you do not know. Do not guess.'


