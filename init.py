from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI

db = SQLDatabase.from_uri("sqlite:///chinook-database/ChinookDatabase/DataSources/Chinook.db")
print(db.dialect)
print(db.get_usable_table_names())
print(db.run("SELECT * FROM Artist LIMIT 10;"))

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, max_tokens=100)
chain = create_sql_query_chain(llm, db)
response = chain.invoke({"question": "what is the total for all invoices for customers who listen to Aerosmith ?"})
print(db.run(response))


