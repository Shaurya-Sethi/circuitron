"""Tools for Circuitron agents.

This module exposes helpers for executing isolated calculations, searching
KiCad libraries and footprints, extracting pin information, running ERC
checks, creating MCP server connections, and retrieving knowledge graph
guidance.
"""

from agents import function_tool
from agents.mcp import MCPServerSse
import asyncio
import os
import subprocess
import textwrap
import json
from .models import CalcResult
from .config import settings
from .docker_session import DockerSession
from .utils import (
    write_temp_skidl_script,
    prepare_output_dir,
    convert_windows_path_for_docker,
)

__all__ = [
    "MCPServerSse",
    "execute_calculation",
    "search_kicad_libraries",
    "search_kicad_footprints",
    "extract_pin_details",
    "create_mcp_server",
    "run_erc",
    "run_erc_tool",
    "run_runtime_check",
    "run_runtime_check_tool",
    "execute_final_script",
    "execute_final_script_tool",
    "get_kg_usage_guide",
]


container_name = f"circuitron-kicad-{os.getpid()}"
kicad_session: DockerSession = DockerSession(settings.kicad_image, container_name)


@function_tool
async def execute_calculation(
    calculation_id: str,
    code: str,
) -> CalcResult:
    """
    Execute pure-Python maths code *generated by the LLM* in an isolated Docker container.

    Args:
        calculation_id: Correlates this request to its tool response.
        code: Python source (generated by the LLM) that prints the final value.
    Returns:
        CalcResult with stdout, stderr, and success flag.
    """
    safe_code = textwrap.dedent(code)
    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--memory",
        "128m",
        "--pids-limit",
        "64",
        settings.calculation_image,
        "python",
        "-c",
        safe_code,
    ]
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
    except subprocess.TimeoutExpired as exc:
        return CalcResult(calculation_id=calculation_id, success=False, stderr=str(exc))
    except subprocess.CalledProcessError as exc:
        return CalcResult(
            calculation_id=calculation_id,
            success=False,
            stdout=exc.stdout.strip(),
            stderr=exc.stderr.strip(),
        )
    except Exception as exc:  # pragma: no cover - unexpected errors
        return CalcResult(calculation_id=calculation_id, success=False, stderr=str(exc))

    return CalcResult(
        calculation_id=calculation_id,
        success=True,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
    )


@function_tool
async def search_kicad_libraries(query: str, max_results: int = 50) -> str:
    """Search KiCad libraries using ``skidl.search``.

    Args:
        query: Search string passed to ``skidl.search``.
        max_results: Maximum number of results to return (default: 50).

    Returns:
        JSON string representing a list of matching parts, ordered by relevance.
    """
    script = textwrap.dedent(
        f"""
import os
import json, io, contextlib
from skidl import *

# Set up KiCad environment variables
os.environ['KICAD5_SYMBOL_DIR'] = '/usr/share/kicad/library'
os.environ['KICAD5_FOOTPRINT_DIR'] = '/usr/share/kicad/modules'
os.environ['KISYSMOD'] = '/usr/share/kicad/modules'

set_default_tool(KICAD5)
max_results = {max_results}
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        search({query!r})
except Exception as exc:
    print(json.dumps({{"error": str(exc)}}))
    raise SystemExit()
text = buf.getvalue().splitlines()
results = []
for line in text:
    line = line.strip()
    if '.lib:' in line and '(' in line and ')' in line:
        try:
            lib_part = line.split('.lib:', 1)
            library = lib_part[0].strip()
            part_info = lib_part[1].strip()
            if '(' in part_info:
                name_desc = part_info.split('(', 1)
                name = name_desc[0].strip()
                description = name_desc[1].rstrip(')') if len(name_desc) > 1 else ''
                results.append({{"name": name, "library": library, "description": description, "footprint": None}})
        except Exception:
            continue

# Apply smart filtering and limiting
filtered_results = []
basic_components = []
specific_components = []

# Separate basic components from complex ones
for result in results:
    name = result["name"].lower()
    desc = result["description"].lower() if result["description"] else ""
    
    # Identify basic passive components that should be prioritized
    if (name in ["r", "c", "l", "r_small", "c_small", "l_small"] or 
        (len(name) <= 3 and any(word in desc for word in ["resistor", "capacitor", "inductor"]) and 
         not any(word in desc for word in ["network", "array", "pack", "dual", "quad"]))):
        basic_components.append(result)
    else:
        specific_components.append(result)

# Prioritize: basic components first, then specific ones, limit total
filtered_results = basic_components[:10] + specific_components[:max_results-len(basic_components)]
filtered_results = filtered_results[:max_results]

print(json.dumps(filtered_results))
"""
    )
    try:
        proc = await asyncio.to_thread(
            kicad_session.exec_python_with_env,
            script,
            timeout=int(settings.network_timeout),
        )
    except subprocess.TimeoutExpired as exc:
        return json.dumps({"error": "search timeout", "details": str(exc)})
    except subprocess.CalledProcessError as exc:
        error_details = {
            "subprocess_stderr": exc.stderr.strip(),
            "subprocess_stdout": exc.stdout.strip() if hasattr(exc, "stdout") else "",
            "return_code": exc.returncode,
        }
        return json.dumps({"error": "subprocess failed", "details": error_details})
    except Exception as exc:  # pragma: no cover - unexpected errors
        return json.dumps(
            {
                "error": "unexpected error",
                "details": str(exc),
                "type": type(exc).__name__,
            }
        )
    return proc.stdout.strip()


