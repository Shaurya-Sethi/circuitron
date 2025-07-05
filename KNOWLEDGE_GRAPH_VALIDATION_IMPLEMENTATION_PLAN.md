# Knowledge Graph-Based Validation Implementation Plan

## Current Implementation Analysis

### Current System Architecture

**Agent Configuration (agents.py):**
- `create_code_validation_agent()` uses `tools=[check_ai_script_hallucinations]`
- `create_code_correction_agent()` uses `tools=[check_ai_script_hallucinations, run_erc_tool]`
- Both agents access `mcp_manager.get_validation_server()` which provides the existing MCP server
- Both agents already have access to `query_knowledge_graph` through the validation MCP server

**Data Models (models.py):**
- `HallucinationReport` class captures the broken tool's output structure
- `CodeValidationOutput` contains a `hallucination_report: HallucinationReport | None` field
- Supporting models: `ValidationSummary`, `AnalysisMetadata` with counts and metrics
- These models are tightly coupled to the failed tool's output format

**Agent Instructions (prompts.py):**
- Validation agent prompt: "Use the `check_ai_script_hallucinations` tool on the provided script content"
- Correction agent prompt: Multiple references to re-validating with `check_ai_script_hallucinations`
- Existing knowledge graph integration guidance is present but secondary to the broken tool

**Tool Implementation (tools.py):**
- `check_ai_script_hallucinations()` function makes HTTP API calls to MCP server
- Function is exported in `__all__` lists (appears twice - line 15 and 38)
- `create_mcp_validation_server()` creates the MCP server that provides `query_knowledge_graph`

**Utility Functions (utils.py):**
- `parse_hallucination_report()` specifically parses the broken tool's JSON output

## Implementation Plan: Transition to Knowledge Graph Validation

### `query_knowledge_graph` Tool — Analysis

#### **Purpose**

The `query_knowledge_graph` tool provides a command-driven interface for agents (and, by extension, users) to explore and query a Neo4j knowledge graph that models the structure and relationships of parsed GitHub repositories. This enables advanced exploration and validation of repository internals (repositories, files, classes, methods, functions, attributes).

---

#### **Function Signature**

```python
@mcp.tool()
async def query_knowledge_graph(ctx: Context, command: str) -> str:
```
- **ctx:** The MCP server context (handles access to the Neo4j driver and session).
- **command:** A string command specifying what to query; supports a set of predefined and custom commands (see below).
- **Returns:** JSON string containing results, errors, metadata, etc.

---

#### **How It Works**

1. **Pre-checks:**  
   - Checks if knowledge graph functionality is enabled (`USE_KNOWLEDGE_GRAPH=true`).
   - Validates Neo4j connection.

2. **Command Parsing:**  
   - Splits the `command` string to determine the instruction and its arguments.
   - Routes to handler methods for each supported command.

3. **Supported Commands:**  
   (Full command set is documented in the docstring, and reinforced by code.)

   | Command Example              | Description                                                             |
   |------------------------------|-------------------------------------------------------------------------|
   | `repos`                      | List all repositories in the knowledge graph (start here!).             |
   | `explore <repo_name>`        | Overview and statistics for a specific repository.                      |
   | `classes`                    | List all classes across all repositories (limited to 20).               |
   | `classes <repo_name>`        | List classes in a specific repository.                                  |
   | `class <class_name>`         | Get methods and attributes for a specific class.                        |
   | `method <method_name>`       | Search for methods by name across all classes.                          |
   | `method <method_name> <class_name>` | Search for a method within a specific class.                    |
   | `query <cypher_query>`       | Perform a custom Cypher query (graph database query language).          |

4. **Response:**  
   - Always returns a JSON string, with:
     - `success`: Boolean.
     - `command`: The parsed command.
     - `data`: Results (varies by command).
     - `metadata`: (e.g., counts, limits).
     - `error`: Error message if applicable.

---

#### **How to Use `query_knowledge_graph` in a Custom Agent**

