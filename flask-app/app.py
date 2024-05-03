from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, session
from static.scripts.phi_3_assistant import PhiChatState
from static.scripts.gpt_4_assistant import GptChatState

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fda401cd2d098d192cc24dc19021a6e4ccb1fb895e5d5e75'

chat_messages = []
def store_message(msg):
    chat_messages.append(msg)


@app.route('/assistant/generateResponse', methods=['POST','GET'])
def new_query():
    id = 202
    
  
    newQuery = request.json['prompt']
    parameters = {'temperature': request.json['temperature'], 'max_new_tokens': request.json['max_new_tokens'], 'top_p': request.json['top_p'], 'deployment': request.json['deployment']}
    print(f"inside new_query({parameters})\n\n")
    
    if request.json['deployment'].find('gpt-4') != -1:
        agent = GptChatState()
    else:
        agent = PhiChatState()
        
    
    store_message(dict(
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

        store_message(dict(
            id = id,
            content = result,
            contentType = newQuery['contentType'],
            senderId = newQuery['senderId'],
            direction = 'incoming',
        ))

        
    #print(f"inside new_query({newQuery} {request.json['useMT']})")

    #store_message.append(jsonify({"chat": f"{result}", "id": id}))
    return  jsonify(messages=chat_messages)


if __name__ == '__main__':
    app.run()
    
