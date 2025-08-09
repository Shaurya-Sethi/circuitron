# Circuitron Setup Guide

This is a dedicated guide to getting the dependencies for the project set up.

## Table of Contents

1. [Docker Setup](#docker-setup)
2. [MCP Server Setup](#mcp-server-setup)
3. [Setting up AI Assistant for Knowledge Base Population](#setting-up-ai-assistant-for-knowledge-base-population)
4. [Populating Knowledge Bases](#populating-knowledge-bases)
5. [Additional Notes on OpenAI API](#additional-notes-on-openai-api)

## Docker Setup

First make sure you have docker installed on your machine.

Then run the following commands to pull the required docker images:

```bash
docker pull ghcr.io/shaurya-sethi/circuitron-kicad:latest
docker pull ghcr.io/shaurya-sethi/circuitron-mcp:latest
docker pull python:3.12-slim
```

## MCP Server Setup

Next, you'll need to follow the following steps to set up the MCP server:

### Step 1: Get OpenAI API Key

First obtain an OpenAI API key from https://platform.openai.com/signup.

**Note:** You will need to top up your account with some credits to use the API.

### Step 2: Create Supabase Account and Project

Create a supabase account at https://supabase.com/

- Go to your dashboard and create a new project. (Follow the instructions on the website - they will guide you through the process and are very straightforward.)
- Then, go to the project settings → API Keys → service_role key and copy it.
- In the same project settings, under the CONFIGURATION tab, go to Data API → And copy your project URL.

**Important:** Once this is done, please go to the "SQL Editor" and then paste the contents of the `setup_supabase.sql` file from the repository into the SQL editor and run it. This will create the required tables in your Supabase database.

### Step 3: Create Neo4j Database


Create a neo4j database on Neo4j Aura cloud service https://neo4j.com/cloud/aura/

(Or you can use a local Neo4j instance, but the cloud service is recommended for ease of use if you are unfamiliar with neo4j and don't already use it locally.)

**If you are using a local Neo4j instance, use this exact URI for the connection:**

```
bolt://host.docker.internal:7687
```

- Once you have created a database, go to the database settings and copy the connection URI, username, and password.

### Step 4: Create mcp.env File

Create a mcp.env file in the root directory of the project and add the following environment variables:

```env
TRANSPORT=sse
HOST=0.0.0.0
PORT=8051
OPENAI_API_KEY=<your OpenAI API key>
MODEL_CHOICE=gpt-4.1-nano
USE_CONTEXTUAL_EMBEDDINGS=true
USE_HYBRID_SEARCH=true
USE_AGENTIC_RAG=true
USE_RERANKING=true
USE_KNOWLEDGE_GRAPH=true
LLM_MAX_CONCURRENCY=2
LLM_REQUEST_DELAY=0.5
SUPABASE_URL=<your Supabase project URL>
SUPABASE_SERVICE_KEY=<your Supabase service_role key>
NEO4J_URI=<your Neo4j URI>
NEO4J_USER=<your Neo4j username>
NEO4J_PASSWORD=<your Neo4j password>
```

Here, you will need to replace the placeholders with the actual values you obtained in the previous steps. Don't change other values.

### Step 5: Run the MCP Server

Now you can run the MCP server using the following command:

```bash
docker run --env-file mcp.env -p 8051:8051 ghcr.io/shaurya-sethi/circuitron-mcp:latest
```

To confirm that the server is running, you can open logs in docker desktop and check for the following:

```
2025-08-01 11:54:15
INFO: Started server process [1]
2025-08-01 11:54:15
INFO: Waiting for application startup.
2025-08-01 11:54:15
INFO: Application startup complete.
2025-08-01 11:54:15
INFO: Uvicorn running on http://0.0.0.0:8051⁠ (Press CTRL+C to quit)
2025-08-01 11:54:18
INFO: 172.17.0.1:48912 - "GET /sse HTTP/1.1" 200 OK
```

## Setting up AI Assistant for Knowledge Base Population

Now let's add this mcp server to your favourite coding agent so it can assist you with setting up the knowledge bases for circuitron.

### For (VSCode) Github Copilot:

- Open the chat sidebar by clicking on the Copilot icon in the Activity Bar on the side of the window.
- Select **Configure Tools → (Scroll all the way down) Add More Tools… → Add MCP Server → HTTP** and enter the URL `http://localhost:8051/sse`. That's it, you should now see the MCP server and its tools listed under the same Configure Tools menu. (Just make sure that they are enabled by checking the checkboxes next to them.)

### For Cline

- Open the Cline chat interface, and click on the icon at the bottom that says "Manage MCP Servers".
- In this, click on the gear icon at the top right to open settings.
- Go to Remote Servers and then add a name for the server (e.g., "Circuitron MCP") and the URL `http://localhost:8051/sse`.
- Click on Add Server. Now Cline should be able to make use of this MCP server to assist you with setting up the knowledge bases for circuitron.

**Note:** With Cline, you can make use of the following **free** model providers' apis: 
- Gemini api is free to use and you just need to get the key from https://aistudio.google.com/apikey
  - For gemini use gemini 2.5 pro or flash
- The Mistral API also has a free tier which you can use by signing up at https://mistral.ai/products/la-plateforme → "Try the API"
  - for mistral use devstral medium

This is just general advice and you can use these apis for free with cline while coding your own projects :)

### For Other IDEs/Coding Agents

Both these are popular free extensions for VSCode, which itself is a popular IDE that most people use. If you are using a different IDE/coding agent (like cursor, gemini-cli, claude code, etc) please refer to their documentation on how to add a custom MCP server. The URL will be the same as above: `http://localhost:8051/sse`. (This should be easy to do but if you're unfamiliar with anything, please just install cline or copilot and follow the above steps, as they are very straightforward and easy to use.)

## Populating Knowledge Bases

Now we can ask our agent to help us set up the knowledge bases for circuitron.

### Step 1: Crawl SKiDL Documentation

Instruct the agent to crawl `https://devbisme.github.io/skidl/` to build the SKiDL documentation corpus.

The agent will use the MCP tool `smart_crawl_url` to parse the documentation and create a knowledge base for SKiDL. (This may take just a few minutes so please be patient.)

**Note:** Sometimes, using models like GPT 4.1 in model selection in copilot may cause the agent to not use the MCP tool. If this happens, try using a different model like claude 4 or be more explicit in your instructions to the agent, such as "Use the MCP tool `smart_crawl_url` to parse the URL `https://devbisme.github.io/skidl/` and create a knowledge base for SKiDL documentation." This should help the agent understand that it needs to use the MCP tool for this task.

At any given point, the agent should NOT be making custom crawling scripts. Please post any issues you face with this in Discussions or create an issue on the GitHub repository.

### Step 2: Parse GitHub Repository

Next, instruct it to parse the GitHub repository `https://github.com/devbisme/skidl` to populate the knowledge graph. For this, the agent should use the `parse_github_repository` MCP tool.

This concludes the dependencies setup for Circuitron. Now you can start using Circuitron as mentioned in the README.md file, but just ensure that the MCP server is running in the background.

## Additional Notes on OpenAI API

### Organization Verification

You'll need to do organization verification to be able to use the reasoning models like o4-mini (which is what circuitron makes use of by default). This is their policy to prevent the use of their model's responses to train other models in a teacher-student way.

If you don't want to do this, you will need to navigate to `settings.py` in the repository and change the default model to gpt-4.1 or gpt-4.1-mini like so:

```python
code_generation_model: str = field(default="gpt-4.1")
```

**Note:** This might degrade overall performance of the system if you use gpt-4.1-mini or nano, OR it might significantly increase costs if you use gpt-4.1 and you might even hit rate limits if you are on tier-1 (5 usd worth of credits).

Hence, both to save costs and to ensure best performance, I recommend you do the organization verification and use o4-mini as the default model.

Please follow this guide for the same: https://help.openai.com/en/articles/10910291-api-organization-verification

It won't take more than a few minutes.

### Cost Optimization

Lastly, you might wanna consider checking the option to share your data (the requests and responses when you use their api) as it will grant a lot of free daily usage. This allowed me to limit the entire cost of development to under 3 dollars (It's been 2 months and I still haven't been able to use the full 5 usd worth of creds).

---

Hope this helps you get started with Circuitron! If you have any questions or run into issues, feel free to reach out in the Discussions section of the GitHub repository.
