<!--
---
name: Python AI Agent Frameworks Demos
description: Collection of Python examples for popular AI agent frameworks using GitHub Models or Azure OpenAI.
languages:
- python
products:
- azure-openai
- azure
page_type: sample
urlFragment: python-ai-agent-frameworks-demos
---
-->
# Python AI Agent Frameworks Demos

[![Open in GitHub Codespaces](https://img.shields.io/static/v1?style=for-the-badge&label=GitHub+Codespaces&message=Open&color=brightgreen&logo=github)](https://codespaces.new/Azure-Samples/python-ai-agent-frameworks-demos)
[![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/Azure-Samples/python-ai-agent-frameworks-demos)

This repository provides examples of many popular Python AI agent frameworks using LLMs from [GitHub Models](https://github.com/marketplace/models). Those models are free to use for anyone with a GitHub account, up to a [daily rate limit](https://docs.github.com/github-models/prototyping-with-ai-models#rate-limits).

* [Getting started](#getting-started)
  * [GitHub Codespaces](#github-codespaces)
  * [VS Code Dev Containers](#vs-code-dev-containers)
  * [Local environment](#local-environment)
* [Running the Python examples](#running-the-python-examples)
* [Guidance](#guidance)
  * [Costs](#costs)
  * [Security guidelines](#security-guidelines)
* [Resources](#resources)

## Getting started

You have a few options for getting started with this repository.
The quickest way to get started is GitHub Codespaces, since it will setup everything for you, but you can also [set it up locally](#local-environment).

### GitHub Codespaces

You can run this repository virtually by using GitHub Codespaces. The button will open a web-based VS Code instance in your browser:

1. Open the repository (this may take several minutes):

    [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Azure-Samples/python-ai-agent-frameworks-demos)

2. Open a terminal window
3. Continue with the steps to run the examples

### VS Code Dev Containers

A related option is VS Code Dev Containers, which will open the project in your local VS Code using the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers):

1. Start Docker Desktop (install it if not already installed)
2. Open the project:

    [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/Azure-Samples/python-ai-agent-frameworks-demos)

3. In the VS Code window that opens, once the project files show up (this may take several minutes), open a terminal window.
4. Continue with the steps to run the examples

### Local environment

1. Make sure the following tools are installed:

    * [Python 3.10+](https://www.python.org/downloads/)
    * Git

2. Clone the repository:

    ```shell
    git clone https://github.com/Azure-Samples/python-ai-agent-frameworks-demos
    cd python-ai-agents-demos
    ```

3. Set up a virtual environment:

    ```shell
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4. Install the requirements:

    ```shell
    pip install -r requirements.txt
    ```

## Running the Python examples

You can run the examples in this repository by executing the scripts in the `examples` directory. Each script demonstrates a different AI agent pattern or framework.

| Example | Description |
| ------- | ----------- |
| fashion_content_agent | A Streamlit application that processes fashion images, generates marketing content using AI, and stores results in Google Sheets. |
| autogen_basic.py | Uses AutoGen to build a single agent. |
| autogen_tools.py | Uses AutoGen to build a single agent with tools. |
| autogen_magenticone.py | Uses AutoGen with the MagenticOne orchestrator agent for travel planning. |
| autogen_swarm.py | Uses AutoGen with the Swarm orchestrator agent for flight refunding requests. |
| langgraph.py | Uses LangGraph to build an agent with a StateGraph to play songs. |
| llamaindex.py | Uses LlamaIndex to build a ReAct agent for RAG on multiple indexes. |
| openai_agents_basic.py | Uses the OpenAI Agents framework to build a single agent. |
| openai_agents.py | Uses the OpenAI Agents framework to handoff between several agents with tools. |
| openai_functioncalling.py | Uses OpenAI Function Calling to call functions based on LLM output. |
| pydanticai.py | Uses PydanticAI to build a two-agent sequential workflow for flight planning. |
| semantickernel.py | Uses Semantic Kernel to build a writer/editor two-agent workflow. |
| smolagents_codeagent.py | Uses SmolAgents to build a question-answering agent that can search the web and run code. |

## Configuring GitHub Models

If you open this repository in GitHub Codespaces, you can run the scripts for free using GitHub Models without any additional steps, as your `GITHUB_TOKEN` is already configured in the Codespaces environment.

If you want to run the scripts locally, you need to set up the `GITHUB_TOKEN` environment variable with a GitHub personal access token (PAT). You can create a PAT by following these steps:

1. Go to your GitHub account settings.
2. Click on "Developer settings" in the left sidebar.
3. Click on "Personal access tokens" in the left sidebar.
4. Click on "Tokens (classic)" or "Fine-grained tokens" depending on your preference.
5. Click on "Generate new token".
6. Give your token a name and select the scopes you want to grant. For this project, you don't need any specific scopes.
7. Click on "Generate token".
8. Copy the generated token.
9. Set the `GITHUB_TOKEN` environment variable in your terminal or IDE:

    ```shell
    export GITHUB_TOKEN=your_personal_access_token
    ```

10. Optionally, you can use a model other than "gpt-4o" by setting the `GITHUB_MODEL` environment variable. Use a model that supports function calling, such as: `gpt-4o`, `gpt-4o-mini`, `o3-mini`, `AI21-Jamba-1.5-Large`, `AI21-Jamba-1.5-Mini`, `Codestral-2501`, `Cohere-command-r`, `Ministral-3B`, `Mistral-Large-2411`, `Mistral-Nemo`, `Mistral-small`

## Provisioning Azure AI resources

You can run all examples in this repository using GitHub Models. If you want to run the examples using models from Azure OpenAI instead, you need to provision the Azure AI resources, which will incur costs.

This project includes infrastructure as code (IaC) to provision Azure OpenAI deployments of "gpt-4o" and "text-embedding-3-large". The IaC is defined in the `infra` directory and uses the Azure Developer CLI to provision the resources.

1. Make sure the [Azure Developer CLI (azd)](https://aka.ms/install-azd) is installed.

2. Login to Azure:

    ```shell
    azd auth login
    ```

    For GitHub Codespaces users, if the previous command fails, try:

   ```shell
    azd auth login --use-device-code
    ```

3. Provision the OpenAI account:

    ```shell
    azd provision
    ```

    It will prompt you to provide an `azd` environment name (like "agents-demos"), select a subscription from your Azure account, and select a location. Then it will provision the resources in your account.

4. Once the resources are provisioned, you should now see a local `.env` file with all the environment variables needed to run the scripts.
5. To delete the resources, run:

    ```shell
    azd down
    ```

## Fashion Content Agent

A Streamlit-based application that automates the generation of marketing content for fashion images using AI vision analysis and content generation.

## Features

- Process up to 3 fashion images simultaneously with batch processing
- Generate comprehensive marketing content:
  - Product titles
  - Detailed descriptions
  - Marketing captions
  - SEO-friendly hashtags
  - Accessibility-focused alt text
- Intelligent duplicate detection to prevent redundant processing
- Automatic Google Sheets integration with email sharing
- Robust error handling and logging system
- Support for various image sources (including Google Drive)
- Comprehensive test suite for reliability

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- Google Cloud account with Sheets API enabled
- Google service account credentials

### Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd fashion-content-agent
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install test dependencies (optional):
   ```bash
   pip install -r tests/requirements-test.txt
   ```

### Configuration

1. Set up environment variables:
   ```bash
   export GOOGLE_CREDENTIALS_FILE="path/to/credentials.json"
   export GOOGLE_SHARE_EMAIL="default@example.com"  # Optional
   ```

2. Configure logging (optional):
   - Default log file: `app.log`
   - Log level: INFO
   - Formats: Timestamp, Level, Message

## Usage

1. Start the application:
   ```bash
   streamlit run app.py
   ```

2. In the web interface:
   - Enter up to 3 image URLs (one per line)
   - Customize the Google Sheet name (optional)
   - Provide your email for sheet access
   - Click "Process Images"

3. The application will:
   - Validate all URLs
   - Check for duplicates
   - Process valid images
   - Generate content
   - Save to Google Sheets
   - Share the sheet with your email

## Testing

The project includes a comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/unit/ -v

# Run specific test categories
python -m pytest tests/unit/test_batch_processing.py
python -m pytest tests/unit/test_email_notification.py
python -m pytest tests/unit/test_logging.py
python -m pytest tests/unit/test_duplicate_detection.py
```

Test coverage includes:
- Batch processing functionality
- Email notification system
- Logging implementation
- Duplicate detection
- Error handling
- Cache management

## Error Handling

The application includes robust error handling for:
- Invalid image URLs
- Inaccessible images
- Google Sheets API errors
- Email sharing issues
- Duplicate images
- Batch processing failures

## Logging

Comprehensive logging system that tracks:
- Operation progress
- Error occurrences
- Performance metrics
- User interactions
- API responses

## Security

- Secure credential management
- Email validation
- Access control for Google Sheets
- Protected image processing
- Secure cache management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite
5. Submit a pull request

## License

[License details]

## Contact

[Contact information]

## Resources

* [AutoGen Documentation](https://microsoft.github.io/autogen/)
* [LangGraph Documentation](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
* [LlamaIndex Documentation](https://docs.llamaindex.ai/en/latest/)
* [OpenAI Agents Documentation](https://openai.github.io/openai-agents-python/)
* [OpenAI Function Calling Documentation](https://platform.openai.com/docs/guides/function-calling?api-mode=chat)
* [PydanticAI Documentation](https://ai.pydantic.dev/multi-agent-applications/)
* [Semantic Kernel Documentation](https://learn.microsoft.com/semantic-kernel/overview/)
* [SmolAgents Documentation](https://huggingface.co/docs/smolagents/index)