@function_tool
async def search_kicad_footprints(query: str, max_results: int = 30) -> str:
    """Search KiCad footprint libraries using ``skidl.search_footprints``.

    Args:
        query: Search string passed to ``skidl.search_footprints``.
        max_results: Maximum number of results to return (default: 30).

    Returns:
        JSON string representing a list of matching footprints.
    """
    script = textwrap.dedent(
        f"""
import os
import json, io, contextlib
from skidl import *

# Set up KiCad environment variables
os.environ['KICAD5_SYMBOL_DIR'] = '/usr/share/kicad/library'
os.environ['KICAD5_FOOTPRINT_DIR'] = '/usr/share/kicad/modules'
os.environ['KISYSMOD'] = '/usr/share/kicad/modules'

set_default_tool(KICAD5)
max_results = {max_results}
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        search_footprints({query!r})
except Exception as exc:
    print(json.dumps({{"error": str(exc)}}))
    raise SystemExit()
text = buf.getvalue().splitlines()
results = []
for line in text:
    line = line.strip()
    if '.pretty:' in line and '(' in line and ')' in line:
        try:
            lib_part = line.split('.pretty:', 1)
            library = lib_part[0].strip()
            fp_info = lib_part[1].strip()
            if '(' in fp_info:
                name_desc = fp_info.split('(', 1)
                name = name_desc[0].strip()
                description = name_desc[1].rstrip(')') if len(name_desc) > 1 else ''
                results.append({{"name": name, "library": library, "description": description}})
        except Exception:
            continue
if len(results) >= max_results:
    results = results[:max_results]
print(json.dumps(results))
"""
    )
    try:
        proc = await asyncio.to_thread(
            kicad_session.exec_python_with_env,
            script,
            timeout=int(settings.network_timeout),
        )
    except subprocess.TimeoutExpired as exc:
        return json.dumps({"error": "footprint search timeout", "details": str(exc)})
    except subprocess.CalledProcessError as exc:
        error_details = {
            "subprocess_stderr": exc.stderr.strip(),
            "subprocess_stdout": exc.stdout.strip() if hasattr(exc, "stdout") else "",
            "return_code": exc.returncode,
        }
        return json.dumps({"error": "subprocess failed", "details": error_details})
    except Exception as exc:  # pragma: no cover - unexpected errors
        return json.dumps(
            {
                "error": "unexpected error",
                "details": str(exc),
                "type": type(exc).__name__,
            }
        )
    return proc.stdout.strip()


