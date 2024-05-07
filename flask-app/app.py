from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, session
from static.scripts.phi_3_assistant import PhiChatState
from static.scripts.gpt_4_assistant import GptChatState

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fda401cd2d098d192cc24dc19021a6e4ccb1fb895e5d5e75'

chatMessages = []
class HandleMessages:
    def storeMessage(self, msg):
        chatMessages.append(msg)

    def clearMessages(self):
        chatMessages.clear()

    def getMessages(self):
        return chatMessages

@app.route('/ping', methods=['GET'])
def pingMe():
     return  jsonify("I am alive!")

@app.route('/clearChat', methods=['POST','GET'])
def clearMe():
     clearMsg = HandleMessages()
     clearMsg.clearMessages()
     return  jsonify(messages=clearMsg.getMessages())

@app.route('/assistant/generateResponse', methods=['POST','GET'])
def new_query():
    id = 202
    
    handelMsgs = HandleMessages()

    newQuery = request.json['prompt']
    parameters = {'temperature': request.json['temperature'], 'max_new_tokens': request.json['max_new_tokens'], 
                  'top_p': request.json['top_p'], 'deployment': request.json['deployment']}
    print(f"inside new_query({parameters})\n\n")
    
    if request.json['deployment'].find('gpt-4') != -1:
        agent = GptChatState()
    else:
        agent = PhiChatState()
        
    
    handelMsgs.storeMessage(dict(
        id = '201',
        content = newQuery['content'],
        contentType = newQuery['contentType'],
        senderId = newQuery['senderId'],
        direction = newQuery['direction'],
    ))
    
    if len(newQuery['content']) != 0:
    # time.sleep(10)
        print(f"inside new_query({newQuery} {request.json['useMT']})")
        result = agent.process_prompt("JohnDoe", "user_1", newQuery['content'], request.json['useMT'], parameters)

        handelMsgs.storeMessage(dict(
            id = id,
            content = result,
            contentType = newQuery['contentType'],
            senderId = newQuery['senderId'],
            direction = 'incoming',
        ))

        
    #print(f"inside new_query({newQuery} {request.json['useMT']})")

    #store_message.append(jsonify({"chat": f"{result}", "id": id}))
    return  jsonify(messages=handelMsgs.getMessages())


if __name__ == '__main__':
    app.run()
    
