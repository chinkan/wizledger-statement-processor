import gradio as gr
import os
import json
from main import process_file_from_ui
import pandas as pd
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
from dotenv import load_dotenv
load_dotenv()

def output_transactions(transactions):
    output.value = json.dumps(transactions, indent=2)

def process_statement(statement, thread, human_input = None):
    result = process_file_from_ui(statement, thread, human_input)
    return pd.DataFrame(result)

def process(statement, openrouter_api_key, openrouter_model, openrouter_api_url):
    statement_path = statement.name if hasattr(statement, 'name') else statement
    
    os.environ["OPENROUTER_API_KEY"] = openrouter_api_key if openrouter_api_key else os.getenv("OPENROUTER_API_KEY")
    os.environ["OPENROUTER_MODEL"] = openrouter_model if openrouter_model else os.getenv("OPENROUTER_MODEL")
    os.environ["OPENROUTER_API_URL"] = openrouter_api_url if openrouter_api_url else os.getenv("OPENROUTER_API_URL")

    thread = {"configurable": {"thread_id": str(uuid.uuid4())}}

    try:
        result = process_statement(statement_path, thread)
    finally:
        pass

    return result, thread["configurable"]["thread_id"]

def continue_processing(human_input, thread_id):
    thread = {"configurable": {"thread_id": thread_id}}
    return process_statement(None, thread, human_input)

def export_transactions(output):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as temp_file:
        output.to_csv(temp_file.name, index=False)
        return temp_file.name

# 創建 FastAPI 應用
app = FastAPI()

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process")
async def api_process(
    statement: UploadFile = File(...),
    openrouter_api_key: str = Form(None),
    openrouter_model: str = Form(None),
    openrouter_api_url: str = Form(None)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_statement:
        temp_statement.write(await statement.read())
        temp_statement_path = temp_statement.name

    try:
        os.environ["OPENROUTER_API_KEY"] = openrouter_api_key if openrouter_api_key else os.getenv("OPENROUTER_API_KEY")
        os.environ["OPENROUTER_MODEL"] = openrouter_model if openrouter_model else os.getenv("OPENROUTER_MODEL")
        os.environ["OPENROUTER_API_URL"] = openrouter_api_url if openrouter_api_url else os.getenv("OPENROUTER_API_URL")

        thread_id = str(uuid.uuid4())
        thread = {"configurable": {"thread_id": thread_id}}
        result = process_statement(temp_statement_path, thread)
        return {"result": result.to_dict(orient='records'), "thread_id": thread_id}
    finally:
        os.unlink(temp_statement_path)

@app.post("/continue_processing")
async def api_continue_processing(request: Request):
    data = await request.json()
    human_input = data["human_input"]
    thread_id = data["thread_id"]
    thread = {"configurable": {"thread_id": thread_id}}
    result = continue_processing(human_input, thread_id)
    return result.to_dict(orient='records')

@app.post("/export_transactions")
async def api_export_transactions(request: Request):
    data = await request.json()
    output = data["output"]
    df = pd.read_json(output)
    csv_file_path = export_transactions(df)
    return FileResponse(csv_file_path, media_type='text/csv', filename='transactions.csv')

# Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("""
    # WizLedger - Monthly Statement Processor
    Processes statements using OpenRouter API and MarkItDown.
    Extracts transactions from monthly bank statements and exports them to CSV.
    """)
    
    with gr.Tabs():
        with gr.TabItem("Process Statement"):
            with gr.Row():
                with gr.Column(scale=1):   
                    statement = gr.File(label="Select a statement file")
                    process_button = gr.Button("Process")
                    output = gr.Dataframe(label="Output", interactive=False, value=[], headers=["date", "description", "amount"])
                    human_input = gr.Textbox(label="Human Input")
                    thread_id = gr.Textbox(label="Thread ID", interactive=False)
                    continue_button = gr.Button("Continue")
                with gr.Column(scale=1):
                    export_button = gr.Button("Export")
                    csv = gr.File(label="CSV", interactive=False)
            with gr.Row():
                with gr.Accordion("API Settings", open=True):
                    gr.Markdown("OpenRouter API")
                    openrouter_api_key = gr.Textbox(label="Enter your OpenRouter API key", type="password", value=os.getenv("OPENROUTER_API_KEY") if os.getenv("OPENROUTER_API_KEY") else "")
                    openrouter_model = gr.Textbox(label="Enter your OpenRouter model",value=os.getenv("OPENROUTER_MODEL") if os.getenv("OPENROUTER_MODEL") else "")
                    openrouter_api_url = gr.Textbox(label="Enter your OpenRouter API URL",value=os.getenv("OPENROUTER_API_URL") if os.getenv("OPENROUTER_API_URL") else "")
        
        with gr.TabItem("API Usage"):
            gr.Markdown("""
            # API Usage Examples
            
            Here are examples of how to use the API endpoints using Python's `requests` library:
            
            ```python
            import requests
            import json
            # Process a new statement
            url = "http://localhost:7860/process"
            files = {
                'statement': ('statement.pdf', open('path/to/statement.pdf', 'rb'), 'application/pdf'),
            }
            response = requests.post(url, files=files)
            result = response.json()
            print(result['result'])
            thread_id = result['thread_id']

            # Continue processing
            url = "http://localhost:7860/continue_processing"
            data = {
                'human_input': 'Some human input',
                'thread_id': thread_id
            }
            response = requests.post(url, json=data)
            print(response.json())
            result = response.json()
            
            # Export transactions
            url = "http://localhost:7860/export_transactions"
            data = {'output': json.dumps(result)}
            response = requests.post(url, json=data)

            # Display the transactions
            import pandas as pd
            import io
            df = pd.read_csv(io.BytesIO(response.content), encoding='utf-8')
            display(df)
            ```
            
            Make sure to replace the placeholder values with your actual data and API keys.
            """)

    def update_output_and_thread_id(result, thread_id):
        return result, thread_id

    process_button.click(process, 
                         inputs=[statement, openrouter_api_key, openrouter_model, openrouter_api_url], 
                         outputs=[output, thread_id])
    continue_button.click(continue_processing, 
                          inputs=[human_input, thread_id], 
                          outputs=[output])
    export_button.click(export_transactions, inputs=[output], outputs=[csv])

# 將 Gradio 界面掛載到 FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

# 啟動 FastAPI 服務器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)