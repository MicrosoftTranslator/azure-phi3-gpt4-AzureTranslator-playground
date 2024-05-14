import os
import requests
# from dotenv import load_dotenv
import io
import time
from datetime import datetime
import ssl

from openai import AzureOpenAI
from openai.types import FileObject
from openai.types.beta import Thread
from openai.types.beta.threads import Run

import shelve
import json

def allowSelfSignedHttps(allowed):
    # bypass the server certificate verification on client side
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

allowSelfSignedHttps(True) # this line is needed if you use self-signed certificate in your scoring service.

isDebug = True

class GptChatState:
    def __init__(self):
        self.should_cleanup: bool = False

        self.ai_messages = []
        self.ai_results = []
        self.ai_category = 'GENERAL'
        # List of assistants created
        self.ai_assistants = []
        # List of threads created
        self.ai_threads = []
        # List of files uploaded
        self.ai_files = []
        self.chat_messages = []
        self.mt_region = "" 
        self.aai_1keyv2 = "" 
        self.mt_endpoint = "" 
        self.mt_base = "" 
        self.phi_3_key = "" 
        self.phi_3_endpoint = "" 
        self.aoai_api_endpoint = "" 
        self.aoai_api_key = "" 
        self.aoai_api_version = "" 
        self.aoai_api_deployment_name = "" 
        self.aoai_api_gpt_assistant = "" 
        
        self.load_env_variables('../.env')
        
        # print(f"inside GptChatState()..*..\n {self.aoai_api_endpoint} {self.aoai_api_key} {self.aoai_api_version}")
        self.client = AzureOpenAI(
            api_key=self.aoai_api_key,  
            api_version=self.aoai_api_version,
            azure_endpoint = self.aoai_api_endpoint
        )

        # Define the Assistant tools
        self.tools_list = [
            {"type": "code_interpreter"},
            {
            "type": "function",
                "function": {
                "name": "getCurrentWeather",
                "description": "Get the weather in location",
                "parameters": {
                    "type": "object",
                    "properties": {
                    "location": {"type": "string", "description": "The city and state e.g. San Francisco, CA"},
                    "unit": {"type": "string", "enum": ["c", "f"]}
                    },
                    "required": ["location"]
                }
                }
            }
        ]

        self.clear_shelves()

# ### Create an Assistant, 1st Thread and grant access to data
    def createAssistant(self, deployment_name: str):
        assistant = self.client.beta.assistants.create(
            name = "Multilingual Medical Virtual Assistant",
            instructions="""
            You are a multilingual professional medical assistant who provides medical information. 
            """,
            model = deployment_name,
            tools = self.tools_list,
            file_ids=[]
        )
        self.print(f"Assistant created: {assistant.id}")        
        self.ai_assistants.append(assistant)
            

    def print(self, text: str):
        if isDebug:
            print(text)
        
    '''
    load_env_variables
    '''
    def load_env_variables(self, env_file_path):
        self.mt_region = os.getenv("MT_REGION")
        self.aai_1keyv2 = os.getenv("AAI_1KEYV2")
        self.mt_endpoint = os.getenv("MT_URI")
        self.mt_base = os.getenv("MT_BASE_URL")
        self.phi_3_key = os.getenv("PHI_3_KEY")
        self.phi_3_endpoint = os.getenv("PHI_3_URL")
        self.aoai_api_endpoint = os.getenv("AOAI_URI")
        self.aoai_api_key = os.getenv("AOAI_KEY")
        self.aoai_api_version = os.getenv("AOAI_VERSION")
        self.aoai_api_deployment_name = os.getenv("AOAI_GPT_DEPLOYMENT")
        self.aoai_api_gpt_assistant = os.getenv("AOAI_GPT_ASSISTANT")

    # ### Setup Translator RESTful call

    def translate(self, text_array, target_language, category='general'):
        # Use the Translator translate function
        url = self.mt_base + '/translate'
        # Build the request
        params = {
            'api-version': '3.0',
            #'from': source_language,
            'to': target_language,
            'category': category
        }
        headers = {
            'Ocp-Apim-Subscription-Key': self.aai_1keyv2,
            'Ocp-Apim-Subscription-Region': self.mt_region,
            'Content-type': 'application/json'
        }
        msg = "" 
        for text in text_array:
            msg += text+"\n"
        body = [{
            'text': msg
        }]
        # Send the request and get response
        request = requests.post(url, params=params, headers=headers, json=body)
        response = request.json()
        self.print(response)

        # Get translation
        translation = response[0]["translations"][0]["text"]
        srcLID = response[0]["detectedLanguage"]["language"]
        
        self.print(response[0])
            
        # Return the translation and source LID
        return translation, srcLID

