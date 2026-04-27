from typing import TypedDict, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.graph import StateGraph, START, END

load_dotenv()

#  글로벌 벡터 저장소 초기화 (실제 제품에선 크로마db, 파인콘 등을 사용)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = InMemoryVectorStore(embeddings)

# Pydantic 스키마 정의 (기억 추출용)
class FactExtraction(BaseModel):
    has_personal_fact: bool = Field(description="사용자의 입력에 개인적인 취향, 가족 관계, 알러지, 중요 일정 등 장기적으로 기억할 만한 정보가 포함되어 있는지 여부")
    fact_summary: str = Field(description="기억해야 할 사실의 간결하고 명확한 요약 (없으면 빈 문자열)")

# 상태(State) 정의
class OSState(TypedDict):
    user_input: str
    retrieved_memories: List[str]
    ai_response: str
    extracted_fact: str

# 노드(Node) 구현
def retrieve_node(state: OSState):
    """사용자의 입력을 바탕으로 벡터 저장소에서 과거의 관련 기억을 검색하여 가져옵니다."""
    user_input = state.get("user_input", "")
    
    # 유사도 검색을 통해 가장 관련성 높은 기억 3개를 추출
    docs = vector_store.similarity_search(user_input, k=3)
    memories = [doc.page_content for doc in docs]
    
    return {"retrieved_memories": memories}

def generate_node(state: OSState):
    """검색된 장기 기억을 프롬프트에 주입하여 초개인화된 답변을 생성합니다."""
    llm = ChatOpenAI(model="gpt-5.4-nano", temperature=0.7)
    
    user_input = state.get("user_input", "")
    memories = state.get("retrieved_memories", [])
    
    memory_text = "\n".join(memories) if memories else "관련된 장기 기억이 없습니다."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 사용자의 삶을 완벽하게 이해하고 돕는 초개인화 라이프 OS 비서입니다. 제공된 [장기 기억]에 관련 정보가 있다면 이를 자연스럽게 대화에 녹여내어 사용자가 '나를 잘 알고 있다'고 느끼게 하십시오. 기억에 없는 내용을 지어내서는 안 됩니다."),
        ("user", "[장기 기억]\n{memory_text}\n\n사용자 입력: {user_input}")
    ])
    
    response = (prompt | llm).invoke({
        "memory_text": memory_text,
        "user_input": user_input
    })
    
    return {"ai_response": response.content}

def extract_and_store_node(state: OSState):
    """사용자의 입력에서 미래에 유용할 수 있는 개인적 사실을 추출하여 벡터 저장소에 저장합니다."""
    llm = ChatOpenAI(model="gpt-5.4-nano", temperature=0)
    structured_llm = llm.with_structured_output(FactExtraction)
    
    user_input = state.get("user_input", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 라이프 OS의 기억 추출기입니다. 사용자의 텍스트를 분석하여 이름, 직업, 음식 선호도, 가족 관계, 생활 습관 등 장기적으로 보존할 가치가 있는 정보만 추출하십시오."),
        ("user", "입력: {user_input}")
    ])
    
    result: FactExtraction = (prompt | structured_llm).invoke({"user_input": user_input})
    
    if result.has_personal_fact and result.fact_summary:
        # 추출된 사실을 벡터화하여 영구 저장소에 추가
        vector_store.add_texts([result.fact_summary])
        return {"extracted_fact": result.fact_summary}
    
    return {"extracted_fact": ""}

# 그래프 조립
workflow = StateGraph(OSState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.add_node("extract_and_store", extract_and_store_node)

# 검색 -> 답변 생성 -> 기억 추출 및 저장 순으로 파이프라인 구성
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", "extract_and_store")
workflow.add_edge("extract_and_store", END)

app_graph = workflow.compile()