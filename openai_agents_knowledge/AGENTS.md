## Documentation & Knowledge Sources

**CRITICAL: ALWAYS consult the official, up-to-date online documentation for any library, framework, or programming language you are working with before implementing or changing anything related to it.**  
Your **primary source** for technical reference should be the official documentation available on the internet.

When using any API, class, method, or tool:
1. Look up the relevant section in the official documentation.
2. Verify syntax, arguments, return types, and intended behavior.
3. Follow usage patterns recommended in the official examples.
4. If uncertain, re-check the official docs or ask the user for clarification — never guess or hallucinate API usage.

### OpenAI Agents SDK — Special Considerations

Circuitron uses a **new and in-development library**: **OpenAI Agents SDK**.  
We are working with **version `0.1.0`**, and the local documentation included in this repository matches this exact version.  
Online documentation may refer to newer versions with API changes — when conflicts arise between the online docs and the local knowledge base, always **prioritize the local version** to ensure compatibility.

### Fallback to Local Documentation (when to use it)

If you cannot access online documentation (e.g., due to network restrictions, rate limits, or downtime) or need to confirm the exact behavior for version `0.1.0`, use the **local OpenAI Agents SDK Knowledge Base** included in the repository:

  **Location:** `openai_agents_knowledge/` directory in project root
  **Key Files:**
  - `openai_agents_knowledge_base.md` - Complete consolidated knowledge base (44,400+ lines)
  - `file_catalog.md` - Detailed catalog of all 361 source files
  - `code_analysis.md` - Python code structure and module analysis
  - `README.md` - Usage guide for the knowledge base
  
  **Usage Instructions:**
  - **For implementation patterns:** Reference `/examples/` section for 73+ practical usage examples
  - **For core functionality:** Study `/src/agents/` section for main SDK implementation
  - **For testing approaches:** Examine `/tests/` section for comprehensive test patterns
  - **For specific features:** Use file catalog to locate relevant source files
  - **For architecture understanding:** Consult code analysis for module relationships