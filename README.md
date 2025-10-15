
# **Copywriter Chatbot**

## **1. Project Overview**

A brief description of your project:

> Copywriter Chatbot is an AI-powered assistant that helps generate marketing copy, banners, and content suggestions. Users can interact via text, and the chatbot generates creative outputs based on the input prompt.


## **2. Workflow / How it Works**

1. **User Input**: User provides a prompt (text) describing the desired copy or content.
2. **API Call**: The chatbot uses a language model (e.g., OpenAI, Groq) to generate responses.
3. **Output Generation**: Generated content is processed and returned as text or images.
4. **Banner Creation**: Show in the Chat interface if user wants can download manually.
5. **Repeat**: Users can continue providing prompts to generate new outputs.
6. **Support Upload files**: If the user wants to upload any file for reference it will support and also take as a reference for the first query after uploading and for later use need to mention explicitly or else not use the uploaded files.


## **4. Setup Instructions**

### **Step 1: Clone the repository**

git clone https://github.com/your-username/penn-chatbot.git
cd penn-chatbot


### **Step 2: Create and activate virtual environment**


python -m venv .venv
.\.venv\Scripts\activate   # Windows


### **Step 3: Install dependencies**


pip install -r requirements.txt


### **Step 4: Create your own `.env` file**

*  create `.env` in the root directory.
* Add your **own API keys** (e.g., OpenAI, Groq, etc.):

```
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_accout_id
CLOUDFLARE_API_TOKEN=your_api_token
```

> ⚠️ Do not commit `.env` — it contains sensitive keys.

---

## **5. Running the Chatbot**


python app.py

* Follow the CLI instructions or use the provided UI (if any).
* display the image in the user interface based upon the user need download manually `.



## **6. Notes**

* Ensure you provide your **own API keys** — the project will not run without them.
* Compatible with Python 3.10+.


