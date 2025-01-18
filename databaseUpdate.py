import pyodbc
from azure.identity import InteractiveBrowserCredential
import sys
from decimal import Decimal
import calendar
import pandas as pd
import json
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
#from credential import username,password


# Define connection parameters
server = 'items2.database.windows.net'
database = 'items2'
connection_string='Driver={ODBC Driver 18 for SQL Server};Server=items2.database.windows.net;Database=items2;Uid=CloudSA22ccf518;Pwd=X_majnoon95?;TrustServerCertificate=yes;'
try:
    conn = pyodbc.connect(connection_string)
    print("Connection successfl")
except Exception as e:
    print(f"Error: {e}")

def transactionUpload (transaction,user_id):
    server = 'items2.database.windows.net'
    database = 'items2'
    connection_string='Driver={ODBC Driver 18 for SQL Server};Server=items2.database.windows.net;Database=items2;Uid=CloudSA22ccf518;Pwd=X_majnoon95?;TrustServerCertificate=yes;'
    conn = pyodbc.connect(connection_string)
    user_id=user_id
    transaction_date=transaction['transaction_date']
    merchant_name=transaction['merchant_name']
    transaction_total=transaction['transaction_total']
    data=transaction['data']
    
    #query='SET IDENTITY_INSERT REQUESTS ON;'
    #cursor = conn.cursor()
    #cursor.execute(query)
    #conn.commit()
    query = f"INSERT INTO ShoppingTransactions (user_id, transaction_date,merchant_name,transaction_total,data) VALUES ( N'{user_id}',N'{transaction_date}',N'{merchant_name}',N'{transaction_total}',N'{data}' );"
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()

    #conn.close()


def monthlyAnalysis(user_id):
    final_result=''
    query="""SELECT 
    YEAR(transaction_date) AS Year,
    MONTH(transaction_date) AS Month,
    SUM(transaction_total) AS TotalAmount
FROM ShoppingTransactions
where user_id=N'"""+user_id +"""'
GROUP BY 
    YEAR(transaction_date),
    MONTH(transaction_date)
ORDER BY 
    Year, Month;
"""
    #print(query)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
    #conn.commit()
        rows = cursor.fetchall()
        query_result = rows  # This will be the actual result from your database query

    # Process and format the output
        formatted_results = []
        for row in query_result:
            year, month, total = row
            month_name = calendar.month_name[month]  # Convert month number to name
            formatted_results.append(f"- {year} {month_name} : {float(total):.2f} €")

    # Join all formatted results into a single string to return
        return "\n".join(formatted_results)
    except Exception as e:
        return(e)
    #conn.close()

def getItems(user_id):
    connection_string='Driver={ODBC Driver 18 for SQL Server};Server=items2.database.windows.net;Database=items2;Uid=CloudSA22ccf518;Pwd=X_majnoon95?;TrustServerCertificate=yes;'
    conn = pyodbc.connect(connection_string)
    user_id=str(user_id)
    query="""SELECT 
    JSON_QUERY(data, '$.items') AS ItemsList
FROM 
    ShoppingTransactions
where user_id=N'"""+user_id +"""' 
    AND transaction_date >= DATEADD(DAY, -20, GETDATE());
"""
    #print(query)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
    #conn.commit()
        rows = cursor.fetchall()
        query_result = rows
        return str(query_result)
    except Exception as e:
        return('Error: '+ query)
    

def categorySpending (user_id):
    user_id=str(user_id)
    query="""SELECT 
    JSON_QUERY(data, '$.categories') AS CategoriesList ,JSON_QUERY(data, '$.total_price') AS TotalPriceList
FROM 
    ShoppingTransactions
where user_id=N'"""+user_id +"""' 
"""
    cursor = conn.cursor()
    cursor.execute(query)
    #conn.commit()
    try:
        rows = cursor.fetchall()
        query_result = rows
        category_series = pd.Series([json.loads(item[0]) for item in rows])
        price_series = pd.Series([json.loads(item[1]) for item in rows])
        category_df = pd.DataFrame(category_series.tolist())
        price_df = pd.DataFrame(price_series.tolist())

# Flatten the DataFrames and combine them
        df = pd.DataFrame({
    'Category': category_df.values.flatten(),
    'Price': price_df.values.flatten()
        })


        #columns = [desc[0] for desc in cursor.description]
        #df = pd.DataFrame(list(rows[0]), columns=['CategoriesList','TotalPriceList'])
    except Exception as e:
        return str(e)
    # try:
    #     all_categories=[]
    #     all_total_prices=[]
    #     for category in df['CategoriesList']:
    #         all_categories.append(category.values())
    #     all_categories = [item for sublist in all_categories for item in sublist]
    #     for price in df['TotalPriceList']:
    #         all_total_prices.append(price.values())
    #     all_total_prices = [item for sublist in all_total_prices for item in sublist]
    # except Exception as e:
    #     return 'Here 2' +str(e)
    # try:
    #     df=pd.DataFrame(zip(all_categories,all_total_prices),columns=['Category','Price'])
    category_sums = df.groupby('Category')['Price'].sum()
    total_price = category_sums.sum()
    category_percentage = (category_sums / total_price) * 100
    category_percentage = category_percentage.apply(lambda x: f"{x:.2f}%")
    output=''
    for category, percentage in category_percentage.items():
        output +=f"  {category}: {percentage}"+"\n"
    return output
  







    
 
    

    
