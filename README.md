# Memory-Augmented Life OS (장기 기억 기반 초개인화 라이프 OS)

## 1. 프로젝트 개요

이 프로젝트는 세션이 종료되면 초기화되는 기존 챗봇의 한계를 극복하기 위해, 벡터 데이터베이스(Vector DB)를 도입하여 에이전트에게 영구적인 장기 기억(Long-term Memory)을 부여하는 고도화된 라이프 비서 시스템입니다.

사용자와 대화를 나눌 때마다 에이전트는 과거의 관련 기억을 검색하여 문맥(Context)을 파악하는 동시에, 현재 대화에서 미래에 유용할 만한 새로운 사실이나 취향을 스스로 추출하여 벡터 저장소에 누적합니다. 시간이 지날수록 사용자를 더 깊이 이해하고 초개인화된 맞춤형 제안을 제공하는 것이 특징입니다.

## 2. 시스템 아키텍처 및 워크플로우

본 시스템은 검색 증강 생성(RAG)과 지식 추출이 결합된 병렬적인 흐름을 가집니다.

1. State Definition: 사용자 입력, 검색된 기억 목록, 에이전트의 응답, 새로 추출된 사실을 전역 상태로 관리합니다.
2. Retrieve Node: 사용자의 현재 입력을 임베딩하여 벡터 DB(InMemoryVectorStore)에서 가장 유사도가 높은 과거의 장기 기억 3가지를 인출합니다.
3. Generate Node: 최신 추론 모델(gpt-5.4-nano)을 사용하여, 인출된 과거의 기억을 프롬프트에 주입하고 사용자의 질문에 초개인화된 답변을 생성합니다.
4. Extract & Store Node: 사용자의 텍스트를 분석하여 이름, 취향, 알러지 등 장기 보존 가치가 있는 '개인적 사실'만을 추출합니다. 추출된 정보는 벡터화되어 영구 저장소에 추가됩니다.

## 3. 기술 스택

* Language: Python 3.10+
* Package Manager: uv
* LLM: OpenAI gpt-5.4-nano (답변 생성 및 정보 추출)
* Embedding Model: text-embedding-3-small (기억의 벡터화)
* Vector Database: LangChain InMemoryVectorStore (학습용 인메모리 DB. 프로덕션에서는 ChromaDB, FAISS, Pinecone 등으로 대체)
* Orchestration: LangGraph (상태 기반 파이프라인), LangChain
* Web Framework: Streamlit (채팅 UI 및 백그라운드 시스템 로그 시각화)

## 4. 프로젝트 구조
```
life-os/
├── .env                  
├── requirements.txt      
├── main.py               
└── app/
    ├── __init__.py
    └── graph.py          
```
## 5. 핵심 준수 사항 (개발 가이드라인)

시스템의 무결성과 안정성을 위해 다음 규칙을 엄격히 준수합니다.

* 프롬프트 템플릿 보호: ChatPromptTemplate 구성 시 파이썬 f-string을 절대로 사용하지 않습니다. 장기 기억 텍스트 내에 포함될 수 있는 특수 기호나 중괄호({})가 템플릿 변수와 충돌하는 것을 원천 차단하기 위함입니다. 변수는 반드시 .invoke() 단계에서 딕셔너리로 주입합니다.
* 상태 참조 안정성: 상태 딕셔너리에 접근할 때 KeyError가 발생하는 것을 방지하기 위해, 반드시 `state.get("키", 기본값)` 방식을 사용하여 안전하게 참조합니다.
* 스트리밍 예외 처리: `app_graph.stream()` 결과를 순회할 때, 반환값이 None인 경우를 대비하여 `if not state_update: continue` 로직을 이중으로 적용하여 앱 크래시를 방지합니다.

## 6. 설치 및 실행 가이드

### 6.1. 환경 변수 설정
프로젝트 루트 경로에 .env 파일을 생성하고 API 키를 입력하십시오.
OPENAI_API_KEY=sk-your-api-key-here

### 6.2. 의존성 설치 및 실행
벡터 저장소 구동을 위해 최신 버전의 LangChain 패키지 설치가 권장됩니다.

uv venv
uv pip install -r requirements.txt
uv pip install -U langchain-core langchain-openai
uv run streamlit run main.py

## 7. 테스트 시나리오 및 검증 방법

1. 기억 주입 (Storage): 채팅창에 "나는 우유 알러지가 있어서 라떼를 마실 때는 무조건 오트 밀크로 바꿔야 해."라고 입력합니다.
2. 백그라운드 처리 확인: 우측 시스템 로그 패널에서 해당 취향 정보가 성공적으로 요약되어 벡터 DB에 저장되는 과정을 모니터링합니다.
3. 다른 주제의 대화: 시스템의 단기 기억(Context Window)을 밀어내기 위해 다른 일상적인 대화를 2~3회 진행합니다.
4. 초개인화 인출 (Retrieval): "나 내일 스타벅스 갈 건데 메뉴 하나 추천해 줘."라고 질문합니다.
5. 결과 검증: 시스템 로그에서 과거의 '우유 알러지 및 오트 밀크' 관련 기억이 성공적으로 인출(Retrieval)되는지 확인하고, 최종 답변이 오트 밀크가 적용된 메뉴를 제안하는지 검증합니다.

## 8. 실행 화면

<img width="1617" height="909" alt="스크린샷 2026-04-27 103525" src="https://github.com/user-attachments/assets/19e7fb23-9a9f-49ed-a16a-f5ad524e9686" />