# ### Handle state
    def add_item(self, item):
        self.ai_messages.append(item)

    def clear_items(self):
        self.ai_messages.clear()

    def add_thread(self, thread):
        for item in self.ai_threads:
            if item.id == thread.id:
                return
        self.ai_threads.append(thread)
        self.print(f"Added thread: {thread.id}, {len(self.ai_threads)}")

    def check_if_thread_exists(self, user_id):
        with shelve.open("threads_db") as self.threads_shelf:
            return self.threads_shelf.get(user_id, None)

    def store_thread(self, user_id, thread):
        with shelve.open("threads_db", writeback=True) as self.threads_shelf:
            self.add_thread(thread)
            self.threads_shelf[user_id] = thread.id

    def clear_shelves(self):
        with shelve.open("assistant_db") as self.assistant_shelf:
            self.assistant_shelf.clear()
        with shelve.open("threads_db") as self.threads_shelf:
            self.threads_shelf.clear()

    def add_item(self, item):
        self.ai_messages.append(item)

    def clear_items(self):
        self.ai_messages.clear()

    def store_message(self, msg):
        self.chat_messages.append(msg)

    # ### Handle and print Assistant Thread Messages

    def read_assistant_file(self, file_id:str):
        response_content = self.client.files.content(file_id)
        return response_content.read()