@function_tool
async def extract_pin_details(library: str, part_name: str) -> str:
    """Return pin details by creating Part object and accessing pins directly."""
    script = textwrap.dedent(f"""
import os
import json
from skidl import *

# Set up KiCad environment variables
os.environ['KICAD5_SYMBOL_DIR'] = '/usr/share/kicad/library'
os.environ['KICAD5_FOOTPRINT_DIR'] = '/usr/share/kicad/modules'
os.environ['KISYSMOD'] = '/usr/share/kicad/modules'

set_default_tool(KICAD5)
try:
    part = Part({library!r}, {part_name!r})
    pins = []
    for pin in part.pins:
        # Convert pin_types enum to string and clean up
        func_str = str(pin.func).replace('pin_types.', '')
        pin_data = {{
            "number": str(pin.num),
            "name": str(pin.name),
            "function": func_str
        }}
        pins.append(pin_data)
    print(json.dumps(pins))
except Exception as exc:
    print(json.dumps({{"error": str(exc)}}))
""")
    try:
        proc = await asyncio.to_thread(
            kicad_session.exec_python_with_env,
            script,
            timeout=int(settings.network_timeout),
        )
    except subprocess.TimeoutExpired as exc:
        return json.dumps({"error": "pin extract timeout", "details": str(exc)})
    except subprocess.CalledProcessError as exc:
        return json.dumps({"error": "subprocess failed", "details": exc.stderr.strip()})
    except Exception as exc:  # pragma: no cover - unexpected errors
        return json.dumps({"error": str(exc)})
    return proc.stdout.strip()


def create_mcp_server() -> MCPServerSse:
    """Create MCP server connection used by all agents.

    Returns:
        MCPServerSse configured for the ``skidl_docs`` server.
    """
    url = f"{settings.mcp_url}/sse"
    timeout = settings.network_timeout
    return MCPServerSse(
        name="skidl_docs",
        params={
            "url": url,
            "timeout": timeout,
            "sse_read_timeout": timeout * 2,
        },
        cache_tools_list=True,
        client_session_timeout_seconds=timeout,
    )


async def run_runtime_check(script_path: str) -> str:
    """Execute a SKiDL script and capture runtime errors."""

    wrapper = textwrap.dedent(
        """
        import os
        import json, runpy, io, contextlib, traceback
        from skidl import *

        # Set up KiCad environment
        os.environ['KICAD5_SYMBOL_DIR'] = '/usr/share/kicad/library'
        os.environ['KICAD5_FOOTPRINT_DIR'] = '/usr/share/kicad/modules'
        os.environ['KISYSMOD'] = '/usr/share/kicad/modules'

        set_default_tool(KICAD5)
        out = io.StringIO()
        err = io.StringIO()
        success = True
        error_details = ""

        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                script_globals = runpy.run_path('/tmp/script.py', run_name='__main__')
                if 'default_circuit' in script_globals or any(
                    'Circuit' in str(type(v)) for v in script_globals.values()
                ):
                    print('Circuit object created successfully')
        except Exception as exc:
            success = False
            error_details = traceback.format_exc()
            err.write(str(exc))

        result = {
            'success': success,
            'error_details': error_details,
            'stdout': out.getvalue(),
            'stderr': err.getvalue(),
        }
        print(json.dumps(result))
        """
    )
    try:
        proc = await asyncio.to_thread(
            kicad_session.exec_erc_with_env,
            script_path,
            wrapper,
            timeout=int(settings.network_timeout),
        )
    except subprocess.TimeoutExpired as exc:
        return json.dumps(
            {"success": False, "error_details": str(exc), "stdout": "", "stderr": str(exc)}
        )
    except subprocess.CalledProcessError as exc:
        return json.dumps(
            {
                "success": False,
                "error_details": exc.stderr.strip(),
                "stdout": exc.stdout.strip(),
                "stderr": exc.stderr.strip(),
            }
        )
    except Exception as exc:  # pragma: no cover - unexpected errors
        return json.dumps(
            {"success": False, "error_details": str(exc), "stdout": "", "stderr": ""}
        )

    return proc.stdout.strip()


# Expose the runtime checker as a FunctionTool named ``run_runtime_check``.
run_runtime_check_tool = function_tool(run_runtime_check)


