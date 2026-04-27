import streamlit as st

st.set_page_config(
    page_title="화학안전 신호등",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 화학안전 신호등")

st.write("작업유형과 취급물질을 입력하면 위험도를 보여줍니다.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    work_type = st.selectbox(
        "작업유형",
        ["HOT_WORK", "MAINTENANCE", "CLEANING", "TRANSFER"]
    )

with col2:
    material = st.text_input("취급물질 입력")

if st.button("분석하기"):
    st.subheader("결과")

    score = 82

    if score >= 75:
        st.error(f"🔴 위험도: {score}점")
    elif score >= 50:
        st.warning(f"🟠 위험도: {score}점")
    else:
        st.success(f"🟢 위험도: {score}점")

    st.write("주요 위험요인: 화기작업 + 인화성 물질")

    st.write("안전대책: 가스농도 측정, 환기, 화기작업허가 확인")