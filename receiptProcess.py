import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
import pandas as pd
import re
# set `<your-endpoint>` and `<your-key>` variables with the values from the Azure portal
#endpoint = "https://receiptrecog.cognitiveservices.azure.com/"
#key = "DQepKp8TuWADXdJySQzSJrwoGd5aVRTiIvn6IsiEAaMGGZZfocNUJQQJ99ALAC5RqLJXJ3w3AAALACOGiOrf"

# The Blob Storage URL for the receipt image
#formUrl = "https://bereceipts.blob.core.windows.net/delhaize/receipt.jpg"


# helper functions




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
        transaction_date=result_dict['documents'][0]['fields']['TransactionDate']['valueDate']
        transaction_total=result_dict['documents'][0]['fields']['Total']['valueCurrency']['amount']
        merchant_name=result_dict['documents'][0]['fields']['MerchantName']['valueString']
        data=result_dict['documents'][0]['fields']['Items']['valueArray']
        extracted_items = [d['valueObject']['Description']['content'] for d in data if 'valueObject' in d and 'Description' in d['valueObject'] and 'content' in d['valueObject']['Description'] ]
        extracted_prices = [d['valueObject']['TotalPrice']['valueCurrency']['amount'] for d in data if 'valueObject' in d and 'TotalPrice' in d['valueObject'] and 'valueCurrency' in d['valueObject']['TotalPrice'] and 'amount' in d['valueObject']['TotalPrice']['valueCurrency']]
        extracted_metadata=[d['content'] for d in data if 'content' in d]
        df=pd.DataFrame(zip(extracted_metadata,extracted_items,extracted_prices),columns=['metadata','items','total_price'])
        df['unit_price'] = df['metadata'].apply(lambda x: re.search(r"(\d+)\s*x\s*(\d,\d{2})\s*(\d,\d{2})", x).group(2) if re.search(r"(\d+)\s*x\s*(\d,\d{2})\s*(\d,\d{2})", x) else None).fillna(df['total_price'])
        df['reduction_percentage'] = df['metadata'].apply(lambda x: re.search(r"(-?\d+)%", x).group(1) if re.search(r"(-?\d+)%", x) else None)
        df['reduction_percentage'] = df['reduction_percentage'].fillna(0)
        df['reduction_percentage']=abs(df['reduction_percentage'].astype(int))/100
        output={}
        output['transaction_date']=transaction_date
        output['merchant_name']=merchant_name
        output['transaction_total']=transaction_total
        output['data']=df.to_json(orient='columns')
        return output
    except Exception as e:
        return e
    
#return result
    # Extract fields
    # if result.fields:
    #     output = ""
    #     for field_name, field in result.fields.items():
    #         output += f"Field name: {field_name}\n"
    #         output += f"Content: {field.content}\n"  # Correct attribute
    #         output += f"Confidence: {field.confidence}\n"
    #         output += f"Type: {field.type}\n"
    #     return output
    # else:
    #     return "No fields were extracted from the document."
    # if result.tables:
    #     outpout_tables=()
    #     for table_idx, table in enumerate(result.tables):
    #         df=pd.DataFrame()
    #         df = pd.DataFrame(index=range(table.row_count), columns=range(table.column_count))
    #         for cell in table.cells:
    #             df.iloc[cell.row_index, cell.column_index]=cell.content
    #         outpout_tables=outpout_tables+(df,)
    # return outpout_tables



if __name__ == "__main__":
    analyze_layout()
