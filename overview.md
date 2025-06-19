# Circuitron – Agentic PCB Design Accelerator

## Project Goal

Develop an agentic, AI-powered PCB design accelerator for professional power electronics engineers.  
Circuitron will transform natural language requirements into design plans, output valid netlists, automatically generate and display KiCad schematics, and also generate (.kicad_pcb files) fully routed pcb layouts. The system will provide an interactive, session-aware workflow, supporting project histories and plan-approve-edit-act loops to ensure accurate and user-approved designs. 
The tool acts as a productivity booster: it provides a high-quality, logically correct skeleton (with full design rationale) that engineers can review, edit, and finalize using industry-standard workflows.

---

## Key Features & Workflow

### **1. Agentic, Reasoning-Driven Workflow**
- **Orchestration:** Uses LangChain for chaining LLM, RAG retrieval, code execution, and user feedback/approval.
- **LLM “Brain”:** Runs on a reasoning-capable LLM (API or local), with both options supported via a modular backend.
- **RAG (Retrieval-Augmented Generation):** Critical to accuracy—a robust retrieval system surfaces relevant SKiDL documentation and usage examples to the LLM for every generation step.
- **Chain-of-Thought Reasoning:** All design decisions are presented as transparent, stepwise plans (including calculations), which the user can review, approve, or edit before design files are generated.

### **2. SKiDL-Based Schematic and Netlist Generation**
- **SKiDL Python code** is generated based on user prompt, design rationale, and retrieved part information, guided by the RAG system to ensure generation of accurate code that is consistent with SKiDL's API.
- **Accurate Part Selection:** The agent queries the actual installed KiCad libraries (via SKiDL's built in search(), possibly in Dockerized environments) to ensure only real, available components are used.
- **User Control:** Engineers may override or select preferred parts before code is finalized.
- **Native Schematic Export:** SKiDL generates a `.sch` schematic file via `generate_schematic`, **directly openable and editable in KiCad**—the industry gold standard. **Note that as of June 2025, this can be opened only in KiCad V5.**
- **Netlist and BOM Generation:** SKiDL also outputs netlists for BOM tools, SPICE simulation, or further processing.
- **SVG Schematic Preview:** Instant schematic visualization in the UI for quick review using `generate_svg()`; fully compatible `.kicad_sch` available for advanced edits.

### **3. PCB Layout & Autorouting**
- **PCB Layout Generation:** Using SKiDL’s `generate_pcb()` or compatible tools, Circuitron outputs `.kicad_pcb` files for physical design.
- **DeepPCB API Integration:** Circuitron can optionally submit PCB layouts to DeepPCB for AI-assisted auto-routing.  
  - **Caveat:** All autorouted layouts are clearly labeled as drafts for human review and optimization, especially for power applications.
- **Full Design Transparency:** All design artifacts (reasoning, schematic, PCB, logs) are provided for auditability and compliance.

### **4. Engineer-First Interface**
- **Interactive Approval Loop:** Engineers review the LLM’s chain-of-thought and the proposed design plan before code execution.
- **UI/UX:** Circuitron exposes a modern UI, starting with Streamlit (for prototyping and demonstration) and later extending to a scalable React-based frontend.
- **All files downloadable in native KiCad formats**—ensuring seamless integration with professional toolchains.
- **Session Memory / Project History**
  - Each design session is tied to a project.
  - The system stores all prompts, plans, netlists, and schematics for each project.
  - Users can review past designs and iterations, and RAG is used to recall relevant prior work for context
---

## Tech Stack

- **Backend Orchestration:** LangChain (Python)
- **LLM:** DeepSeek-R1, OpenRouter, Mistral, OpenAI, etc
- **RAG:** Custom-built, indexing SKiDL docs, example designs
- **Schematic & Netlist Generation:** SKiDL (Python)
- **PCB Layout Generation:** SKiDL, KiCad Python APIs
- **Autorouting:** DeepPCB API
- **File Management:** Local or Dockerized KiCad install for part queries and file validation
- **API Service:** FastAPI (Python)
- **Frontend:** Streamlit (prototype), React/Next.js (production)
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
     - Netlist and BOM
     - SVG schematic for UI preview
     - `.kicad_pcb` layout file
5. **Electrical Rule Checking:**
   - SKiDL Performs electrical rules checking (ERC) for common mistakes (e.g., unconnected device I/O pins).
5. **PCB Autorouting:**  
   - `.kicad_pcb` submitted to DeepPCB for AI-assisted routing.
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

- **Web-based Schematic Editor:**  
  Allow engineers to make basic edits/annotations in-browser before downloading.
- **Team Collaboration:**  
  Multi-user projects, feedback, and iterative design history.
- **AI-Driven Schematic Beautification:**  
  Advanced auto-layout for prettier, more readable schematics.
- **Integration with Compliance/Simulation Tools:**  
  Auto-generate simulation files, DRC/EMC checks, and compliance reports.

---

## References & Links

- [SKiDL Documentation](https://devbisme.github.io/skidl/)
- [KiCad Official Site](https://kicad.org/)
- [DeepPCB](https://deeppcb.com/)
- [LangChain](https://langchain.com/)
- [KiCad Symbol Libraries](https://github.com/kicad/kicad-symbols)
- [KiCad Footprint Libraries](https://github.com/kicad/kicad-footprints)

---

**Last Updated:** 2025-06-15