import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
import pandas as pd
import re
from datetime import date
from dotenv import load_dotenv
from openai import OpenAI
import logging




load_dotenv(dotenv_path=r'keys.env')
openai_api_key = os.getenv('OPENAI_API_KEY')
logging.basicConfig(level=logging.ERROR)

def get_chatgpt_response(prompt,openai_api_key):
    client = OpenAI(
        # This is the default and can be omitted
        api_key=openai_api_key
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or "gpt-4" if available
        messages=[{"role": "user", "content": prompt}]
    )
    return response

def get_category(items_list,openai_api_key):
    food_categories = [
    "Dairy",
    "Meat",
    "Poultry",
    "Fish and Seafood",
    "Vegetables",
    "Fruits",
    "Grains and Cereals",
    "Legumes and Pulses",
    "Nuts and Seeds",
    "Oils and Fats",
    "Beverages",
    "Snacks and Confectionery",
    "Spices and Condiments",
    "Packaged and Processed Foods",
    "Bakery Products"
]

    prompt='Please categorize the following list of items into these categories of food products:' +str(food_categories)+'. Provide the outcome in the form of a Python-readable list of categories, with each item categorized accordingly, no extra text or explanation. The list should look like a valid Python list, like this: ["Dairy", "Meat", "Vegetables", "Snacks and Confectionery"].Here are the items to categorize: ' + str(items_list)
    response = get_chatgpt_response(prompt,openai_api_key)
    return(response.choices[0].message.content)

def get_standardized_product(items_list,openai_api_key):
    prompt='Please standardize this item list into standard product names.Do not provide product specifities. Provide the outcome in the form of a Python-readable list of categories, with each item categorized accordingly, no extra text or explanation. The list should look like a valid Python list, like this: ["Milk", "Cheddar Cheese", "Tomatoe"].' +'Here are the items to standardize: ' + str(items_list)
    response = get_chatgpt_response(prompt,openai_api_key)
    return(response.choices[0].message.content)



def analyze_layout(endpoint,key,formUrl):
    # sample document
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-receipt", AnalyzeDocumentRequest(url_source=formUrl
    ))
    try:
        result: AnalyzeResult = poller.result()
        result_dict=result.as_dict()
        try:
            transaction_date=result_dict['documents'][0]['fields']['TransactionDate']['valueDate']
        except:
            transaction_date=date.today()
        transaction_total=result_dict['documents'][0]['fields']['Total']['valueCurrency']['amount']
        try:
            merchant_name=result_dict['documents'][0]['fields']['MerchantName']['valueString']
        except:
            merchant_name=''
        data=result_dict['documents'][0]['fields']['Items']['valueArray']
        default_price = {'valueCurrency': {'amount': 0}}
        for item in data:
            if "'Price': " not  in str(item):
                item['valueObject']['Price'] = default_price
        extracted_items = [d['valueObject']['Description']['content'] for d in data if 'valueObject' in d and 'Description' in d['valueObject'] and 'content' in d['valueObject']['Description'] ]
        extracted_prices = [d['valueObject']['TotalPrice']['valueCurrency']['amount'] for d in data if 'valueObject' in d and 'TotalPrice' in d['valueObject'] and 'valueCurrency' in d['valueObject']['TotalPrice'] and 'amount' in d['valueObject']['TotalPrice']['valueCurrency']]
        extracted_unit_prices=[d['valueObject']['Price']['valueCurrency']['amount'] for d in data if 'valueObject' in d and 'Price' in d['valueObject'] and 'valueCurrency' in d['valueObject']['Price'] and 'amount' in d['valueObject']['Price']['valueCurrency']]
        extracted_metadata=[d['content'] for d in data if 'content' in d]
        try:
            standardized_items=eval(get_standardized_product(extracted_items,openai_api_key))
        except Exception as e:
            standardized_items=['' for _ in range(len(extracted_items))]
        try:
            categories=eval(get_category(extracted_items,openai_api_key))
        except Exception as e:
            categories=['' for _ in range(len(extracted_items))]
        df=pd.DataFrame(zip(extracted_metadata,extracted_items,standardized_items,categories,extracted_unit_prices,extracted_prices),columns=['metadata','items','standardized_items','categories','unit_price','total_price'])
        #df['unit_price'] = df['metadata'].apply(lambda x: re.search(r"(\d+)\s*x\s*(\d,\d{2})\s*(\d,\d{2})", x).group(2) if re.search(r"(\d+)\s*x\s*(\d,\d{2})\s*(\d,\d{2})", x) else None).fillna(df['total_price'])
        df.loc[df['unit_price'] == 0, 'unit_price'] = df['total_price']
        try:
            df['reduction_percentage'] = df['metadata'].apply(lambda x: re.search(r"(-?\d+)%", x).group(1) if re.search(r"(-?\d+)%", x) else None)
            df['reduction_percentage'] = df['reduction_percentage'].fillna(0)
            df['reduction_percentage']=abs(df['reduction_percentage'].astype(int))/100
        except:
            df['reduction_percentage']=0
            pass
        output={}
        output['transaction_date']=transaction_date
        output['merchant_name']=merchant_name
        output['transaction_total']=transaction_total
        output['data']=df.to_json(orient='columns')
        return output
    except Exception as e:
        return e
if __name__ == "__main__":
    analyze_layout()
