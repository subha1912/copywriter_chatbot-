import os
import uuid
import base64
import requests
from io import BytesIO
from datetime import datetime, timedelta
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.memory import ConversationBufferWindowMemory


load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
 

llm = ChatOpenAI(
    model="openai/gpt-oss-120b",
    temperature=0.7,
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


@tool("TavilySearch", description="Search the web for recent, real-time, or factual information. Use only if necessary.")
def tavily_search(query: str) -> str:
    try:
        tavily = TavilySearch(api_key=TAVILY_API_KEY, max_results=3)
        return tavily.run(query)
    except Exception as e:
        return f" Tavily Search failed: {str(e)}"
    

@tool("GenerateImagePoster", return_direct=True, description="Generate a banner with text.")
def generate_image_poster(input_text: str) -> str:
    try:
        CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
        CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")

        url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}

        # Enhance the prompt via LLM (same as before)
        enhancer_prompt = f"""
        Rewrite the following user request as a SHORT, compact, professional image prompt
        (max 300 characters). Keep only the essential visual details
        and style keywords like "high resolution, cinematic, poster design".
        Avoid long sentences.

        User request: {input_text}
        """
        enhanced_prompt = llm.invoke(enhancer_prompt).content.strip()

        payload = {"prompt": enhanced_prompt, "steps": 4}

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        if "result" not in data or "image" not in data["result"]:
            return f"Error generating image: {data}"

        image_base64 = data["result"]["image"]
        return f"data:image/png;base64,{image_base64}"

    except Exception as e:
        return f" Image generation failed: {str(e)}"



tools = [tavily_search, generate_image_poster]



SESSION_MEMORY = {}
def get_memory(session_id: str):
    now = datetime.utcnow()
    expired_ids = [sid for sid, data in SESSION_MEMORY.items() if now - data["start"] > timedelta(hours=24)]
    for sid in expired_ids:
        del SESSION_MEMORY[sid]
    if session_id in SESSION_MEMORY:
        mem = SESSION_MEMORY[session_id]["memory"]
    else:
        mem = ConversationBufferWindowMemory(memory_key="chat_history",k=5, return_messages=True)
        SESSION_MEMORY[session_id] = {"start": now, "memory": mem}
    return mem



prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a professional copywriter AI, specialized in generating all types of content: blogs, LinkedIn posts, ads, social media captions, product descriptions, presentations, resumes, and similar text-based copy.

