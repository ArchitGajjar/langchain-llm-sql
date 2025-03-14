from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

# import langChain packages and modules.
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI

from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

app = FastAPI()

# List of allowed origins (domains that can access your API)
origins = [
    "*",  # React or other frontend apps
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

db = SQLDatabase.from_uri("sqlite:///chinook-database/ChinookDatabase/DataSources/Chinook.db")
print(db.dialect)
print(db.get_usable_table_names())
# Testing purpose -> print(db.run("SELECT * FROM Artist LIMIT 10;"))

answer_prompt = PromptTemplate.from_template(
    """Given the following user question, corresponding SQL query, and SQL result, answer the user question.
    Question: {question}
    SQL Query: {query}
    SQL Result: {result}
    Answer: """
)

# Define a Pydantic model for request and response validation
class Item(BaseModel):
    sender: str
    text: str

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI server!"}

# Endpoint to retrieve an item by ID
@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "query": q}

# Endpoint to create a new item
@app.post("/api/messages")
def create_item(item: Item):
    print("request received : ", item);
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, max_tokens=100)

    reference_chain = create_sql_query_chain(llm, db) 

    answer = answer_prompt | llm | StrOutputParser()
    execute_query = QuerySQLDataBaseTool(db=db)
    write_query = create_sql_query_chain(llm, db)
    print("write_query : ", write_query);
    chain = (
        RunnablePassthrough.assign(query=write_query).assign(
            result=itemgetter("query") | execute_query
        )
        | answer
    )

    # what is the total for all invoices for customers who listen to Aerosmith ?
    response = chain.invoke({"question": item.text})
    reference = reference_chain.invoke({"question": item.text})

    print("Query response : ", response);
    return {
        "text": item.text,
        "sender": item.sender,
        "response": response,
        "reference": reference
    }

# Endpoint to update an existing item
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {
        "message": f"Item with ID {item_id} updated successfully!",
        "updated_item": item
    }