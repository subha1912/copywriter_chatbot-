
# **Copywriter Chatbot**

## **1. Project Overview**

A brief description of your project:

> Copywriter Chatbot is an AI-powered assistant that helps generate marketing copy, banners, and content suggestions. Users can interact via text, and the chatbot generates creative outputs based on the input prompt.


## **2. Workflow / How it Works**

1. **User Input**: User provides a prompt (text) describing the desired copy or content.
2. **API Call**: The chatbot uses a language model (e.g., OpenAI, Groq) to generate responses.
3. **Output Generation**: Generated content is processed and returned as text or images.
4. **Banner Creation**: Optional generated banners are stored in a `generated_banners/` folder.
5. **Repeat**: Users can continue providing prompts to generate new outputs.


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
STABILITY_API_KEY=your_stability_key
```

> ⚠️ Do not commit `.env` — it contains sensitive keys.

---

## **5. Running the Chatbot**


python app.py

* Follow the CLI instructions or use the provided UI (if any).
* Generated banners will be stored in `generated_banners/`.



## **6. Notes**

* Ensure you provide your **own API keys** — the project will not run without them.
* Large generated images can increase repo size; consider cleaning `generated_banners/` if not needed.
* Compatible with Python 3.10+.