# ### Setup Translator RESTful call

    def print_messages(self, name: str, messages):
        message_list = []
        self.ai_messages.clear()

        # Get all the messages till the last user message
        for message in messages:
            message_list.append(message)
            if message.role == "user":
                break

        # Reverse the messages to show the last user message first
        message_list.reverse()

        # Print the user or Assistant messages or images
        for message in message_list:
            for item in message.content:
                # Determine the content type
                if item.type == 'text':
                    self.add_item("{0}\n".format(item.text.value))

                # Check and print details about annotations if they exist
                if item.text.annotations:
                    for annotation in item.text.annotations:
                        self.add_item("Annotation Text: {0}".format(annotation.text))
                        self.add_item("File_Id: {0}".format(annotation.file_path.file_id))

                        annotation_data = self.client.files.content(annotation.file_path.file_id)
                        annotation_data_bytes = annotation_data.read()

                        #file_extension = annotation.text.split('.')[-1]
                        filename = annotation.text.split('/')[-1]

                        with open(f"{filename}", "wb") as file:
                            file.write(annotation_data_bytes)

            # Check if the content is an image file and print its file ID and name
                elif item.type == 'image_file':
                    # Retrieve image from file id                
                    data_in_bytes = self.read_assistant_file(item.image_file.file_id)
                    # Convert bytes to image
                    readable_buffer = io.BytesIO(data_in_bytes)
                    image = self.Image.open(readable_buffer)
                    # Resize image to fit in terminal
                    width, height = image.size
                    image = image.resize((width // 2, height // 2), self.Image.LANCZOS)
                    # Display image
                    image.show()
                    
        
    
    # ### Process the user Prompts

    def get_target_language(self, query):
        self.ai_messages.clear()
        self.add_item(query)
        txt = query
        tgt = 'en'
        
        prompt, srcLID = self.translate(self.ai_messages, tgt, self.ai_category)
        
        self.ai_messages.clear()

        self.print(f"inside get_target_language()...\n {prompt} {txt} {tgt}")
        
        if (prompt.lower().find('translate')) != -1:
            if prompt.lower().find('french') != -1:
                tgt = 'fr'
                txt = prompt.split('Translate')[0]
            elif prompt.lower().find('german') != -1:
                tgt = 'de'
                txt = prompt.split('Translate')[0]
            elif prompt.lower().find('spanish') != -1:
                tgt = 'es'
                txt = prompt.split('Translate')[0]
            elif prompt.lower().find('chinese') != -1:
                tgt = 'zh'
                txt = prompt.split('Translate')[0]
        else:
            tgt = srcLID

        self.print(f"inside get_target_language()...\n {query[0]} {txt} {tgt} srcLID {srcLID}")

        return prompt, tgt
    
    def process_prompt(self, name, user_id, query: str, ACSTranslate: bool, parameters: dict):
              
        # if self.ai_assistants == []:
        #     self.createAssistant(parameters['deployment'])
            
        # Customer selection sets it
        self.ai_results = []
        prompt = query
        tgt = 'en'
        msg = ""

        if ACSTranslate:  #send query in English
            prompt, tgt = self.get_target_language(prompt)
            self.print(f"{prompt}, {tgt}, {ACSTranslate}")
            
        #return ai_results.append(prompt)
        #'''
        
        thread_id = self.check_if_thread_exists(user_id)

        # If a thread doesn't exist, create one and store it
        if thread_id is None:
            self.print(f"Creating new thread for {name} with user_id {user_id}")
            thread = self.client.beta.threads.create()
            self.store_thread(user_id, thread)
            thread_id = thread.id
        # Otherwise, retrieve the existing thread
        else:
            self.print(f"Retrieving existing thread for {name} with user_id {user_id}")
            thread = self.client.beta.threads.retrieve(thread_id)
            self.add_thread(thread)

        self.client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)
        
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id= self.aoai_api_gpt_assistant,
            instructions="Please address the user as Jane Doe. The user has a premium account. Be assertive, accurate, and polite. Ask if the user has further questions. Do not provide explanations for the answers."
            + "The current date and time is: "
            + datetime.now().strftime("%x %X")
            + ". ",
        )

        # self.print(f"processing ...({ACSTranslate}), {self.ai_assistants[0].id}...")
        
        while True:
            run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "completed":
                # Handle completed
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                self.print(f"messages: {messages}")
                self.print_messages(name, messages)
                self.print(f"inside process_prompt()\n {self.ai_messages}, {tgt}")
                
            
                # Print translated text result
            
                if ACSTranslate:
                    self.ai_results.append("Powered by Azure AI Translator...\n\n{0}".format(self.translate(self.ai_messages, tgt, self.ai_category)[0]))
                    return self.ai_results
                else:
                    # for text in ai_messages:
                    #     msg += text+"\n"
                    # return msg
                    break
                
            if run.status == "failed":
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                self.print_messages(name, messages)
                # Handle failed
                break
            if run.status == "expired":
                # Handle expired
                self.print(f"user: {name}:\nRequest expired...\n")
                break
            if run.status == "cancelled":
                # Handle cancelled
                self.print(f"user: {name}:\nRequest cancelled...\n")
                break
            if run.status == "requires_action":  
                # Define the list to store tool outputs
                tool_outputs = []  
                
                # Submit all tool outputs at once after collecting them in a list
                if tool_outputs:
                    try:
                        run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                        )
                        self.print("Tool outputs submitted successfully.")
                    except Exception as e:
                        print("Failed to submit tool outputs:", e)
                
                break
            else:
                time.sleep(5)
                
        self.print(f"inside process_prompt()\n {self.ai_messages}")
        
        return ("{0}\n{1}".format(self.ai_messages[0], self.ai_messages[1]))    

    def cleanup(self, client):
        print("Deleting: ", len(self.ai_assistants), " assistants.")
        for assistant in self.ai_assistants:
            print(client.beta.assistants.delete(assistant.id))
        print("Deleting: ", len(self.ai_threads), " threads.")
        for thread in self.ai_threads:
            print(client.beta.threads.delete(thread.id))
        print("Deleting: ", len(self.ai_files), " files.")
        for file in self.ai_files:
            print(client.files.delete(file.id))

