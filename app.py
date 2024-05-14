
import copy
import json
import os
import logging
import uuid
from dotenv import load_dotenv
import httpx
from quart import (
    Blueprint,
    Quart,
    jsonify,
    make_response,
    request,
    send_from_directory,
    render_template,
)

# from openai import AsyncAzureOpenAI
# from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from backend.phi_3_assistant import PhiChatState
from backend.gpt_4_assistant import GptChatState

bp = Blueprint("routes", __name__, static_folder="static", template_folder="static")
load_dotenv()

def create_app():
    app = Quart(__name__)
    app.register_blueprint(bp)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    return app

chatMessages = []
class HandleMessages:
    def storeMessage(self, msg):
        chatMessages.append(msg)

    def clearMessages(self):
        chatMessages.clear()

    def getMessages(self):
        return chatMessages

@bp.route('/ping', methods=['GET'])
async def pingMe():
     return  jsonify("I am alive!")

@bp.route('/clearChat', methods=['POST','GET'])
async def clearMe():
     clearMsg = HandleMessages()
     clearMsg.clearMessages()
     return  jsonify(messages=clearMsg.getMessages())

@bp.route('/assistant/generateResponse', methods=['POST','GET'])
async def new_query():
    id = 202
    
    handelMsgs = HandleMessages()

    newQuery = await request.get_json() #['prompt']
    print(f"inside new_query({newQuery})\n\n")
    prompt = newQuery['prompt']
    parameters = {'temperature': newQuery['temperature'], 'max_new_tokens': newQuery['max_new_tokens'], 
                  'top_p': newQuery['top_p'], 'deployment': newQuery['deployment']}
    print(f"inside new_query({parameters})\n\n")
    
    if newQuery['deployment'].find('gpt-4') != -1:
        agent = GptChatState()
    else:
        agent = PhiChatState()
        
    
    handelMsgs.storeMessage(dict(
        id = '201',
        content = prompt['content'],
        contentType = prompt['contentType'],
        senderId = prompt['senderId'],
        direction = prompt['direction'],
    ))
    
    if len(prompt['content']) != 0:
    # time.sleep(10)
        print(f"inside new_query({newQuery} {newQuery['useMT']})")
        result = agent.process_prompt("JohnDoe", "user_1", prompt['content'], newQuery['useMT'], parameters)

        handelMsgs.storeMessage(dict(
            id = id,
            content = result,
            contentType = prompt['contentType'],
            senderId = prompt['senderId'],
            direction = 'incoming',
        ))

        
    #print(f"inside new_query({newQuery} {request.json['useMT']})")

    #store_message.append(jsonify({"chat": f"{result}", "id": id}))
    return  jsonify(messages=handelMsgs.getMessages())


app = create_app()
