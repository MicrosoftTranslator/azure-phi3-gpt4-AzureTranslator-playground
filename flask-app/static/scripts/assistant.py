from flask import render_template, request, url_for, flash, redirect, jsonify, session
import os
import requests
from dotenv import load_dotenv
import urllib.request
import json
import ssl
import json

def allowSelfSignedHttps(allowed):
    # bypass the server certificate verification on client side
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

allowSelfSignedHttps(True) # this line is needed if you use self-signed certificate in your scoring service.

isDebug = False


# ### Handle state
class ChatState:
    def __init__(self):
        self.should_cleanup: bool = False

        self.ai_messages = []
        self.ai_results = []
        self.ai_category = 'GENERAL'

        self.mt_region = "" 
        self.aai_1keyv2 = "" 
        self.mt_endpoint = "" 
        self.mt_base = "" 
        self.phi_3_key = "" 
        self.phi_3_endpoint = "" 

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

    def add_item(self, item):
        self.ai_messages.append(item)

    def clear_items(self):
        self.ai_messages.clear()


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
        
        # Get translation
        translation = response[0]["translations"][0]["text"]
        srcLID = response[0]["detectedLanguage"]["language"]
        
        if isDebug:
            print(response[0])
            
        # Return the translation and source LID
        return translation, srcLID

     
    
    # ### Process the user Prompts
    '''
    get_target_language
    '''
    def get_target_language(self, query):
        self.ai_messages.clear()
        self.add_item(query)
        txt = query
        tgt = 'en'
        
        prompt, srcLID = self.translate(self.ai_messages, tgt, self.ai_category)
        
        if isDebug:
            print(f"inside get_target_language()...\n {prompt} {txt} {tgt}")
        
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

        if isDebug:
            print(f"inside get_target_language()...\n {query[0]} {txt} {tgt} srcLID {srcLID}")

        return prompt, tgt
    
    '''
    process_prompt
    
    '''
    def process_prompt(self, name, user_id, query: str, ACSTranslate: bool, ACSPii: bool, parameters: dict):
        # Customer selection sets it
        ai_results = ['Powered by Azure AI Translator...\n\n']
        
        self.ai_messages.clear()
        
        prompt = query
        tgt = 'en'
        msg = ""
        
        if ACSTranslate:  #send query in English
            prompt, tgt = self.get_target_language(query)

        if isDebug:
            print(prompt, tgt, ACSTranslate)
            
        data = {"input_data": {"input_string":
                [{"role":"system", "content": "You are a professional assistant for students."},
                {"role":"user", "content": prompt}],
                "parameters": {
                            "top_p": parameters['top_p'],
                            "top_k": 0.8,
                            "stop": ["<|end|>"],
                            "stop_sequences": ["<|end|>"],
                            "temperature": parameters['temperature'],
                            "max_new_tokens": parameters['max_new_tokens'],
                            "return_full_text": "False",
                            "repetition_penalty": 1.2,
                            "max_length":200 
                        }
                }
            }

        body = str.encode(json.dumps(data))      

        if isDebug:
            print(f"processing ...({body})...")

        if not self.phi_3_key:
            raise Exception("A key should be provided to invoke the endpoint")

        # The azureml-model-deployment header will force the request to go to a specific deployment.
        # Remove this header to have the request observe the endpoint traffic rules
        headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ self.phi_3_key), 'azureml-model-deployment': parameters['deployment'] }

        req = urllib.request.Request(self.phi_3_endpoint, body, headers)
        
        if isDebug:
           print(f"Request ...({req})...({self.phi_3_endpoint})")

        try:
            response = urllib.request.urlopen(req)

            result = response.read()
            
            dictStr = dict(json.loads(result))
            if isDebug:
                print(dictStr["output"])
                
            self.add_item(dictStr["output"])

            if ACSTranslate:
                ai_results.append("{0}".format(self.translate(self.ai_messages, tgt, self.ai_category)[0]))
                return ai_results


        except urllib.error.HTTPError as error:
            print("The request failed with status code: " + str(error.code))

            # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
            print(error.info())
            print(error.read().decode("utf8", 'ignore'))   
            
        if isDebug:
            print(f"inside process_prompt()\n {self.ai_messages}")
            
        return self.ai_messages    
