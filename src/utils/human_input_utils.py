import requests
import json
import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from models.transactions import Transactions

def get_prompt_template() -> str:
    return """<task>
You are a transaction management assistant. Your task is to interpret user input and update a list of financial transactions accordingly.
</task>

<current_transactions>
{transactions}
</current_transactions>

<user_request>
{user_input}
</user_request>

<instructions>
Based on the user's request, update the list of transactions by doing ONE of the following:
- If the user wants to modify a specific transaction, update only that transaction
- If the user wants to add a new transaction, add it to the list
- If the user wants to delete a transaction, remove it from the list

Each transaction must have exactly these three properties:
- date: The date in YYYY-MM-DD format (string)
- description: A brief description of the transaction (string)
- amount: The transaction amount as a number (negative for debits, positive for credits)
</instructions>

<output_format>
Return a JSON array of transaction objects. Each object must have exactly the three properties listed above.

Example output format:
[
  {{
    "date": "2024-01-15",
    "description": "Grocery shopping",
    "amount": -45.67
  }},
  {{
    "date": "2024-01-16",
    "description": "Salary deposit",
    "amount": 2500.00
  }}
]

Return ONLY the JSON array. Do not include any explanations, comments, or additional text.
</output_format>"""

def interpret_and_update(user_input: str, transactions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    
    llm = ChatOpenAI(
        model_name=os.getenv('OPENROUTER_MODEL'), 
        openai_api_base=os.getenv('OPENROUTER_API_URL'), 
        openai_api_key=os.getenv('OPENROUTER_API_KEY'))
    
    prompt_text = get_prompt_template()
    prompt = ChatPromptTemplate.from_template(prompt_text)
    parser = PydanticOutputParser(pydantic_object=Transactions)

    chain = prompt | llm | parser

    try:
        updated_transactions: Transactions = chain.invoke({"transactions": transactions, "user_input": user_input})
        return updated_transactions.model_dump()
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(f"Unexpected error in interpret_and_update: {str(e)}")
        return transactions
    
if __name__ == "__main__":
    with open("output/transactions.json", "r", encoding="utf-8") as jsonfile:
        transactions = json.load(jsonfile)
        updated_transactions = interpret_and_update("Add a new transaction on 2024-08-11 for 100.00, description is 'test'", transactions)
        print(updated_transactions)
