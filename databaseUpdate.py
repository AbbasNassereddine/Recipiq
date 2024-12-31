import pyodbc
from azure.identity import InteractiveBrowserCredential
import sys
from decimal import Decimal
import calendar

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
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        return('Error: '+ query)

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
    user_id=str(user_id)
    query="""SELECT 
    JSON_QUERY(data, '$.items') AS ItemsList
FROM 
    ShoppingTransactions
where user_id=N'"""+user_id +"""' 
    AND transaction_date >= DATEADD(DAY, -10, GETDATE());
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
    
 
    

    
