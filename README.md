# Getting Started with Azure AI Phi-3 Chat API, GPT-4 Assistants API and Azure Translator

## Requirements
- VS code must be installed
- [recommended] python -m venv ./my_venv
- node.js and npm
- Following is best to be run from VS Code terminal after you select the project folder. 
  - npm install --save-dev react-dev-utils
  - npm install @mui/material @emotion/react @emotion/styled @chatscope/chat-ui-kit-react
  - npm install react-select
  - pip install openai
  - pip install requests python-dotenv json  ssl  urllib3
  
## .env must be added to the root directory. Content (without sub-bullet):
- MT_REGION=<resource region, e.g., eastus>
- AAI_1KEYV2=<resource key, e.g., a1b1234567890123456789ca123456c7>
- MT_URI=https://resource-name.cognitiveservices.azure.com/
- MT_BASE_URL=https://resource-name.cognitiveservices.azure.com/translator/text/v3.0
- PHI_3_URL=phi-3-model-deployment-endpoint
- PHI_3_KEY=phi-3-deployment-key
- AOAI_URI=https://resource-namet-pilot.openai.azure.com/
- AOAI_BASE_URL=https://resource-name.openai.azure.com/openai
- AOAI_KEY=<resource key, e.g., a1b1234567890123456789ca123456c7>
- AOAI_VERSION=<model-version, e.g., 2024-02-15-preview>
- AOAI_GPT_DEPLOYMENT=<gpt-4-deployment-name>
- AOAI_GPT_ASSISTANT=<assistant-id, e.g., asst_9v7TP8yAUeFSgL345npccEmr>

## Launch the app
1. Start VS code and open the app folder from "File" tab
2. Create 2 terminals
3. In terminal 1: "cd .\flask-app\" and start flask "python -m flask run"
4. In termina 2: start npm "npm start"
   - You should see:
   ![Landing page](flask-app/static/image/Landing-page.png)

#### You can:
1. Type query in Ask anything.
2. Use slider switch for Azure AI Translator.
3. Select deployment model (phi-3-mini-128k-instruct-2 as an example for chat and GPT for assistants).
4. Change query paramters.
5. Clear chat.