async def run_erc(script_path: str) -> str:
    """Run a SKiDL script and perform ERC inside Docker.

    Args:
        script_path: Path to the SKiDL script.

    Returns:
        JSON string with ``success`` flag, ``erc_passed`` status, stdout, and stderr.
        
    Note:
        SKiDL's ERC() function prints messages to stdout like:
        "2 warnings found during ERC."
        "0 errors found during ERC."
        It doesn't return a numeric error count. We parse the stdout to determine
        if ERC passed (0 errors) or failed (>0 errors).

    Example:
        >>> await run_erc("/tmp/test.py")
        '{"success": true, "erc_passed": true, "stdout": "0 errors found during ERC.\\n0 warnings found during ERC.\\n", "stderr": ""}'
    """

    wrapper = textwrap.dedent(
        """
        import os
        import json, runpy, io, contextlib, re
        from skidl import *
        
        # Set up KiCad environment variables
        os.environ['KICAD5_SYMBOL_DIR'] = '/usr/share/kicad/library'
        os.environ['KICAD5_FOOTPRINT_DIR'] = '/usr/share/kicad/modules'
        os.environ['KISYSMOD'] = '/usr/share/kicad/modules'
        
        set_default_tool(KICAD5)
        out = io.StringIO()
        err = io.StringIO()
        success = True
        erc_passed = False
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                runpy.run_path('/tmp/script.py', run_name='__main__')
                ERC()  # ERC() prints messages to stdout, doesn't return error count
                
            # Parse ERC output to determine if it passed
            erc_output = out.getvalue()
            error_match = re.search(r'(\\d+) errors found during ERC', erc_output)
            error_count = int(error_match.group(1)) if error_match else 0
            erc_passed = error_count == 0
            
        except Exception as exc:
            success = False
            err.write(str(exc))
        print(json.dumps({'success': success, 'erc_passed': erc_passed, 'stdout': out.getvalue(), 'stderr': err.getvalue()}))
        """
    )
    try:
        proc = await asyncio.to_thread(
            kicad_session.exec_erc_with_env,
            script_path,
            wrapper,
            timeout=int(settings.network_timeout),
        )
    except subprocess.TimeoutExpired as exc:
        return json.dumps(
            {"success": False, "erc_passed": False, "stdout": "", "stderr": str(exc)}
        )
    except subprocess.CalledProcessError as exc:
        return json.dumps(
            {
                "success": False,
                "erc_passed": False,
                "stdout": exc.stdout.strip(),
                "stderr": exc.stderr.strip(),
            }
        )
    except Exception as exc:  # pragma: no cover
        return json.dumps(
            {"success": False, "erc_passed": False, "stdout": "", "stderr": str(exc)}
        )

    return proc.stdout.strip()


# Expose the ERC checker as a FunctionTool named ``run_erc``.
# ``run_erc_tool`` is the variable imported by agents but the tool's
# ``name`` attribute remains "run_erc".
run_erc_tool = function_tool(run_erc)