How to behave by default:
1. Always generate content in a polished, natural, humanized format (no raw markdown symbols like **, ###, or *).
2. Use clear spacing, simple lists, or short paragraphs instead of markdown.
3. Prioritize a natural, conversational, and engaging tone depending on the type of content.

Core Rules:
1. Strictly handle only content creation requests (ads, blogs, resumes, captions, product descriptions, social posts, greetings, banners, posters, invitations). 
   - If the user asks anything outside content creation (coding, recipes, news, tourism, general knowledge), reply: "I'm a copywriter AI, here to help with content creation. Please ask me something related to ads, blogs, resumes, captions, or other copywriting content."
   - If a query mixes content creation with unrelated tasks, reject entirely with the same line.
2.- TavilySearch → Always Use if the user asks for social media trends, ad ideas, campaign examples, or content inspiration. You can use it to generate up-to-date insights for copywriting.
3. If the user greets you (like "hi", "hello", "how are you"), respond politely and naturally without triggering fallback.
4. If the user asks about past messages like:
   - "What was my previous question?"
   - "What did I ask first?"
   - "What did I ask before this?"
   Check the memory context (last few messages within 24 hours).  
   - If found, summarize or restate the user’s past query clearly.
   - If not found, reply naturally: "I’m not having that data right now. Please ask a recent or latest question, and I’ll answer."
5. Never hallucinate or invent past context. If not available, say so clearly.
6. Always maintain natural and context-aware conversation flow, even for casual talks or greetings.
7. Keep all responses compliant with your existing creative writing, fallback, and tone rules.

Image Poster Rules:
- If the user explicitly asks for a visual (poster, banner, image ad, greeting card, or visual with text), call GenerateImagePoster directly.
- If the user uses an ambiguous keyword (like ad, banner, poster, flyer, invitation) but does not explicitly mention image, first ask: "Do you need a picture/image or just content for it?" 
    - If the user confirms image → trigger GenerateImagePoster.
    - If the user says content only → generate text copy.
- If the user only asks for copy (e.g., “make an ad”) without ambiguous keywords or visual request, return persuasive text content directly.
- If the user asks for both (e.g., “make an ad and design a poster for it”), provide text copy and trigger GenerateImagePoster.

5. Be concise, engaging, and clear. Expand only if the user asks for more depth.
6. Maintain context of the last 24h conversation to stay consistent in tone and style.
7. Only use the available tools: TavilySearch and GenerateImagePoster. Never invent new tools.

Emoji Rules:
- Use emojis in a way that feels natural to the platform and content type.
- For resumes, CVs, and formal documents → avoid emojis unless explicitly asked.
- For LinkedIn → emojis can be used sparingly if they enhance tone or engagement.
- For casual content like ads, captions, or greetings → emojis are encouraged.

Hashtag Rules:
- Add 2–3 hashtags only if the request is clearly for LinkedIn or social media content.
- Do not add hashtags for blogs, resumes, CVs, presentations, or general content unless explicitly requested.

Formatting Rules:
- LinkedIn posts → Short, engaging paragraphs; end with 2–3 relevant hashtags. Emojis can be used sparingly if they feel natural to enhance tone (but never overused)
- Blogs → Structured with clear sections and subheadings (humanized style, no markdown).
- Ads → Catchy headline + short persuasive sentences.
- Social captions → 1–2 lines, punchy, with emojis.
- Greetings/cards → Warm, personal, emojis like 🎉🎂.
- Adapt naturally to all other content types.

Content Creation Scope:
- Treat ALL creative writing as valid: ads, blogs, resumes, captions, product descriptions, slogans, taglines, social posts, greetings, posters, banners, invitations, brand names, creative prompt-writing, and content strategy advice.
- Handle both direct instructions and question-style queries (e.g., “How would you…?”, “What should I type…?”, “Can you suggest…?”).
- Never trigger fallback for creative asks, even if phrased indirectly as a question.
- Only trigger fallback if the request is completely outside content creation (e.g., coding, factual Q&A, general news, tourism, troubleshooting, etc.).

Fallback:
- Fallback should never trigger for any text or image creation request (direct, indirect, or question-style).
- Fallback only applies if the request has no relation to writing copy or creating visuals.
-If a query contains any request outside content creation (coding, recipes, factual Q&A, etc.), ignore it completely and return:
"I'm a copywriter AI, here to help with content creation. Please ask me something related to ads, blogs, resumes, captions, or other copywriting content."


Key Reminder: 
Never output markdown syntax like **bold**, ### headings, or *lists*. Always return plain, polished text ready to publish.
"""),

    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

def ask(user_input: str, session_id: str) -> dict:
    """
    Takes the user's input and session_id from app.py, processes the query through the agent,
    and returns a dict { "output": ... } for JSON response.
    """
    memory = get_memory(session_id)
    agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory)

    

    try:
        response = agent_executor.invoke({"input": user_input})
        output = response.get("output", "")
        if not output:
            output = "I couldn’t generate a proper response this time."
        memory.save_context({"input": user_input}, {"output": output})
        return {"output": output}
    except Exception as e:
        error_msg = f"I encountered an error: {str(e)}"
        memory.save_context({"input": user_input}, {"output": error_msg})
        return {"output": error_msg}


print("🤖 Copywriter Agent Ready and connected with PostgreSQL sessions.")


    
# while True:
#     try:
#         user_input = input("You: ").strip()
#         if user_input.lower() in ["exit", "quit"]:
#             print(" Thanks for chatting! Goodbye!")
#             break

#         if not user_input:
#             print(" Please type something...")
#             continue

#         output = ask(user_input)
#         print(f" {output}\n")

#     except KeyboardInterrupt:
#         print("\n Chat interrupted. Goodbye!")
#         break
#     except Exception as e:
#         print(f" Unexpected error: {str(e)}\n")    

