# `query_knowledge_graph` Tool — Analysis

## **Purpose**

The `query_knowledge_graph` tool provides a command-driven interface for agents (and, by extension, users) to explore and query a Neo4j knowledge graph that models the structure and relationships of parsed GitHub repositories. This enables advanced exploration and validation of repository internals (repositories, files, classes, methods, functions, attributes).

---

## **Function Signature**

```python
@mcp.tool()
async def query_knowledge_graph(ctx: Context, command: str) -> str:
```
- **ctx:** The MCP server context (handles access to the Neo4j driver and session).
- **command:** A string command specifying what to query; supports a set of predefined and custom commands (see below).
- **Returns:** JSON string containing results, errors, metadata, etc.

---

## **How It Works**

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
   | `method <method_name>`       | Search for methods by name across all classes (limited to 20).          |
   | `method <method_name> <class_name>` | Search for a method within a specific class.                    |
   | `function <function_name>`   | Search for standalone functions by name (limited to 20).                |
   | `query <cypher_query>`       | Perform a custom Cypher query (graph database query language).          |

4. **Response:**  
   - Always returns a JSON string, with:
     - `success`: Boolean.
     - `command`: The parsed command.
     - `data`: Results (varies by command).
     - `metadata`: (e.g., counts, limits).
     - `error`: Error message if applicable.

---

## **How to Use `query_knowledge_graph` in a Custom Agent**

### **Preparation**
- Ensure Neo4j is running and environment variables are correctly set (`USE_KNOWLEDGE_GRAPH=true`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`).
- The knowledge graph should already be populated (e.g., via `parse_github_repository`).

### **Step-by-step Usage**

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

6. **Search for standalone functions by name**  
   ```python
   result_json = await query_knowledge_graph(ctx, "function hello")
   ```

7. **Run a custom Cypher query**  
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
| `explore <repo_name>`                      | Stats (files, classes, functions, methods) for a repo    |
| `classes`                                  | List up to 20 classes across all repos                   |
| `classes <repo_name>`                      | List up to 20 classes in the specified repo              |
| `class <class_name>`                       | Methods and attributes for a class                       |
| `method <method_name>`                     | All methods with this name (across all classes, limit 20)|
| `method <method_name> <class_name>`        | Method info scoped to a given class                      |
| `function <function_name>`                 | All standalone functions with this name (limit 20)       |
| `query <cypher_query>`                     | Run a custom Neo4j Cypher query (max 20 results)         |

---