async def execute_final_script(script_content: str, output_dir: str) -> str:
    """Execute a SKiDL script fully and return generated file paths as JSON."""

    output_dir = prepare_output_dir(output_dir)
    try:
        docker_output_dir = convert_windows_path_for_docker(output_dir)
    except ValueError as exc:
        return json.dumps({"success": False, "stderr": str(exc), "files": []})

    session = DockerSession(
        settings.kicad_image,
        f"circuitron-final-{os.getpid()}",
        volumes={output_dir: docker_output_dir},
    )
    # Create a wrapper script that handles library loading more gracefully
    wrapped_script = f"""
import os
import sys
from skidl import *

# Set up KiCad environment variables
os.environ['KICAD5_SYMBOL_DIR'] = '/usr/share/kicad/library'
os.environ['KICAD5_FOOTPRINT_DIR'] = '/usr/share/kicad/modules'
os.environ['KISYSMOD'] = '/usr/share/kicad/modules'

# Set KiCad as the default tool
set_default_tool(KICAD5)

# User script starts here
{script_content}
"""
    
    script_path = write_temp_skidl_script(wrapped_script)
    try:
        proc = await asyncio.to_thread(
            session.exec_full_script_with_env,
            script_path,
            timeout=int(settings.network_timeout),
        )
        success = proc.returncode == 0
        
        # Always attempt to copy generated files, regardless of script success
        # This ensures we capture any files that were generated before a failure
        copied_files = []
        copy_errors = []
        
        try:
            # Copy all files from the container's working directory to the output directory
            copied_files = session.copy_generated_files("/workspace/*", output_dir)
            # Get relative filenames for the response
            files = [os.path.basename(f) for f in copied_files]
        except Exception as e:
            copy_errors.append(f"File copy error: {str(e)}")
            files = []
        
        # Enhanced error reporting
        stderr_output = proc.stderr.strip()
        if copy_errors:
            stderr_output += "\n" + "\n".join(copy_errors) if stderr_output else "\n".join(copy_errors)
        
        # Add informative messages about file generation status
        if not success and files:
            stderr_output += f"\nNote: Script failed but {len(files)} file(s) were still generated and copied."
        elif not success and not files:
            stderr_output += "\nNote: Script failed and no files were generated."
        elif success and not files:
            stderr_output += "\nWarning: Script succeeded but no files were found to copy."
        
        return json.dumps(
            {
                "success": success,
                "stdout": proc.stdout.strip(),
                "stderr": stderr_output,
                "files": [os.path.join(output_dir, f) for f in files],
            }
        )
    except subprocess.TimeoutExpired as exc:
        # Even if timeout occurred, try to copy any files that might have been generated
        copied_files = []
        try:
            copied_files = session.copy_generated_files("/workspace/*", output_dir)
            files = [os.path.basename(f) for f in copied_files]
        except Exception:
            files = []
        
        timeout_msg = f"Script execution timeout: {str(exc)}"
        if files:
            timeout_msg += f"\nNote: Timeout occurred but {len(files)} file(s) were still recovered."
        
        return json.dumps({"success": False, "stderr": timeout_msg, "files": [os.path.join(output_dir, f) for f in files]})
    except subprocess.CalledProcessError as exc:
        # Even if the process failed, try to copy any files that might have been generated
        copied_files = []
        try:
            copied_files = session.copy_generated_files("/workspace/*", output_dir)
            files = [os.path.basename(f) for f in copied_files]
        except Exception:
            files = []
        
        stderr_output = exc.stderr.strip() if exc.stderr else ""
        if files:
            stderr_output += f"\nNote: Process failed but {len(files)} file(s) were still recovered." if stderr_output else f"Process failed but {len(files)} file(s) were still recovered."
        
        return json.dumps(
            {
                "success": False,
                "stdout": exc.stdout.strip() if exc.stdout else "",
                "stderr": stderr_output,
                "files": [os.path.join(output_dir, f) for f in files],
            }
        )
    finally:
        session.stop()
        try:
            os.remove(script_path)

        except OSError:
            pass

execute_final_script_tool = function_tool(execute_final_script)


