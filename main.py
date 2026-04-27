import streamlit as st
from app.graph import app_graph

st.set_page_config(page_title="라이프 OS 비서", layout="wide")

st.title("장기 기억 기반 초개인화 라이프 OS")
st.markdown("벡터 데이터베이스(Vector DB)를 활용하여 사용자의 취향과 사실을 영구적으로 기억하고, 이를 바탕으로 대화의 문맥을 개인화하는 지능형 비서입니다.")
st.divider()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "system_logs" not in st.session_state:
    st.session_state.system_logs = []

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("라이프 OS 대화창")
    
    with st.container(height=500):
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
    user_input = st.chat_input("비서에게 일정이나 취향을 이야기해 보십시오.")

with col2:
    st.subheader("시스템 백그라운드 처리 로그")
    st.markdown("에이전트가 기억을 검색하고 저장하는 과정을 실시간으로 보여줍니다.")
    
    with st.container(height=500, border=True):
        for log in st.session_state.system_logs:
            st.markdown(log)

#  st.rerun() 조기 호출을 제거하고, 입력 즉시 파이프라인으로 넘기도록 수정
if user_input:
    # 사용자 입력을 세션에 즉시 저장하고 화면에 임시 표시
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with col1:
        with st.chat_message("user"):
            st.write(user_input)

    initial_state = {
        "user_input": user_input,
        "retrieved_memories": [],
        "ai_response": "",
        "extracted_fact": ""
    }
    
    response_text = ""
    
    # 파이프라인 가동 및 시스템 로그 실시간 업데이트
    with col2:
        with st.spinner("과거 기억을 검색하고 데이터를 처리 중입니다..."):
            for output in app_graph.stream(initial_state):
                if not output:
                    continue
                    
                for node_name, state_update in output.items():
                    if not state_update:
                        continue
                        
                    if node_name == "retrieve":
                        memories = state_update.get("retrieved_memories", [])
                        if memories:
                            log_text = "[Retrieval] 관련 기억을 벡터 DB에서 성공적으로 불러왔습니다.\n"
                            for m in memories:
                                log_text += f"- {m}\n"
                            st.session_state.system_logs.append(log_text)
                        else:
                            st.session_state.system_logs.append("[Retrieval] 입력과 관련된 과거 기억이 없습니다.")
                            
                    elif node_name == "generate":
                        response_text = state_update.get("ai_response", "")
                        
                    elif node_name == "extract_and_store":
                        fact = state_update.get("extracted_fact", "")
                        if fact:
                            st.session_state.system_logs.append(f"[Storage] 새로운 정보가 벡터 DB에 저장되었습니다:\n- {fact}")
                        else:
                            st.session_state.system_logs.append("[Storage] 저장할 만한 새로운 개인 정보가 없습니다.")
                    
    # 모든 백그라운드 처리가 끝난 후 AI의 최종 답변을 세션에 추가하고 화면 갱신
    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
    st.rerun()