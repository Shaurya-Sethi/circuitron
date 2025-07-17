# Circuitron

## Project Goal

Develop an agentic, AI-powered PCB design accelerator for professional power electronics engineers.  
Circuitron will transform natural language requirements into design plans, output valid netlists, automatically generate and display KiCad schematics, and also generate (.kicad_pcb files) fully routed pcb layouts. The system will provide an interactive, session-aware workflow, supporting project histories and plan-approve-edit-act paradigm to ensure accurate and user-approved designs. 
The tool acts as a productivity booster: it provides a high-quality, logically correct skeleton (with full design rationale) that engineers can review, edit, and finalize using industry-standard workflows.

---

## Key Features & Workflow

### **1. Agentic, Reasoning-Driven Workflow**
- **Orchestration:** Uses OpenAI Agents SDK for chaining LLM, RAG via Model Context Protocol, code execution, and user feedback/approval.
- **LLM “Brain”:** Runs on a reasoning-capable LLM (OpenAI API).
- **RAG (Retrieval-Augmented Generation):** Critical to accuracy—a robust retrieval system surfaces relevant SKiDL documentation and usage examples to the LLM for every generation step utilising a MCP Server that exposes tools like `perform_rag_query` and `search_code_examples`.
- **Chain-of-Thought Reasoning:** All design decisions are presented as transparent, stepwise plans (including calculations), which the user can review, approve, or edit before design files are generated.

