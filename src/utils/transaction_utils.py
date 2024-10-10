import requests
import json
import csv
import os
from typing import List, Dict
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM
from accelerate import Accelerator
from transformers import pipeline

def get_prompt(ocr_text: str) -> str:
    return f"""You are an AI assistant trained to extract transaction information from financial statements. 
    Given the following text from a financial statement, please extract all transactions and format them as a list of JSON objects.
    Each transaction should have the following properties:
    - date: The date of the transaction in the format YYYY-MM-DD
    - description: A brief description of the transaction
    - amount: The transaction amount as a float (negative for debits, positive for credits)

    Here's the text from the financial statement:

    {ocr_text}

    Please return ONLY the simplified list of JSON objects, without any additional explanation or text."""

def extract_transactions(ocr_text: str) -> List[Dict[str, str]]:
    prompt = get_prompt(ocr_text)

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": os.getenv('OPENROUTER_MODEL'),
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(os.getenv('OPENROUTER_API_URL'), headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        transactions_str = result['choices'][0]['message']['content']
        
        transactions = json.loads(transactions_str)
        
        # Validate and clean up the transactions
        validated_transactions = []
        for transaction in transactions:
            if all(key in transaction for key in ['date', 'description', 'amount']):
                # Ensure amount is a float
                transaction['amount'] = float(transaction['amount'])
                validated_transactions.append(transaction)
        
        return validated_transactions
    except Exception as e:
        print(f"Error extracting transactions: {str(e)}")
        return []

def store_transactions_csv(transactions: List[Dict[str, str]], filename: str):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['date', 'description', 'amount']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for transaction in transactions:
            writer.writerow(transaction)
    
    print(f"Transactions stored in {filename}")

def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

def detect_has_transactions(chunk: str) -> bool:
    global model, tokenizer
    try:
        model, tokenizer
    except:
        model_name = "./models/fine_tuned_model"  
        # model_name = "HuggingFaceTB/SmolLM-135M" # Example of a very small model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)

    inputs = tokenizer(f"Does this text contain financial transactions? {chunk}", return_tensors="pt", max_length=1024, truncation=True)

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits, dim=-1).item()
        return predicted_class == 1  # Assuming 1 means "yes"
    
def extract_transactions_locally(ocr_text: str) -> List[Dict[str, str]]:
    chunks = split_text_into_chunks(ocr_text)
    transactions = []
    for chunk in chunks:
        transactions.extend(extract_transactions_for_chunk(chunk))
    return transactions
    
def extract_transactions_for_chunk(chunk: str) -> List[Dict[str, str]]:
    global pipe
    try:
        pipe
    except NameError:
        pipe = pipeline(
            "text-generation",
            model="google/gemma-2-9b-it",
            model_kwargs={"torch_dtype": torch.bfloat16},
            device="mps"  # 如果在Mac設備上運行，請將此更改為"mps"
        )

    prompt = get_prompt(chunk)
    messages = [
        {"role": "user", "content": prompt}
    ]

    outputs = pipe(messages, max_new_tokens=2048)
    transactions_str = outputs[0]["generated_text"][-1]["content"].strip()
    print(transactions_str)

    try:
        transactions = json.loads(transactions_str)
        return transactions
    except json.JSONDecodeError:
        print("解析JSON時出錯")
        return []

            
if __name__ == "__main__":  
    chunk_results = []
    with open(f"output/sample22.txt", "r", encoding="utf-8") as file:
        ocr_text = file.read()
        chunks = split_text_into_chunks(ocr_text)
        
        for chunk in chunks:
            result = extract_transactions_for_chunk(chunk)
            chunk_results.append([chunk.replace('\n', ' '), result])
            
    with open(f"output/test_gemma_result.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Chunk", "Transactions"])  # 寫入標題行
        writer.writerows(chunk_results)  # 寫入所有結果行

    # with open(f"output/test2.txt", "r", encoding="utf-8") as file:
    #     ocr_text = file.read()
    #     chunks = split_text_into_chunks(ocr_text)
    #     for chunk in chunks:
    #         result = detect_has_transactions(chunk)
    #         if result:
    #             transactions = extract_transactions_for_chunk(chunk)
    #             print(transactions)

