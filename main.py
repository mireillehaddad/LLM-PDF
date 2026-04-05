from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError(
        "OPENAI_API_KEY not found. Please add it to .env or set it in the environment."
    )

os.environ["OPENAI_API_KEY"] = api_key

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

response = llm.invoke("Hello!")
print(response.content)