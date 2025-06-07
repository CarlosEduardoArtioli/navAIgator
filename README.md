<img src="./assets/web-ui.png" alt="Browser Use Web UI" width="full"/>

<br/>

[![GitHub stars](https://img.shields.io/github/stars/browser-use/web-ui?style=social)](https://github.com/browser-use/web-ui/stargazers)
[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)
[![Documentation](https://img.shields.io/badge/Documentation-📕-blue)](https://docs.browser-use.com)
[![WarmShao](https://img.shields.io/twitter/follow/warmshao?style=social)](https://x.com/warmshao)

This project builds upon the foundation of the [browser-use](https://github.com/browser-use/browser-use), which is designed to make websites accessible for AI agents.

We would like to officially thank [WarmShao](https://github.com/warmshao) for his contribution to this project.

**WebUI:** is built on Gradio and supports most of `browser-use` functionalities. This UI is designed to be user-friendly and enables easy interaction with the browser agent.

**Expanded LLM Support:** We've integrated support for various Large Language Models (LLMs), including: Google, OpenAI, Azure OpenAI, Anthropic, DeepSeek, Ollama etc. And we plan to add support for even more models in the future.

**Custom Browser Support:** You can use your own browser with our tool, eliminating the need to re-login to sites or deal with other authentication challenges. This feature also supports high-definition screen recording.

**Persistent Browser Sessions:** You can choose to keep the browser window open between AI tasks, allowing you to see the complete history and state of AI interactions.

**Azure DevOps Integration:** Seamlessly integrate with Azure DevOps to automatically create work items with execution results, attachments, and link them to parent user stories for comprehensive test automation tracking.

**Laminar Observability:** Built-in integration with Laminar for comprehensive AI observability, including automatic tracing of LLM calls, browser actions, performance metrics, and task execution analytics.

<video src="https://github.com/user-attachments/assets/56bc7080-f2e3-4367-af22-6bf2245ff6cb" controls="controls">Your browser does not support playing this video!</video>

## Installation Guide

### Option 1: Local Installation

Read the [quickstart guide](https://docs.browser-use.com/quickstart#prepare-the-environment) or follow the steps below to get started.

#### Step 1: Clone the Repository
```bash
git clone https://github.com/browser-use/web-ui.git
cd web-ui
```

#### Step 2: Set Up Python Environment
We recommend using [uv](https://docs.astral.sh/uv/) for managing the Python environment.

Using uv (recommended):
```bash
uv venv --python 3.11
```

Activate the virtual environment:
- Windows (Command Prompt):
```cmd
.venv\Scripts\activate
```
- Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```
- macOS/Linux:
```bash
source .venv/bin/activate
```

#### Step 3: Install Dependencies
Install Python packages:
```bash
uv pip install -r requirements.txt
```

Install Browsers in Patchright. 
```bash
patchright install --with-deps
```
Or you can install specific browsers by running:
```bash
patchright install chromium --with-deps
```

#### Step 4: Configure Environment
1. Create a copy of the example environment file:
- Windows (Command Prompt):
```bash
copy .env.example .env
```
- macOS/Linux/Windows (PowerShell):
```bash
cp .env.example .env
```
2. Open `.env` in your preferred text editor and add your API keys and other settings

#### Step 5: Enjoy the web-ui
1.  **Run the WebUI:**
    ```bash
    python webui.py --ip 127.0.0.1 --port 7788
    ```
2. **Access the WebUI:** Open your web browser and navigate to `http://127.0.0.1:7788`.
3. **Using Your Own Browser(Optional):**
    - Set `BROWSER_PATH` to the executable path of your browser and `BROWSER_USER_DATA` to the user data directory of your browser. Leave `BROWSER_USER_DATA` empty if you want to use local user data.
      - Windows
        ```env
         BROWSER_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
         BROWSER_USER_DATA="C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data"
        ```
        > Note: Replace `YourUsername` with your actual Windows username for Windows systems.
      - Mac
        ```env
         BROWSER_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
         BROWSER_USER_DATA="/Users/YourUsername/Library/Application Support/Google/Chrome"
        ```
    - Close all Chrome windows
    - Open the WebUI in a non-Chrome browser, such as Firefox or Edge. This is important because the persistent browser context will use the Chrome data when running the agent.
    - Check the "Use Own Browser" option within the Browser Settings.

### Option 2: Docker Installation

#### Prerequisites
- Docker and Docker Compose installed
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (For Windows/macOS)
  - [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) (For Linux)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/browser-use/web-ui.git
cd web-ui
```

#### Step 2: Configure Environment
1. Create a copy of the example environment file:
- Windows (Command Prompt):
```bash
copy .env.example .env
```
- macOS/Linux/Windows (PowerShell):
```bash
cp .env.example .env
```
2. Open `.env` in your preferred text editor and add your API keys and other settings

#### Step 3: Docker Build and Run
```bash
docker compose up --build
```
For ARM64 systems (e.g., Apple Silicon Macs), please run follow command:
```bash
TARGETPLATFORM=linux/arm64 docker compose up --build
```

#### Step 4: Enjoy the web-ui and vnc
- Web-UI: Open `http://localhost:7788` in your browser
  - VNC Viewer (for watching browser interactions): Open `http://localhost:6080/vnc.html`
  - Default VNC password: "youvncpassword"
  - Can be changed by setting `VNC_PASSWORD` in your `.env` file

## Azure DevOps Integration

The WebUI includes built-in Azure DevOps integration that automatically creates work items with detailed execution results, making it perfect for test automation and task tracking.

### Features

✅ **Automatic Work Item Creation** - Creates work items with execution results
✅ **File Attachments** - Uploads execution output, chat history, and screen recordings  
✅ **Parent Linking** - Links created work items to parent user stories
✅ **Connection Testing** - Validates Azure DevOps connectivity
✅ **User Story Retrieval** - Fetches and displays user story information

### Setup

1. **Configure Azure DevOps Settings** in the WebUI:
   - **Organization**: Your Azure DevOps organization name
   - **Project**: Your project name  
   - **Personal Access Token (PAT)**: Token with Work Items (read/write) permissions
   - **Parent Work Item ID** (optional): ID to link created work items as children

2. **Generate Personal Access Token**:
   - Go to Azure DevOps → User Settings → Personal Access Tokens
   - Create new token with "Work Items (read and write)" scope
   - Copy the token and paste it in the WebUI

3. **Enable Auto-Send**: Toggle the "Auto-send results to Azure DevOps" option

### Usage

Once configured, the integration works automatically:

1. **Execute any agent task** in the Browser Use Agent tab
2. **Work item is created** automatically upon task completion  
3. **Attachments are uploaded**:
   - `agent_output.txt` - Complete execution output and summary
   - `agent_history.json` - Full chat history and execution data  
   - `execution_recording.gif` - Screen recording (if available)
4. **Work item is linked** to the specified parent user story

### Supported Work Item Types

The integration automatically tries different work item types based on your Azure DevOps project template:
- Task (preferred)
- User Story  
- Bug
- Issue

### Manual Operations

You can also use the Azure DevOps tab for manual operations:
- **Test Connection** - Verify your Azure DevOps settings

## Laminar Observability Integration

The WebUI includes built-in Laminar integration for comprehensive AI observability and monitoring.

### Features

✅ **Automatic LLM Tracing** - Traces all LLM calls automatically  
✅ **Browser Action Monitoring** - Tracks all browser interactions and actions  
✅ **Performance Metrics** - Monitors execution time, success rates, and errors  
✅ **Task Analytics** - Detailed analytics of agent task execution  
✅ **Real-time Monitoring** - Live monitoring dashboard in the WebUI  
✅ **Self-hosting Support** - Works with both cloud and self-hosted Laminar instances

### Setup

1. **Configure Laminar Settings** in the Laminar tab:
   - **Project API Key**: Your Laminar project API key
   - **Base URL**: Laminar server URL (default: https://api.lmnr.ai)
   - **Enable/Disable**: Toggle Laminar integration

2. **Get Project API Key**:
   - Visit [lmnr.ai](https://www.lmnr.ai/)
   - Create an account and project
   - Go to Settings → API Keys
   - Generate a new API key

3. **Environment Configuration** (optional):
   ```env
   LMNR_PROJECT_API_KEY=your_api_key_here
   LMNR_BASE_URL=https://api.lmnr.ai
   LMNR_ENABLED=true
   ```

### Usage

Once configured, Laminar automatically tracks:

1. **Agent Task Execution** - Complete task lifecycle with timing and outcomes
2. **Browser Actions** - All clicks, typing, navigation with success/failure status  
3. **LLM Interactions** - Automatic tracing of all language model calls
4. **Performance Metrics** - Execution time, token usage, error rates
5. **Custom Events** - Task completion, cancellation, and error events

### Monitored Metrics

- **Task Execution Time** - How long each agent task takes
- **Success/Failure Rates** - Task completion statistics  
- **Browser Action Types** - Distribution of browser interactions
- **Error Analysis** - Detailed error tracking and categorization
- **Token Usage** - LLM token consumption tracking

### Self-hosting Laminar

For self-hosted Laminar instances:
1. Set up Laminar using their [documentation](https://docs.lmnr.ai/)
2. Update the Base URL in the Laminar tab to your instance
3. Ensure your API key is configured for your self-hosted instance
- **Retrieve User Story** - Fetch and display user story details by ID

## Changelog
- [x] **2025/01/27:** Added comprehensive Azure DevOps integration with automatic work item creation, file attachments, parent linking, and connection testing for seamless test automation workflow.
- [x] **2025/01/26:** Thanks to @vvincent1234. Now browser-use-webui can combine with DeepSeek-r1 to engage in deep thinking!
- [x] **2025/01/10:** Thanks to @casistack. Now we have Docker Setup option and also Support keep browser open between tasks.[Video tutorial demo](https://github.com/browser-use/web-ui/issues/1#issuecomment-2582511750).
- [x] **2025/01/06:** Thanks to @richard-devbot. A New and Well-Designed WebUI is released. [Video tutorial demo](https://github.com/warmshao/browser-use-webui/issues/1#issuecomment-2573393113).
