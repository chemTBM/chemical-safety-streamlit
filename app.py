import streamlit as st
import pandas as pd
import numpy as np
import joblib

# =========================
# 1) 모델 불러오기
# =========================
model = joblib.load("model_histgb_v2.pkl")
model_columns = joblib.load("model_columns_histgb_v2.pkl")

# =========================
# 2) 화면 제목
# =========================
st.title("화학안전 TBM 위험도 평가")
st.write("작업유형과 물질 위해성을 입력하면 위험도 점수를 계산합니다.")

# =========================
# 3) 사용자 입력 화면
# =========================
work_type = st.selectbox(
    "작업유형을 선택하세요",
    [
        "ROUTINE",
        "IDLE",
        "MAINTENANCE",
        "CLEANING",
        "STARTUP_SHUTDOWN",
        "HOT_WORK"
    ]
)

st.subheader("물질 위해성 입력")

flammable = st.selectbox(
    "인화성",
    [0, 1, 3, 6],
    help="없음=0, 낮음=1, 중간=3, 높음=6"
)

toxic_inhalation = st.selectbox(
    "급성 독성(흡입)",
    [0, 1, 3, 6],
    help="없음=0, 낮음=1, 중간=3, 높음=6"
)

corrosive = st.selectbox(
    "금속부식성 물질",
    [0, 1, 3, 6],
    help="없음=0, 낮음=1, 중간=3, 높음=6"
)

high_pressure_gas = st.selectbox(
    "고압가스",
    [0, 1, 3, 6],
    help="없음=0, 낮음=1, 중간=3, 높음=6"
)

# =========================
# 4) 입력값을 모델 컬럼 구조로 변환
# =========================
def make_input_data():
    input_df = pd.DataFrame(columns=model_columns)
    input_df.loc[0] = 0

    # 작업유형 더미변수 처리
    work_col = f"work_type_{work_type}"
    if work_col in input_df.columns:
        input_df.loc[0, work_col] = 1

    # 위해성 변수 입력
    if "인화성" in input_df.columns:
        input_df.loc[0, "인화성"] = flammable

    if "급성 독성(흡입)" in input_df.columns:
        input_df.loc[0, "급성 독성(흡입)"] = toxic_inhalation

    if "금속부식성 물질" in input_df.columns:
        input_df.loc[0, "금속부식성 물질"] = corrosive

    if "고압가스" in input_df.columns:
        input_df.loc[0, "고압가스"] = high_pressure_gas

    return input_df

# =========================
# 5) 점수 계산 함수
# =========================
def calculate_score(prob):
    score = prob * 100

    if score < 40:
        level = "🟢 저위험"
    elif score < 70:
        level = "🟡 중위험"
    else:
        level = "🔴 고위험"

    return score, level

# =========================
# 6) 버튼 클릭 시 예측
# =========================
if st.button("위험도 계산하기"):
    input_df = make_input_data()

    pred_prob = model.predict_proba(input_df)[0][1]
    score, level = calculate_score(pred_prob)

    st.subheader("위험도 평가 결과")
    st.metric("위험도 점수", f"{score:.1f}점")
    st.write(f"위험 수준: **{level}**")

    with st.expander("모델 입력값 확인"):
        st.dataframe(input_df)
