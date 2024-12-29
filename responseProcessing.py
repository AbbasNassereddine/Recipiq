
from dotenv import load_dotenv
import os
#from openai import OpenAI
import difflib
import json
from openai import OpenAI
import requests
import sys
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')



def get_chatgpt_response(prompt,openai_api_key):
    client = OpenAI(
        # This is the default and can be omitted
        api_key=openai_api_key
    )
    response = client.chat.completions.create(
        model="gpt-4",  # or "gpt-4" if available
        messages=[{"role": "user", "content": prompt}]
    )
    return response

# def locationGeoCode (address,country,azure_loc_key):
#     address=address + ', ' + country
#     geocode_url = f"https://atlas.microsoft.com/search/address/json?api-version=1.0&subscription-key={azure_loc_key}&query={address}"
#     response = requests.get(geocode_url)
#     data = response.json()
#     location = data['results'][0]['position']
#     latitude=location['lat']
#     longitude=location['lon']
#     return latitude, longitude

def recipe_suggestion (recipe_input,openai_api_key):
    prompt='You are a friendly bot that recommend recipes based on an input from supermarket receipts. Give preference to healthy options. You can provide emojis in you reponse. This is the list of available items: ' + recipe_input+'. Provide the reponse in a list of concise recommendations.'
    try:
        response = get_chatgpt_response(prompt,openai_api_key)
        return(response.choices[0].message.content)
    except Exception as e:
        return('error in response processing')



    


   