### **2. SKiDL-Based Schematic and Netlist Generation**
- **SKiDL Python code** is generated based on user prompt, design rationale, and retrieved part information, guided by the RAG system to ensure generation of accurate code that is consistent with SKiDL's API.
- **Accurate Part Selection:** The agent queries the actual installed KiCad libraries (via SKiDL's built in search(), in Docker environment) to ensure only real, available components are used.
- **User Control:** Engineers may override or select preferred parts before code is finalized. (Planned)
- **Native Schematic Export:** SKiDL generates a `.sch` schematic file via `generate_schematic`, **directly openable and editable in KiCad**—the industry gold standard. **Note that as of June 2025, this can be opened only in KiCad V5.**
- **Netlist and BOM Generation:** SKiDL also outputs netlists for BOM tools, SPICE simulation, or further processing.
- **SVG Schematic Preview:** Instant schematic visualization in the UI for quick review using `generate_svg()`; fully compatible `.kicad_sch` available for advanced edits.

### **3. PCB Layout & Autorouting**
- **PCB Layout Generation:** Using SKiDL’s `generate_pcb()` or compatible tools, Circuitron outputs `.kicad_pcb` files for physical design.
 - **DeepPCB API Integration:** *Planned*: Circuitron will optionally submit PCB layouts to `DeepPCB` for AI-assisted auto-routing. The public API documentation is currently limited, so this feature will be implemented in a future release.
  - **Caveat:** All autorouted layouts are clearly labeled as drafts for human review and optimization, especially for power applications.
- **Full Design Transparency:** All design artifacts (reasoning, schematic, PCB, logs) are provided for auditability and compliance.

### **4. Engineer-First Interface**
- **Interactive Approval Loop:** Engineers review the LLM’s chain-of-thought and the proposed design plan before code execution.
- **UI/UX:** Circuitron exposes a modern TUI, starting with rich (for prototyping and demonstration) and later extending to a scalable React-based frontend.
- **All files downloadable in native KiCad formats**—ensuring seamless integration with professional toolchains.
- **Session Memory / Project History**
  - This is a planned feature for future releases.
  - Each design session is tied to a project.
  - The system stores all prompts, plans, netlists, and schematics for each project.
  - Users can review past designs and iterations, and RAG is used to recall relevant prior work for context
---

## Tech Stack

- **Backend Orchestration:** OpenAI Agents SDK (Python)
- **LLM:** Currently OpenAI with future plans for Local LLM support via Ollama, and support for other providers.
- **RAG:** Via MCP (Model Context Protocol) server, indexing SKiDL docs, example designs
- **Schematic & Netlist Generation:** SKiDL (Python)
- **PCB Layout Generation:** SKiDL
- **Autorouting:** Planned DeepPCB API integration (documentation still evolving)
- **File Management:** Dockerized KiCad install for part searches and file generation
- **Frontend:** rich CLI (prototype), React/Next.js (production)
- **Containerization:** Docker for reproducibility, dependency isolation

---

## Sample Implementation Workflow

1. **User Input:**  
   - Engineer submits design prompt (e.g., “Design a 3-phase inverter gate driver with isolated power supplies and desat detection”).
2. **LLM Planning & Reasoning:**  
   - LLM (guided by RAG) generates a stepwise plan, rationale, and any required calculations.
   - User reviews, approves, or edits the plan.
3. **Part Selection & SKiDL Code Generation:**  
   - Agent searches local KiCad libraries for real parts matching requirements via SKiDL's built in `search()` function.
   - LLM generates SKiDL code, reflecting user preferences and constraints.
4. **File Generation:**
   - SKiDL script can generate:
     - `.sch` schematic
     - Netlist
     - SVG schematic for UI preview
     - `.kicad_pcb` layout file
5. **Code Validation:**
   - A dedicated agent checks the script for hallucinations and syntax issues using a knowledge graph via `query_knowledge_graph` (exposed by MCP server).
6. **Code Correction Loop:**
   - If validation fails or ERC reports errors, dedicated agents iteratively fix the code and re-run checks.
7. **Electrical Rule Checking:**
   - SKiDL Performs electrical rules checking (ERC) for common mistakes (e.g., unconnected device I/O pins).
8. **PCB Autorouting (future):**
   - Planned support for submitting `.kicad_pcb` files to DeepPCB for AI-assisted routing once the API stabilizes.
6. **Review & Handoff:**  
   - UI displays all files, design logs, and rationale.
   - Engineers can download and open all files directly in KiCad for review, simulation, further editing, and sign-off.

---

## Positioning & Expectation Setting

- **Productivity Booster, Not Replacement:**  
  Circuitron is designed to accelerate and support engineers, not bypass expert review.  
  Every output is fully transparent, reviewable, and modifiable—never “fire-and-forget.”
- **Maximum Compatibility:**  
  All design files are native to KiCad (schematic, PCB, netlist, BOM).
- **Full Reasoning:**  
  Design process, chain-of-thought, and rationale are always included—boosting trust and auditability.
- **Strict Transparency:**  
  All auto-generated designs are labeled as drafts for professional review, especially for high-power or safety-critical boards.

---

## Stretch Goals & Roadmap

* **Sequential Thinking MCP Integration:**
  Incorporate the `sequential thinking` MCP server at the initial planning stage to generate more comprehensive, high-quality design plans—improving overall project structure and reasoning quality.

* **Reliable & User-Centric Footprint Search:**
  Continue developing a dedicated agent for stable, accurate footprint searches. Extend this by integrating GUI-based search tools (e.g., `zyc`), allowing engineers to manually select footprints for increased control and trust in the design flow.

* **Streamlined Web/Desktop App:**
  Expand Circuitron beyond CLI by implementing a user-friendly web app or desktop application. This will make advanced features like manual footprint selection and visual design review easily accessible to all users.

* **Schematic Beautification Agent:**
  Build a schematic beautification agent leveraging powerful vision-language models to automatically review, enhance, and optimize schematic visuals for clarity, aesthetics, and adherence to best practices.

* **Advanced Autorouting with DeepPCB API:**
  Integrate DeepPCB’s public API for robust, AI-powered PCB autorouting, once their API is stable and fully documented, closing the loop from schematic to manufacturable PCB layout.

* **Agentic Memory & Multi-Project Management:**
  Architect a persistent, context-aware memory system to support multi-design projects, shared project context, design history, and smarter, session-aware agent workflows—drawing inspiration from advanced agentic frameworks like `cline`.

---

## References & Links

- [SKiDL Documentation](https://devbisme.github.io/skidl/)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)

---