#### **Preparation**
- Ensure Neo4j is running and environment variables are correctly set (`USE_KNOWLEDGE_GRAPH=true`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`).
- The knowledge graph should already be populated (e.g., via `parse_github_repository`).

#### **Step-by-step Usage**

1. **List all repositories in the knowledge graph**  
   ```python
   result_json = await query_knowledge_graph(ctx, "repos")
   ```

2. **Get statistics and structure of a specific repo**  
   ```python
   result_json = await query_knowledge_graph(ctx, "explore my-repo-name")
   ```

3. **List classes in all repos or a specific repo**  
   ```python
   result_json = await query_knowledge_graph(ctx, "classes")
   result_json = await query_knowledge_graph(ctx, "classes my-repo-name")
   ```

4. **Get all info about a specific class**  
   ```python
   result_json = await query_knowledge_graph(ctx, "class MyClassName")
   ```

5. **Find all methods named `run` (optionally scoped to a class)**  
   ```python
   result_json = await query_knowledge_graph(ctx, "method run")
   result_json = await query_knowledge_graph(ctx, "method run MyClassName")
   ```

6. **Run a custom Cypher query**  
   ```python
   cypher = 'MATCH (c:Class)-[:HAS_METHOD]->(m:Method) WHERE m.name = "run" RETURN c.name, m.name LIMIT 5'
   result_json = await query_knowledge_graph(ctx, f"query {cypher}")
   ```

#### **Interpreting Results**

- Parse the returned JSON. Check `"success"`, read `"data"` for structured results, and handle `"error"` if present.
- For commands with potentially large results, note that results are **limited to 20 records** for performance/safety.

#### **Best Practices**

- **Always start with `repos`** to discover what repositories are indexed.
- Use `explore <repo>` before drilling down into classes/methods.
- For custom queries, ensure your Cypher query is safe and will not return excessive data.
- Handle errors gracefully (see `"error"` field in output).

---

#### **Summary Table of Supported Commands**

| Command Syntax                              | Use Case/What It Returns                                 |
|---------------------------------------------|----------------------------------------------------------|
| `repos`                                    | List all repos in the knowledge graph                    |
| `explore <repo_name>`                      | Stats (files, classes, methods, etc.) for a repo         |
| `classes`                                  | List up to 20 classes across all repos                   |
| `classes <repo_name>`                      | List up to 20 classes in the specified repo              |
| `class <class_name>`                       | Methods and attributes for a class                       |
| `method <method_name>`                     | All methods with this name (across all classes)          |
| `method <method_name> <class_name>`        | Method info scoped to a given class                      |
| `query <cypher_query>`                     | Run a custom Neo4j Cypher query (max 20 results)         |

---

### Phase 1: Remove Broken Tool Infrastructure

**1.1 Remove Tool Function (tools.py)**
- Delete the `check_ai_script_hallucinations()` function (lines 300-325)
- Remove `"check_ai_script_hallucinations"` from both `__all__` lists (lines 15 and 38)
- Keep `create_mcp_validation_server()` as it provides `query_knowledge_graph`

**1.2 Update Agent Tool Lists (agents.py)**
- In `create_code_validation_agent()`: Change `tools=[check_ai_script_hallucinations]` to `tools=[]`
- In `create_code_correction_agent()`: Change `tools=[check_ai_script_hallucinations, run_erc_tool]` to `tools=[run_erc_tool]`
- Both agents retain access to `query_knowledge_graph` through the MCP server
- Update agent descriptions to reflect knowledge graph-based validation

**1.3 Remove Tool Import (agents.py)**
- Remove `check_ai_script_hallucinations` from the import statement on line 35

**1.4 Remove Utility Function (utils.py)**
- Delete `parse_hallucination_report()` function (lines 456-460)
- Remove any other utility functions specifically tied to the broken tool's output format

### Phase 2: Update Data Models

**2.1 Replace HallucinationReport Model (models.py)**
- Remove `HallucinationReport`, `ValidationSummary`, and `AnalysisMetadata` classes
- Create new `KnowledgeGraphValidationReport` model with:
  - `total_apis_checked: int` - Total number of APIs validated
  - `valid_apis: int` - Number of confirmed valid APIs
  - `invalid_apis: int` - Number of detected hallucinations
  - `confidence_score: float` - Calculated as `valid_apis / total_apis_checked`
  - `validation_details: List[APIValidationResult]` - Per-API validation results
  - `skidl_insights: List[str]` - Knowledge graph discoveries about correct APIs

**2.2 Create Supporting Models (models.py)**
- New `APIValidationResult` model with:
  - `api_name: str` - Name of function/method/class
  - `api_type: Literal["function", "method", "class"]` - Type of API
  - `target_class: str | None` - For methods, the class they should be on
  - `line_number: int | None` - Location in script
  - `is_valid: bool` - Whether API exists in knowledge graph
  - `fix_suggestion: str | None` - Specific recommendation if invalid

**2.3 Update CodeValidationOutput (models.py)**
- Replace `hallucination_report: HallucinationReport | None` with `kg_validation_report: KnowledgeGraphValidationReport | None`
- Keep existing `status`, `summary`, `issues` fields for backward compatibility

### Phase 3: Rewrite Agent Instructions

**3.1 Validation Agent Prompt (prompts.py)**
- Replace the current prompt section that instructs using `check_ai_script_hallucinations`
- Add systematic knowledge graph validation instructions:
  - **Step 1**: Initialize with `query_knowledge_graph("repos")` and `query_knowledge_graph("explore skidl")`
  - **Step 2**: Extract all API calls from the script (functions, methods, classes)
  - **Step 3**: For each API, use appropriate `query_knowledge_graph` commands:
    - Functions: `query_knowledge_graph("query MATCH (f:Function) WHERE f.name = 'X' RETURN f")`
    - Methods: `query_knowledge_graph("method X ClassName")` 
    - Classes: `query_knowledge_graph("class X")`
  - **Step 4**: Calculate confidence and compile specific issues with fix suggestions

**3.2 Correction Agent Prompt (prompts.py)**
- Remove all 8 references to `check_ai_script_hallucinations` from the prompt
- Update validation workflow to use systematic knowledge graph checking:
  - Replace **Step 3: Re-validate** to use knowledge graph systematic validation
  - Replace **Step 5: Final Validation** to use knowledge graph systematic validation
- Enhance the existing knowledge graph integration guidance to be the primary validation method
- Update the iterative correction process to rely on knowledge graph findings

### Phase 4: Add New Validation Logic

**4.1 Knowledge Graph Validation Patterns**
The agents will implement these validation patterns using natural language instructions:

- **Function Validation**: Query the knowledge graph to check if standalone functions exist
- **Method Validation**: Verify methods exist on specific classes or find which class they belong to
- **Class Validation**: Confirm classes exist in the SKiDL codebase
- **SKiDL-Specific Rules**: Check for common hallucinations like `generate_bom()` and misused Circuit methods
- **Usage Pattern Validation**: Ensure APIs are used correctly (e.g., Circuit methods not called as standalone functions)

**4.2 Response Parsing and Reporting**
Agents will parse `query_knowledge_graph` JSON responses and:
- Count total APIs checked vs valid APIs found
- Generate specific fix suggestions based on what actually exists
- Create line-specific issue reports with actionable recommendations
- Calculate confidence scores based on validation results

### Phase 5: Testing and Validation

**5.1 Create Test Scripts**
- Scripts with known hallucinations (`generate_bom()`, fake methods)
- Scripts with valid SKiDL code for confidence validation
- Edge cases and complex usage patterns

**5.2 Validation Process**
- Test agents can properly initialize knowledge graph connection
- Verify systematic API checking covers all code elements
- Confirm accurate detection of both valid and invalid APIs
- Validate fix suggestions are actionable and correct

**5.3 Performance Validation**
- Measure validation time for typical scripts
- Ensure knowledge graph queries don't timeout
- Test resilience to knowledge graph connectivity issues

### Phase 6: Migration Considerations

**6.1 Backward Compatibility**
- The `CodeValidationOutput` and `CodeCorrectionOutput` models maintain their core interfaces
- Pipeline integration points remain unchanged
- Error handling and fallback mechanisms preserved

**6.2 Configuration Updates**
- Ensure MCP validation server configuration supports the expected knowledge graph tools
- Update any environment variables or settings related to validation
- Verify knowledge graph data is properly populated with SKiDL repository information

**6.3 Documentation Updates**
- Update agent documentation to reflect new validation approach
- Create troubleshooting guides for knowledge graph connectivity
- Document the systematic validation process for maintenance

## Implementation Benefits

**Immediate Advantages:**
- **Functional Validation**: Replaces 0% detection rate with reliable knowledge graph-based checking
- **No New Infrastructure**: Leverages existing, proven `query_knowledge_graph` tool
- **Agent Intelligence**: Utilizes LLM capabilities for flexible, context-aware validation
- **Maintainable**: Changes require prompt updates, not complex code modifications

**Long-term Benefits:**
- **Transparent Logic**: Clear, debuggable validation process using natural language instructions
- **Extensible**: Easy to add new validation rules through prompt enhancements
- **Accurate**: Based on actual SKiDL codebase structure, not brittle AST parsing
- **Resilient**: Less prone to breaking during refactoring or updates

This implementation plan provides a systematic transition from the broken hallucination detection tool to a reliable, knowledge graph-based validation system while preserving existing pipeline integration and providing improved accuracy and maintainability.