@function_tool
async def get_kg_usage_guide(task_type: str) -> str:
    """Return knowledge graph query examples for common validation tasks.

    Args:
        task_type: Category of examples to return. Supported values are
            ``"class"``, ``"method"``, ``"function"``, ``"import"``,
            ``"attribute"``, ``"workflow"``, ``"schema"``, ``"advanced"``, and ``"examples"``.

    Returns:
        Guidance string containing ``query_knowledge_graph`` commands and usage patterns.

    Example:
        >>> get_kg_usage_guide("method")
        'method <name> <Class>\nmethod <name>'
    """

    task = task_type.lower()
    guides = {
        "class": (
            'query_knowledge_graph("class <ClassName>")\n'
            '# Example: query_knowledge_graph("class Part")\n'
            '# Returns: All methods and attributes for the specified class'
        ),
        "method": (
            'query_knowledge_graph("method <method> <ClassName>")\n'
            'query_knowledge_graph("method <method>")\n'
            '# Example: query_knowledge_graph("method generate_schematic Circuit")\n'
            '# Returns: Method details within specific class or across all classes'
        ),
        "function": (
            'query_knowledge_graph("function <function_name>")\n'
            '# Example: query_knowledge_graph("function generate_netlist")\n'
            '# Returns: Standalone function details including signatures and parameter details (limited to 20 results)'
        ),
        "import": (
            "query_knowledge_graph(\"query MATCH (f:Function) WHERE f.name = '<name>' "
            "RETURN f UNION MATCH (c:Class) WHERE c.name = '<name>' RETURN c\")\n"
            "# Finds both functions and classes with the given name for import validation"
        ),
        "attribute": (
            'query_knowledge_graph("class <ClassName>")\n'
            "# Check returned attributes section for the desired attribute name\n"
            "# Attributes are listed separately from methods in class query results"
        ),
        "workflow": (
            "# ESSENTIAL KNOWLEDGE GRAPH WORKFLOW:\n"
            "# 1. Always start with repository discovery:\n"
            'query_knowledge_graph("repos")\n'
            "\n# 2. Get repository structure and statistics:\n"
            'query_knowledge_graph("explore skidl")\n'
            "\n# 3. Explore classes in the repository:\n"
            'query_knowledge_graph("classes skidl")\n'
            "\n# 4. Investigate specific classes:\n"
            'query_knowledge_graph("class Part")\n'
            'query_knowledge_graph("class Net")\n'
            "\n# 5. Search for specific methods:\n"
            'query_knowledge_graph("method connect Part")\n'
            'query_knowledge_graph("method generate_netlist")\n'
            "\n# 6. Search for standalone functions:\n"
            'query_knowledge_graph("function generate_netlist")\n'
            "\n# 7. Use custom queries for complex investigations:\n"
            'query_knowledge_graph("query MATCH (c:Class)-[:HAS_METHOD]->(m:Method) WHERE m.name = \'drive\' RETURN c.name, m.name")'
        ),
        "schema": (
            "# KNOWLEDGE GRAPH SCHEMA:\n"
            "# Node Types:\n"
            "# - Repository: {name: string}\n"
            "# - File: {path: string, module_name: string}\n"
            "# - Class: {name: string, full_name: string}\n"
            "# - Method: {name: string, params_list: [string], params_detailed: [string], return_type: string, args: [string]}\n"
            "# - Function: {name: string, params_list: [string], params_detailed: [string], return_type: string, args: [string]}\n"
            "# - Attribute: {name: string, type: string}\n"
            "\n# Relationship Types:\n"
            "# - (Repository)-[:CONTAINS]->(File)\n"
            "# - (File)-[:DEFINES]->(Class)\n"
            "# - (Class)-[:HAS_METHOD]->(Method)\n"
            "# - (Class)-[:HAS_ATTRIBUTE]->(Attribute)\n"
            "# - (File)-[:DEFINES]->(Function)\n"
            "\n# Query limits: All results limited to 20 records for performance"
        ),
        "advanced": (
            "# ADVANCED KNOWLEDGE GRAPH PATTERNS:\n"
            "\n# Find all classes with specific method:\n"
            'query_knowledge_graph("query MATCH (c:Class)-[:HAS_METHOD]->(m:Method) WHERE m.name = \'run\' RETURN c.name, m.name LIMIT 10")\n'
            "\n# Find methods with specific parameter patterns:\n"
            'query_knowledge_graph("query MATCH (m:Method) WHERE ANY(param IN m.params_list WHERE param CONTAINS \'net\') RETURN m.name, m.params_list LIMIT 10")\n'
            "\n# Explore class inheritance patterns:\n"
            'query_knowledge_graph("query MATCH (c:Class) WHERE c.name CONTAINS \'Part\' RETURN c.name, c.full_name LIMIT 10")\n'
            "\n# Find all functions in a module:\n"
            'query_knowledge_graph("query MATCH (f:File)-[:DEFINES]->(func:Function) WHERE f.module_name = \'skidl\' RETURN func.name, func.params_list LIMIT 10")'
        ),
        "examples": (
            "# COMPLETE KNOWLEDGE GRAPH EXAMPLE WORKFLOW:\n"
            'query_knowledge_graph("repos")  # Start here - discover available repositories\n'
            'query_knowledge_graph("explore skidl")  # Get SKiDL repo statistics\n'
            'query_knowledge_graph("classes skidl")  # List classes in SKiDL\n'
            'query_knowledge_graph("class Part")  # Investigate Part class\n'
            'query_knowledge_graph("method connect Part")  # Find connect method in Part\n'
            'query_knowledge_graph("method generate_netlist")  # Find generate_netlist method\n'
            'query_knowledge_graph("function generate_netlist")  # Find generate_netlist function\n'
            'query_knowledge_graph("query MATCH (f:Function) WHERE f.name = \'generate_netlist\' RETURN f")  # Custom query for functions'
        ),
    }

    return guides.get(task, "Task type not recognized. Available types: class, method, function, import, attribute, workflow, schema, advanced, examples")


