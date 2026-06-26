from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama


prompt = ChatPromptTemplate.from_template(
    "Explain this in simple terms: {topic}"
)

model =  ChatOllama(model="qwen2.5")

chain = prompt | model

result = chain.invoke({"topic": "Recursion"})
print(result)