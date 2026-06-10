import streamlit as st
import pandas as pd
import numpy as np
import joblib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import os
from pathlib import Path
import textwrap
import streamlit.components.v1 as components
import re
from difflib import SequenceMatcher
from openai import OpenAI
from supabase import create_client
from io import BytesIO
from docxtpl import DocxTemplate

# =========================
# 1) 파일 불러오기
# =========================
model = joblib.load("model_histgb_v2.pkl")
model_columns = joblib.load("model_columns_histgb_v2.pkl")
mapping_df = pd.read_excel("hazard_mapping.xlsx")

# TBM 문구 DB 불러오기
risk_message_df = pd.read_excel("tbm_message_db.xlsx", sheet_name="risk_message_db")
accident_case_df = pd.read_excel("tbm_message_db.xlsx", sheet_name="accident_case_db")
final_result = pd.read_excel(
    "final_result.xlsx",
    dtype={"CHEMID": str}
)

final_result.columns = final_result.columns.str.strip()
final_result.columns = final_result.columns.str.strip()

# 엑셀 컬럼명 앞뒤 공백 제거
risk_message_df.columns = risk_message_df.columns.str.strip()
accident_case_df.columns = accident_case_df.columns.str.strip()


st.set_page_config(
    page_title="화학안전 TBM",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown(
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" />',
    unsafe_allow_html=True
)

st.markdown("""
<style>
/* 전체 배경 */
.stApp {
    background: #f1f5f9;
}

/* Streamlit 기본 여백 */
.block-container {
    max-width: 480px;
    padding-top: 3rem;
    padding-bottom: 7rem;
}

/* 상단 로고 영역 */
.login-header {
    text-align: center;
    margin-bottom: 18px;
}

.login-logo-row {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}

.login-logo-icon {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: #2170e4;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 19px;
    font-weight: 800;
}

.login-title {
    font-size: 25px;
    font-weight: 800;
    color: #091426;
}

.login-subtitle {
    font-size: 14px;
    color: #45474c;
}

/* 메인 카드 */
.login-card {
    background: #ffffff;
    border: 1px solid #c5c6cd;
    border-radius: 18px;
    padding: 28px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* 모드 카드 */
.mode-card-wrap {
    display: flex;
    gap: 10px;
    margin-bottom: 18px;
}

.mode-card {
    flex: 1;
    border-radius: 14px;
    padding: 16px 10px;
    text-align: center;
    border: 2px solid transparent;
    background: #f0edef;
    color: #45474c;
    font-weight: 700;
}

.mode-card-active {
    background: #2170e4;
    color: #ffffff;
    border: 2px solid #2170e4;
}

.mode-icon {
    font-size: 25px;
    margin-bottom: 5px;
}

.mode-label {
    font-size: 14px;
}

/* 안내 박스 */
.info-box {
    background: #f5f3f4;
    border: 1px solid rgba(197,198,205,0.5);
    border-radius: 14px;
    padding: 14px;
    display: flex;
    gap: 10px;
    margin-top: 18px;
    margin-bottom: 22px;
}

.info-icon {
    color: #ba1a1a;
    font-size: 20px;
    line-height: 1.4;
}

.info-text {
    color: #45474c;
    font-size: 13px;
    line-height: 1.55;
}

/* 입력창 */
div[data-baseweb="input"] {
    border-radius: 12px;
}

/* 기본 버튼 */
div.stButton > button {
    border-radius: 12px;
    font-size: 16px;
    font-weight: 800;
    background: #2170e4;
    color: white;
    border: none;
    min-height: 46px;
}

/* 하단 푸터 */
.login-footer {
    text-align: center;
    margin-top: 28px;
    color: #75777d;
    font-size: 12px;
}

/* 상단 그라데이션 */
.top-gradient-line {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #2170e4, #091426, #2170e4);
    z-index: 9999;
}

/* 하단 네비게이션 */
.bottom-nav-spacer {
    height: 88px;
}

/* =========================
   위험도 결과 화면 전체 스타일
========================= */


.result-page-topbar {
    position: sticky;
    top: 2px;
    z-index: 100;
    background: #fbf8fa;
    border-bottom: 1px solid #c5c6cd;
    padding: 14px 4px 12px 4px;
    margin-bottom: 20px;
}

.result-topbar-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.result-topbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.result-back-icon {
    width: 36px;
    height: 36px;
    border-radius: 999px;
    background: #f0edef;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #091426;
    font-weight: 800;
}

.result-app-title {
    font-size: 22px;
    font-weight: 800;
    color: #091426;
}

.result-report-label {
    font-size: 11px;
    letter-spacing: 0.08em;
    font-weight: 800;
    color: #75777d;
    margin-bottom: 4px;
}

.result-title {
    font-size: 30px;
    font-weight: 900;
    color: #091426;
    line-height: 1.25;
    margin-bottom: 6px;
}

.result-subtitle {
    font-size: 14px;
    color: #45474c;
    line-height: 1.45;
    margin-bottom: 18px;
}

.result-card {
    background: #ffffff;
    border: 1px solid #c5c6cd;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 16px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
}

.result-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 4px;
}

.result-card-icon {
    font-size: 20px;
}

.result-card-title {
    font-size: 18px;
    font-weight: 900;
    color: #091426;
}

.message-item {
    display: flex;
    gap: 10px;
    padding: 12px 0;
    border-bottom: 1px solid #e5e7eb;
}

.message-item:last-child {
    border-bottom: none;
}

.message-num {
    font-size: 13px;
    font-weight: 900;
    color: #ba1a1a;
    min-width: 26px;
}

.message-text {
    font-size: 14px;
    line-height: 1.5;
    color: #1b1b1d;
}

.measure-item {
    display: flex;
    gap: 10px;
    padding: 11px 0;
    border-bottom: 1px solid #e5e7eb;
}

.measure-item:last-child {
    border-bottom: none;
}

.measure-check {
    color: #2170e4;
    font-weight: 900;
    min-width: 20px;
}

.measure-text {
    font-size: 14px;
    line-height: 1.5;
    color: #1b1b1d;
}

.incident-placeholder {
    background: linear-gradient(135deg, #091426, #1e293b);
    color: white;
    border-radius: 14px;
    padding: 18px;
    margin-top: 12px;
}

.incident-placeholder-title {
    font-size: 15px;
    font-weight: 900;
    margin-bottom: 8px;
}

.incident-placeholder-desc {
    font-size: 13px;
    line-height: 1.45;
    opacity: 0.9;
}

.result-info-caption {
    font-size: 12px;
    color: #75777d;
    margin-top: 8px;
    margin-bottom: 14px;
}

/* 작업정보 입력 화면 */
.app-topbar {
    position: fixed;
    top: 4px;
    left: 50%;
    transform: translateX(-50%);

    width: min(480px, calc(100% - 28px));

    z-index: 9999;

    background: #fbf8fa;
    border-bottom: 1px solid #c5c6cd;

    padding: 14px 4px 12px 4px;

    box-shadow: 0 4px 14px rgba(15,23,42,0.08);
}

.topbar-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.topbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.back-btn {
    width: 36px;
    height: 36px;
    border-radius: 999px;
    background: #f0edef;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #091426;
    font-weight: 800;
}

.app-title {
    font-size: 22px;
    font-weight: 800;
    color: #091426;
}

.hero-title {
    font-size: 29px;
    line-height: 1.25;
    font-weight: 800;
    color: #091426;
    margin-bottom: 8px;
}

.hero-subtitle {
    font-size: 14px;
    color: #45474c;
    margin-bottom: 22px;
}


.field-label {
    font-size: 12px;
    letter-spacing: 0.05em;
    font-weight: 800;
    color: #45474c;
    margin-bottom: 8px;
}

.selected-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(33,112,228,0.10);
    color: #0058be;
    border: 1px solid rgba(0,88,190,0.20);
    font-size: 13px;
    font-weight: 700;
    margin-top: 8px;
}

.plant-image-card {
    margin-top: 24px;
    height: 180px;
    border-radius: 18px;
    overflow: hidden;
    background: linear-gradient(135deg, #091426, #2170e4);
    color: white;
    padding: 24px;
    display: flex;
    align-items: flex-end;
    font-size: 14px;
    line-height: 1.5;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.14);
}

.bottom-nav-spacer {
    height: 76px;
}

</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>

/* =========================
   TBM 체크리스트 화면
========================= */

.checklist-topbar {
    position: sticky;
    top: 4px;
    z-index: 100;
    background: #fbf8fa;
    border-bottom: 1px solid #c5c6cd;
    padding: 14px 4px 12px 4px;
    margin-bottom: 20px;
}

.checklist-topbar-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.checklist-topbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.checklist-back-icon {
    width: 36px;
    height: 36px;
    border-radius: 999px;
    background: #f0edef;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #091426;
    font-weight: 800;
}

.checklist-app-title {
    font-size: 22px;
    font-weight: 900;
    color: #091426;
}

.checklist-info-card {
    background: #ffffff;
    border: 1px solid #c5c6cd;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
}

.checklist-badge {
    display: inline-block;
    background: #d8e2ff;
    color: #0058be;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
}

.checklist-title {
    font-size: 25px;
    font-weight: 900;
    color: #091426;
    line-height: 1.25;
    margin-bottom: 6px;
}

.checklist-subtitle {
    font-size: 14px;
    color: #45474c;
    line-height: 1.45;
}

.checklist-section-title {
    font-size: 19px;
    font-weight: 900;
    color: #091426;
    margin: 22px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.checklist-item-card {
    background: #ffffff;
    border: 1px solid #c5c6cd;
    border-radius: 16px;
    padding: 14px 14px;
    margin-bottom: 10px;
    box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
}

.checklist-remark-card {
    background: #ffffff;
    border: 1px solid #c5c6cd;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 18px;
    box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
}

.checklist-small-label {
    font-size: 11px;
    color: #75777d;
    font-weight: 900;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}

.checklist-save-note {
    font-size: 12px;
    color: #75777d;
    line-height: 1.45;
    margin-top: 8px;
    margin-bottom: 12px;
}

</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>

/* =========================
   나의 작업일지 화면
========================= */


.journal-topbar {
    position: sticky;
    top: 4px;
    z-index: 100;
    background: #fbf8fa;
    border-bottom: 1px solid #c5c6cd;
    padding: 14px 4px 12px 4px;
    margin-bottom: 20px;
}

.journal-topbar-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.journal-topbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.journal-back-icon {
    width: 36px;
    height: 36px;
    border-radius: 999px;
    background: #f0edef;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #091426;
    font-weight: 800;
}

.journal-app-title {
    font-size: 22px;
    font-weight: 900;
    color: #091426;
}

.journal-title {
    font-size: 30px;
    font-weight: 900;
    color: #091426;
    line-height: 1.25;
    margin-bottom: 6px;
}

.journal-subtitle {
    font-size: 14px;
    color: #45474c;
    line-height: 1.45;
    margin-bottom: 20px;
}

.journal-card {
    background: #ffffff;
    border: 1px solid #c5c6cd;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 16px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
}

.journal-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
}

.journal-card-title {
    font-size: 18px;
    font-weight: 900;
    color: #091426;
}

.journal-summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #e5e7eb;
    padding: 10px 0;
    gap: 12px;
}

.journal-summary-label {
    font-size: 12px;
    color: #75777d;
    font-weight: 900;
    letter-spacing: 0.05em;
}

.journal-summary-value {
    font-size: 14px;
    color: #091426;
    font-weight: 800;
    text-align: right;
}

.journal-risk-badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 8px;
    background: #ffdad6;
    color: #93000a;
    font-size: 12px;
    font-weight: 900;
}

.journal-message-box {
    background: #f5f3f4;
    border-radius: 14px;
    padding: 14px;
    font-size: 14px;
    line-height: 1.5;
    color: #1b1b1d;
    margin-top: 12px;
}

.journal-small-label {
    font-size: 11px;
    color: #75777d;
    font-weight: 900;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}


.journal-submit-card {
    background: rgba(33, 112, 228, 0.06);
    border: 1px solid rgba(33, 112, 228, 0.25);
    border-radius: 18px;
    padding: 18px;
    margin-top: 20px;
    margin-bottom: 18px;
}

.journal-submit-title {
    font-size: 18px;
    font-weight: 900;
    color: #0058be;
    margin-bottom: 6px;
}

.journal-submit-desc {
    font-size: 14px;
    color: #45474c;
    line-height: 1.45;
}

</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>


/* =========================
   작업팀 접속 첫 화면
========================= */


.team-create-wrap {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 90px;
}

.team-create-btn {
    border: 1px solid rgba(255,255,255,0.5);
    border-radius: 999px;
    padding: 10px 18px;
    color: white;
    font-size: 14px;
    font-weight: 800;
    background: rgba(255,255,255,0.06);
}

.team-icon {
    width: 104px;
    height: 104px;
    border-radius: 999px;
    background: rgba(255,255,255,0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24px auto;
    font-size: 54px;
    box-shadow: 0 0 30px rgba(33,112,228,0.35);
}

.team-title {
    text-align: center;
    font-size: 34px;
    font-weight: 900;
    margin-bottom: 42px;
}

.team-helper {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin: 16px 0 18px 0;
    color: rgba(255,255,255,0.72);
    font-size: 13px;
}

.team-footer {
    text-align: center;
    margin-top: 58px;
    color: rgba(255,255,255,0.4);
    font-size: 11px;
    letter-spacing: 0.16em;
    font-weight: 800;
}

.team-plant-bg {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    height: 180px;
    opacity: 0.16;
    background: linear-gradient(to top, rgba(0,0,0,0.7), rgba(0,0,0,0));
    pointer-events: none;
}


/* 팀 접속 화면 입력창 */


.team-access-input div[data-baseweb="input"] {
    background: #ffffff !important;
    border-radius: 999px !important;
    min-height: 58px;
}

.team-access-input input {
    color: #091426 !important;
    font-size: 16px !important;
    font-weight: 700 !important;
}

.team-access-input input::placeholder {
    color: #75777d !important;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* =========================
   팀 생성 화면
========================= */


.create-team-topbar {
    position: sticky;
    top: 4px;
    z-index: 100;
    background: #fbf8fa;
    border-bottom: 1px solid #c5c6cd;
    padding: 14px 4px 12px 4px;
    margin-bottom: 20px;
}

.create-team-topbar-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.create-team-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.create-team-back {
    width: 36px;
    height: 36px;
    border-radius: 999px;
    background: #f0edef;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #091426;
    font-weight: 900;
}

.create-team-app-title {
    font-size: 22px;
    font-weight: 900;
    color: #091426;
}

.create-team-title {
    font-size: 30px;
    font-weight: 900;
    color: #091426;
    line-height: 1.25;
    margin-bottom: 6px;
}

.create-team-subtitle {
    font-size: 14px;
    color: #45474c;
    line-height: 1.45;
    margin-bottom: 22px;
}

.create-field-label {
    font-size: 12px;
    color: #45474c;
    font-weight: 900;
    letter-spacing: 0.05em;
    margin: 14px 0 8px 0;
}

.worker-chip {
    display: inline-flex;
    align-items: center;
    width: 100%;
    background: rgba(33,112,228,0.10);
    border: 1px solid rgba(33,112,228,0.25);
    color: #0058be;
    padding: 10px 13px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 900;
    margin-bottom: 6px;
}

.worker-list-title {
    font-size: 18px;
    font-weight: 900;
    color: #091426;
    margin-bottom: 12px;
}

.worker-chip-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
}

.worker-chip {
    display: inline-flex;
    align-items: center;
    background: rgba(33,112,228,0.10);
    border: 1px solid rgba(33,112,228,0.25);
    color: #0058be;
    padding: 7px 11px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 900;
}

.create-team-info-box {
    display: flex;
    gap: 10px;
    background: rgba(216,226,255,0.55);
    border: 1px solid #adc6ff;
    color: #004395;
    padding: 14px;
    border-radius: 14px;
    font-size: 13px;
    line-height: 1.45;
    margin-bottom: 16px;
}

.input-info-box {
    background: #f5f7fb;
    border: 1px solid #d6d9e0;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 16px;
    font-size: 15px;
    font-weight: 600;
    color: #31343a;
}

</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* Streamlit 기본 상단툴바를 피해서 앱 상단바 고정 */
.app-topbar,
.result-page-topbar,
.checklist-topbar,
.journal-topbar,
.create-team-topbar,
.manager-topbar {
    position: fixed !important;
    top: 76px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;

    width: min(480px, calc(100% - 28px)) !important;

    z-index: 9998 !important;

    margin: 0 !important;
    box-sizing: border-box !important;

    box-shadow: 0 4px 14px rgba(15,23,42,0.08);
}

/* 상단바가 fixed라서 본문이 가려지지 않도록 여백 추가 */
.fixed-topbar-spacer {
    height: 20px;
}

/* 관리자 대시보드 상단바는 기존 어두운 디자인 유지 */
.manager-topbar {
    background: #091426 !important;
    color: white !important;
    border-radius: 0 0 18px 18px !important;
    padding: 18px 16px !important;
}

/* 모바일에서 살짝 조정 */
@media (max-width: 640px) {
    .app-topbar,
    .result-page-topbar,
    .checklist-topbar,
    .journal-topbar,
    .create-team-topbar,
    .manager-topbar {
        top: 10px !important;
        width: calc(100% - 22px) !important;
    }

    .fixed-topbar-spacer {
        height: 20px;
    }
}
</style>
""", unsafe_allow_html=True)
# ========= 화면 구현 CCS =====

if "page" not in st.session_state:
    st.session_state.page = "team_access"

query_params = st.query_params

if query_params.get("page"):
    st.session_state.page = query_params.get("page")

if "mode" not in st.session_state:
    st.session_state.mode = "작업자"

if "work_data" not in st.session_state:
    st.session_state.work_data = {}

if "team_name" not in st.session_state:
    st.session_state.team_name = ""

if "team_password" not in st.session_state:
    st.session_state.team_password = ""

if "team_id" not in st.session_state:
    st.session_state.team_id = ""

if "created_teams" not in st.session_state:
    st.session_state.created_teams = {}

if "temp_workers" not in st.session_state:
    st.session_state.temp_workers = []

# =========================
# 안내 이미지 팝업 설정
# =========================
HELP_INFO_DIR = Path(__file__).parent / "help_info"

HELP_IMAGES = {
    "login": ["mode_choice"],
    "create_team": ["create_team"],
    "input": ["input_work"],
    "result": ["risk_1", "risk_2"],
    "checklist": ["checklist"],
    "journal": ["journal"],
    "manager": ["manager_1", "manager_2", "manager_3"],
}

def get_help_image_path(image_name):
    """
    확장자를 직접 쓰지 않아도 png, jpg, jpeg, webp 순서로 찾아줌
    """
    for ext in ["png", "jpg", "jpeg", "webp"]:
        path = HELP_INFO_DIR / f"{image_name}.{ext}"
        if path.exists():
            return path
    return None


@st.dialog("화면 안내", width="large")
def show_help_popup(page_key):
    image_list = HELP_IMAGES.get(page_key, [])

    if not image_list:
        st.warning("이 화면에 등록된 안내 이미지가 없습니다.")
        return

    slide_key = f"help_slide_{page_key}"

    if slide_key not in st.session_state:
        st.session_state[slide_key] = 0

    current_idx = st.session_state[slide_key]
    current_image_name = image_list[current_idx]
    image_path = get_help_image_path(current_image_name)

    if image_path is None:
        st.error(f"안내 이미지를 찾을 수 없습니다: {current_image_name}")
        st.caption(f"확인 경로: {HELP_INFO_DIR}")
    else:
        st.image(str(image_path), use_container_width=True)

    if len(image_list) > 1:
        col_prev, col_page, col_next = st.columns([1, 2, 1])

        with col_prev:
            if st.button("◀ 이전", use_container_width=True):
                st.session_state[slide_key] = (current_idx - 1) % len(image_list)
                st.session_state.active_help_page = page_key
                st.rerun()

        with col_page:
            st.markdown(
                f"<div style='text-align:center; padding-top:8px; font-weight:800;'>{current_idx + 1} / {len(image_list)}</div>",
                unsafe_allow_html=True
            )

        with col_next:
            if st.button("다음 ▶", use_container_width=True):
                st.session_state[slide_key] = (current_idx + 1) % len(image_list)
                st.session_state.active_help_page = page_key
                st.rerun()


def open_help_if_requested():
    help_page = st.query_params.get("help")

    if help_page in HELP_IMAGES:
        show_help_popup(help_page)

def show_active_help_popup():
    active_page = st.session_state.get("active_help_page")

    if active_page in HELP_IMAGES:
        show_help_popup(active_page)

def render_topbar_spacer():
    st.markdown('<div class="fixed-topbar-spacer"></div>', unsafe_allow_html=True)
    
def show_team_access():

    # Material Icons
    st.markdown("""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" />
""", unsafe_allow_html=True)

    # CSS
    st.markdown("""
<style>

.stApp {
    background: linear-gradient(180deg, #091426 0%, #0b2f7a 100%);
}

.block-container {
    max-width: 420px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

/* 상단 팀생성 버튼 */
.team-create-wrap {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 50px;
}

.team-create-btn {
    background: linear-gradient(180deg,#2170e4,#0058be);
    color: white;
    border-radius: 999px;
    padding: 12px 20px;
    font-weight: 900;
    font-size: 14px;
    box-shadow: 0 6px 16px rgba(0,0,0,0.22);
    display: inline-block;
}

/* 아이콘 */
.team-icon {
    width: 108px;
    height: 108px;
    border-radius: 999px;
    background: rgba(255,255,255,0.14);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 26px auto;
    box-shadow: 0 0 34px rgba(33,112,228,0.35);
}

.material-symbols-rounded {
    font-variation-settings:
    'FILL' 1,
    'wght' 500,
    'GRAD' 0,
    'opsz' 48;
}

.team-helmet-icon {
    font-size: 56px;
    color: white;
}

/* 제목 */
.team-title {
    text-align: center;
    color: white;
    font-size: 34px;
    font-weight: 900;
    margin-bottom: 42px;
}

/* 입력창 */
div[data-baseweb="input"] {
    background: white !important;
    border-radius: 999px !important;
    min-height: 58px !important;
}

div[data-baseweb="input"] input {
    height: 58px !important;
    color: #091426 !important;
    font-weight: 700 !important;
    font-size: 16px !important;
}

/* 버튼 */
div.stButton > button {
    border-radius: 999px;
    font-size: 17px;
    font-weight: 900;
    background: linear-gradient(180deg, #2170e4 0%, #0058be 100%);
    color: white;
    border: none;
    box-shadow: 0 6px 16px rgba(0,0,0,0.22);
    margin-top: 8px;
}

/* 안내문구 */
.team-helper {
    text-align: center;
    color: rgba(255,255,255,0.72);
    font-size: 13px;
    margin: 16px 0 20px 0;
    line-height: 1.5;
}

/* 하단 */
.team-footer {
    text-align: center;
    color: rgba(255,255,255,0.4);
    font-size: 11px;
    letter-spacing: 0.16em;
    font-weight: 800;
    margin-top: 48px;
}

</style>
""", unsafe_allow_html=True)

    # 상단 팀 생성 버튼
    st.markdown("""
<div class="team-create-wrap">
    <a href="?page=create_team" target="_self" style="text-decoration:none;">
        <div class="team-create-btn">+ 팀 생성</div>
    </a>
</div>
""", unsafe_allow_html=True)

    # 아이콘 + 제목
    st.markdown("""
<div class="team-icon">
    <span class="material-symbols-rounded team-helmet-icon">
        engineering
    </span>
</div>

<div class="team-title">작업팀 접속</div>
""", unsafe_allow_html=True)

    # 입력창
    team_name = st.text_input(
        "팀명",
        placeholder="팀명을 입력하세요",
        label_visibility="collapsed",
        key="team_name_input"
    )

    team_password = st.text_input(
        "팀 비밀번호",
        placeholder="비밀번호를 입력하세요",
        type="password",
        label_visibility="collapsed",
        key="team_password_input"
    )

    # 안내문구
    st.markdown("""
<div class="team-helper">
🛡️ 안전관리자가 생성한 팀정보로 접속합니다.
</div>
""", unsafe_allow_html=True)

    # 접속 버튼
    if st.button(
        "TBM 접속하기",
        key="team_access_submit",
        use_container_width=True
    ):
        if not team_name.strip():
            st.warning("팀명을 입력해 주세요.")

        elif not team_password.strip():
            st.warning("비밀번호를 입력해 주세요.")

        else:
            team = login_team(
                team_name.strip(),
                team_password.strip()
            )
            if not team:
                st.error("팀명 또는 비밀번호가 일치하지 않습니다.")
                return

            st.session_state.team_name = team["team_name"]
            st.session_state.team_password = team_password.strip()
            st.session_state.team_id = team["id"]            

            st.query_params.clear()

            st.session_state.page = "login"
            st.rerun()

    # 하단 문구
    st.markdown("""
<div class="team-footer">
SAFETY TBM SYSTEM
</div>
""", unsafe_allow_html=True)

def show_login():

    # =========================
    # 상단바
    # =========================
    topbar_html = '<div class="create-team-topbar"><div class="create-team-topbar-row"><div class="create-team-left"><a href="?page=team_access" target="_self" style="text-decoration:none;"><div class="create-team-back">←</div></a><div class="create-team-app-title">작업 모드 선택</div></div><a href="?page=login&help=login" target="_self" style="text-decoration:none;"><div style="font-size:22px; color:#45474c;">ℹ️</div></a></div></div>'
    st.markdown(topbar_html, unsafe_allow_html=True)
    render_topbar_spacer()

    # =========================
    # 로그인 헤더
    # =========================
    login_header_html = '<div class="login-header"><div class="login-logo-row"><div class="login-logo-icon">✓</div><div class="login-title">Safety TBM</div></div><div class="login-subtitle">안전한 작업의 시작, 스마트 안전관리 플랫폼</div></div>'
    st.markdown(login_header_html, unsafe_allow_html=True)


    # =========================
    # 모드 선택
    # =========================
    mode = st.radio(
        "접속 모드",
        ["작업자", "안전관리자"],
        horizontal=True,
        label_visibility="collapsed",
        key="login_mode_radio"
    )

    # =========================
    # 모드 카드 UI
    # =========================
    if mode == "작업자":
        mode_card_html = '<div class="mode-card-wrap"><div class="mode-card mode-card-active"><div class="mode-icon">👷</div><div class="mode-label">작업자 모드</div></div><div class="mode-card"><div class="mode-icon">🛡️</div><div class="mode-label">안전관리자 모드</div></div></div>'
    else:
        mode_card_html = '<div class="mode-card-wrap"><div class="mode-card"><div class="mode-icon">👷</div><div class="mode-label">작업자 모드</div></div><div class="mode-card mode-card-active"><div class="mode-icon">🛡️</div><div class="mode-label">안전관리자 모드</div></div></div>'

    st.markdown(mode_card_html, unsafe_allow_html=True)

    # =========================
    # 입력 영역
    # =========================
    if mode == "작업자":
        worker_name = st.text_input(
            "작업자명",
            placeholder="성명을 입력하세요",
            key="login_worker_name"
        )
        
        today_tasks = get_today_work_tasks(
            st.session_state.get("team_id", "")
        )
        selected_task = None
        if today_tasks:
            task_options = {
                f'{task.get("work_name", "-")} / {task.get("scheduled_time", "-")}': task
                for task in today_tasks
        }
        
            selected_task_label = st.selectbox(
                "작업명 선택",
                list(task_options.keys()),
                key="login_selected_task"
            )
            selected_task = task_options[selected_task_label]
        
        else:
            st.warning("안전관리자가 등록한 오늘 작업이 없습니다.")
        
        

        is_tbm_leader = st.checkbox(
            "TBM 리더입니다",
            key="is_tbm_leader"
        )

        leader_department = ""
        leader_position = ""
        

        if is_tbm_leader:

            leader_department = st.text_input(
                "소속",
                placeholder="예: 생산1팀",
                key="leader_department"
            )

            leader_position = st.text_input(
                "직책",
                placeholder="예: 반장",
                key="leader_position"
            )


        manager_password_input = ""

    else:
        manager_password_input = st.text_input(
            "안전관리자 모드 진입 비밀번호",
            placeholder="팀 생성 시 등록한 안전관리자 비밀번호 입력",
            type="password",
            key="login_manager_password"
        )

        worker_name = ""
        work_name = "안전관리자 대시보드"

    # =========================
    # 안내 문구
    # =========================
    info_box_html = '<div class="info-box"><div class="info-icon">ℹ</div><div class="info-text">본 시스템은 산업안전보건법에 따른 <b>TBM(Tool Box Meeting)</b>의 디지털 기록을 위해 사용됩니다. 정확한 정보를 입력해 주시기 바랍니다.</div></div>'
    st.markdown(info_box_html, unsafe_allow_html=True)

    # =========================
    # 시작 버튼
    # =========================
    if st.button("TBM 시작  ▶", key="login_start_btn", use_container_width=True):
        st.session_state.work_data["접속시간"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


        if mode == "작업자":

            if not worker_name.strip():
                st.warning("작업자명을 입력해 주세요.")
                return

            if selected_task is None:
                st.warning("등록된 작업을 선택해 주세요.")
                return

            st.session_state.mode = mode
            st.session_state.work_data["작업자명"] = worker_name.strip()
            st.session_state.work_data["작업명"] = selected_task.get("work_name", "")
            st.session_state.work_data["작업내용"] = selected_task.get("work_content", "")
            st.session_state.work_data["작업장소"] = selected_task.get("work_location", "")
            st.session_state.work_data["TBM장소"] = selected_task.get("tbm_place", "")
            st.session_state.work_data["예정시간"] = selected_task.get("scheduled_time", "")
            st.session_state.work_data["task_id"] = selected_task.get("id", "")
            st.session_state.work_data["접속모드"] = mode
            st.session_state.work_data["접속시간"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            st.session_state.work_data["TBM리더여부"] = is_tbm_leader
            st.session_state.work_data["리더소속"] = leader_department.strip()
            st.session_state.work_data["리더직책"] = leader_position.strip()
            st.session_state.work_data["리더성명"] = worker_name.strip() if is_tbm_leader else ""

            if st.session_state.work_data.get("TBM리더여부", False):
                st.session_state.work_data["TBM시작시간"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            st.query_params.clear()

            st.session_state.page = "input"
            st.rerun()

        else:

            if not manager_password_input.strip():
                st.warning("안전관리자 비밀번호를 입력해 주세요.")
                return

            result = (
                supabase.table("teams")
                .select("*")
                .eq("id", st.session_state.team_id)
                .execute()
            )

            if not result.data:
                st.error("팀 정보를 찾을 수 없습니다.")
                return

            team_info = result.data[0]
            saved_manager_password = team_info.get("manager_password", "")

            if manager_password_input.strip() != saved_manager_password:
                st.error("안전관리자 비밀번호가 일치하지 않습니다.")
                return

            st.session_state.mode = mode
            st.session_state.manager_name = team_info.get("manager_name", "안전관리자")

            st.session_state.work_data["작업자명"] = st.session_state.get("manager_name", "안전관리자")
            st.session_state.work_data["작업명"] = "안전관리자 대시보드"
            st.session_state.work_data["접속모드"] = mode
            st.session_state.work_data["접속시간"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            st.query_params.clear()

            st.session_state.page = "manager"
            st.rerun()


    show_bottom_nav()
    # =========================
    # 푸터
    # =========================
    footer_html = '<div class="login-footer">이용약관 · 개인정보처리방침<br>© 2026 Korea Environment Corporation. All Rights Reserved.</div>'
    st.markdown(footer_html, unsafe_allow_html=True)

def show_create_team():
    topbar_html = '<div class="create-team-topbar"><div class="create-team-topbar-row"><div class="create-team-left"><a href="?page=team_access" target="_self" style="text-decoration:none;"><div class="create-team-back">←</div></a><div class="create-team-app-title">팀 생성</div></div><a href="?page=create_team&help=create_team" target="_self" style="text-decoration:none;"><div style="font-size:22px; color:#45474c;">ℹ️</div></a></div></div>'
    st.markdown(topbar_html, unsafe_allow_html=True)
    render_topbar_spacer()

    st.markdown("""
<div class="create-team-title">새 TBM 작업방 만들기</div>
<div class="create-team-subtitle">
    안전관리자가 팀명, 비밀번호, 작업자 명단을 등록합니다.
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="create-field-label">팀명</div>', unsafe_allow_html=True)
    team_name = st.text_input(
        "팀명",
        placeholder="예: OO공장 정비1팀",
        label_visibility="collapsed",
        key="create_team_name"
    )

    st.markdown('<div class="create-field-label">팀 비밀번호</div>', unsafe_allow_html=True)
    team_password = st.text_input(
        "팀 비밀번호",
        placeholder="작업자에게 공유할 비밀번호 입력",
        type="password",
        label_visibility="collapsed",
        key="create_team_password"
    )

    st.markdown('<div class="create-field-label">안전관리자 비밀번호</div>', unsafe_allow_html=True)
    manager_password = st.text_input(
        "안전관리자 비밀번호",
        placeholder="안전관리자 모드 진입 비밀번호",
        type="password",
        label_visibility="collapsed",
        key="create_manager_password"
    )

    st.markdown('<div class="create-field-label">안전관리자 비밀번호 확인</div>', unsafe_allow_html=True)
    manager_password_confirm = st.text_input(
        "안전관리자 비밀번호 확인",
        placeholder="비밀번호를 한 번 더 입력하세요",
        type="password",
        label_visibility="collapsed",
        key="create_manager_password_confirm"
    )

    st.markdown('<div class="create-field-label">안전관리자명</div>', unsafe_allow_html=True)
    manager_name = st.text_input(
        "안전관리자명",
        placeholder="예: 홍길동",
        label_visibility="collapsed",
        key="create_manager_name"
    )

    st.markdown("""
<div class="worker-list-title" style="margin-top:24px;">작업자 명단 등록</div>
""", unsafe_allow_html=True)

    col_worker, col_add = st.columns([4, 1])

    with col_worker:
        worker_name = st.text_input(
            "작업자 이름 입력",
            placeholder="작업자 이름 입력",
            label_visibility="collapsed",
            key="worker_name_input"
        )

    with col_add:
        if st.button("추가", key="add_worker_btn", use_container_width=True):
            if not worker_name.strip():
                st.warning("작업자 이름을 입력해 주세요.")
            elif worker_name.strip() in st.session_state.temp_workers:
                st.warning("이미 등록된 작업자입니다.")
            else:
                st.session_state.temp_workers.append(worker_name.strip())
                st.rerun()

    if st.session_state.temp_workers:
        for idx, worker in enumerate(st.session_state.temp_workers):
            col_name, col_del = st.columns([5, 1])

            with col_name:
                st.markdown(
                    f'<div class="worker-chip">{worker}</div>',
                    unsafe_allow_html=True
                )

            with col_del:
                if st.button("X", key=f"delete_worker_{idx}"):
                    st.session_state.temp_workers.remove(worker)
                    st.rerun()
    else:
        st.caption("아직 등록된 작업자가 없습니다.")

    st.markdown("""
<div class="create-team-info-box">
ℹ️ 등록된 작업자만 해당 팀의 작업자로 선택할 수 있습니다.
</div>
""", unsafe_allow_html=True)

    if st.button("작업팀 생성하기", key="create_team_submit", use_container_width=True):
        if not team_name.strip():
            st.warning("팀명을 입력해 주세요.")

        elif not team_password.strip():
            st.warning("팀 비밀번호를 입력해 주세요.")

        elif not manager_password.strip():
            st.warning("안전관리자 비밀번호를 입력해 주세요.")

        elif not manager_password_confirm.strip():
            st.warning("안전관리자 비밀번호 확인을 입력해 주세요.")

        elif manager_password.strip() != manager_password_confirm.strip():
            st.error("안전관리자 비밀번호와 비밀번호 확인이 일치하지 않습니다.")

        elif not manager_name.strip():
            st.warning("안전관리자명을 입력해 주세요.")

        elif not st.session_state.temp_workers:
            st.warning("작업자 명단을 1명 이상 등록해 주세요.")

        else:
            try:
                saved_team = create_team(
                    team_name=team_name.strip(),
                    team_password=team_password.strip(),
                    manager_name=manager_name.strip(),
                    manager_password=manager_password.strip(),
                    workers=st.session_state.temp_workers.copy()
                )

                if not saved_team:
                    st.error("DB 저장 결과가 비어 있습니다.")
                    return

                st.session_state.team_name = team_name.strip()
                st.session_state.team_password = team_password.strip()
                st.session_state.team_id = saved_team[0]["id"]
                st.session_state.manager_name = manager_name.strip()
                st.session_state.manager_password = manager_password.strip()
                st.session_state.temp_workers = []

                st.success("작업팀이 생성되었습니다.")
                st.session_state.page = "team_access"
                st.rerun()

            except Exception as e:
                if "duplicate key value" in str(e):
                    st.error("이미 존재하는 팀명입니다. 다른 팀명을 입력해 주세요.")
                else:
                    st.error("Supabase 저장 중 오류가 발생했습니다.")
                    st.write(str(e))
                return

def show_work_input():

    # =========================
    # 상단바
    # =========================
    topbar_html = '<div class="app-topbar"><div class="topbar-row"><div class="topbar-left"><a href="?page=login" target="_self" style="text-decoration:none;"><div class="back-btn">←</div></a><div class="app-title">Safety TBM</div></div><a href="?page=input&help=input" target="_self" style="text-decoration:none;"><div style="font-size:22px; color:#45474c;">ℹ️</div></a></div></div>'
    st.markdown(topbar_html, unsafe_allow_html=True)
    render_topbar_spacer()

    st.markdown("""
    <div>
        <div class="hero-title">오늘의 작업 정보를 확인하세요.</div>
        <div class="hero-subtitle">안전관리자가 등록한 작업 정보를 기준으로 TBM을 진행합니다.</div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # 선택 작업 정보 자동 표시
    # =========================
    work_name = st.session_state.work_data.get("작업명", "-")
    work_content = st.session_state.work_data.get("작업내용", "-")
    work_location = st.session_state.work_data.get("작업장소", "-")
    scheduled_time = st.session_state.work_data.get("예정시간", "-")
    tbm_place = st.session_state.work_data.get("TBM장소", "-")

    st.markdown(f"""
<div class="result-card">
    <div class="result-card-header">
        <div class="result-card-icon">📋</div>
        <div class="result-card-title">선택한 작업 정보</div>
    </div>
    <div class="message-text">
        <b>작업명</b> : {work_name}<br>
        <b>작업내용</b> : {work_content}<br>
        <b>작업장소</b> : {work_location}<br>
        <b>예정시간</b> : {scheduled_time}<br>
        <b>TBM 장소</b> : {tbm_place}
    </div>
</div>
""", unsafe_allow_html=True)

    # =========================
    # 작업 유형
    # =========================
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown('<div class="field-label">작업 유형</div>', unsafe_allow_html=True)

    work_type_display = st.selectbox(
        "작업 유형",
        [
            "정기작업",
            "비작업(순찰·경비)",
            "유지보수",
            "화기작업",
            "시운전·정지",
            "세척작업"
        ],
        label_visibility="collapsed"
    )

    # =========================
    # 작업 시간
    # =========================
    time_slot, current_dt = get_current_time_slot()
    current_time = current_dt.strftime("%Y-%m-%d %H:%M")

    st.markdown('<div class="input-card input-card-muted">', unsafe_allow_html=True)
    st.markdown('<div class="field-label">작업 시간 자동 입력</div>', unsafe_allow_html=True)

    st.text_input(
        "작업 시간",
        value=f"{current_time} · {time_slot}",
        disabled=True,
        label_visibility="collapsed"
    )

    # =========================
    # 취급물질 입력
    # =========================
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown('<div class="field-label">취급물질 입력</div>', unsafe_allow_html=True)

    chemical = st.text_input(
        "취급물질",
        placeholder="화학물질명을 입력하세요. 예: 염산, 황산, 암모니아",
        label_visibility="collapsed"
    )

    # =========================
    # 위험도 분석 버튼
    # =========================
    if st.button("⚠️ 위험도 분석하기", use_container_width=True):

        if not work_location or work_location == "-":
            st.warning("선택한 작업의 작업장소 정보가 없습니다. 안전관리자에게 작업정보를 확인해 주세요.")
            return

        if not chemical.strip():
            st.warning("취급물질을 입력해 주세요.")
            return

        work_type_map = {
            "정기작업": "ROUTINE",
            "비작업(순찰·경비)": "IDLE",
            "유지보수": "MAINTENANCE",
            "화기작업": "HOT_WORK",
            "시운전·정지": "STARTUP_SHUTDOWN",
            "세척작업": "CLEANING"
        }

        work_type = work_type_map[work_type_display]

        st.session_state.work_data.update({
            "작업명": work_name,
            "작업내용": work_content,
            "작업장소": work_location,
            "예정시간": scheduled_time,
            "TBM장소": tbm_place,
            "작업유형": work_type_display,
            "작업유형_모델값": work_type,
            "취급물질": chemical,
            "작업시간": current_time,
            "작업시간대": time_slot
        })

        try:
            chem_id, chem_name, err = get_chemid_by_name(
                chemical,
                SERVICE_KEY
            )

            if err:
                st.error(err)
                return

            status_code, detail_text = get_hazard_by_chemid(
                chem_id,
                SERVICE_KEY
            )

            if status_code != 200:
                st.error(f"상세 위해성 API 호출 실패: {status_code}")
                return

            classification_text = extract_classification_text(detail_text)

            hazard_scores = map_hazard_scores_by_excel(
                classification_text,
                mapping_df
            )

            st.session_state.hazard_scores = hazard_scores
            st.session_state.chem_id = chem_id
            st.session_state.chem_name = chem_name
            st.session_state.classification_text = classification_text

            input_df = make_input_data(work_type, time_slot)
            pred_prob = model.predict_proba(input_df)[0][1]

            score, level, detail = calculate_final_score(
                input_df=input_df,
                pred_prob=pred_prob,
                work_type=work_type,
                time_slot=time_slot,
                chem_info_missing=0
            )

            st.session_state.result = {
                "score": score,
                "level": level,
                "detail": detail,
                "input_df": input_df,
                "chem_name": chem_name,
                "chem_id": chem_id,
                "hazard_scores": hazard_scores,
                "classification_text": classification_text,
                "작업명": work_name,
                "작업내용": work_content,
                "작업장소": work_location,
                "예정시간": scheduled_time,
                "TBM장소": tbm_place,
                "작업유형": work_type_display,
                "작업유형_모델값": work_type,
                "취급물질": chemical,
                "작업시간": current_time,
                "작업시간대": time_slot,
                "task_id": st.session_state.work_data.get("task_id", "")
            }

            st.session_state.risk_score = score
            st.session_state.page = "result"
            st.rerun()

        except Exception as e:
            st.error("위험도 분석 중 오류가 발생했습니다.")
            st.exception(e)

    st.markdown("""
    <div class="plant-image-card">
        실시간 현장 데이터 기반 위험 분석 알고리즘이 가동 중입니다.
    </div>
    """, unsafe_allow_html=True)

    show_bottom_nav()
def show_bottom_nav():

    current_page = st.session_state.get("page", "input")
    current_mode = st.session_state.get("mode", "작업자")

    last_page = "manager" if current_mode == "안전관리자" else "journal"
    last_icon = "▦" if current_mode == "안전관리자" else "✎"

    def nav_class(page_name):
        return "bottom-nav-item active" if current_page == page_name else "bottom-nav-item"

    st.markdown(f"""
<style>
.bottom-nav-spacer {{
    height: 88px;
}}

.bottom-nav-fixed {{
    position: fixed;
    left: 50%;
    bottom: 14px;
    transform: translateX(-50%);
    width: min(440px, calc(100% - 28px));
    height: 64px;
    background: #fbf8fa;
    border: 1px solid #c5c6cd;
    border-radius: 22px;
    box-shadow: 0 10px 30px rgba(15,23,42,0.18);
    z-index: 9999;
    overflow: hidden;

    display: grid;
    grid-template-columns: repeat(4, 1fr);
}}

.bottom-nav-item {{
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none !important;
    color: #8a8f98 !important;
    font-size: 28px;
    font-weight: 900;
    height: 64px;
    border-right: 1px solid #c5c6cd;
    background: #fbf8fa;
}}

.bottom-nav-item:last-child {{
    border-right: none;
}}

.bottom-nav-item.active {{
    color: #0b3fa5 !important;
    background: rgba(11,63,165,0.06);
}}

.bottom-nav-item:hover {{
    color: #0b3fa5 !important;
    background: rgba(11,63,165,0.06);
}}

@media (max-width: 640px) {{
    .bottom-nav-fixed {{
        width: calc(100% - 22px);
        bottom: 10px;
        height: 60px;
        border-radius: 20px;
    }}

    .bottom-nav-item {{
        height: 60px;
        font-size: 24px;
    }}
}}
</style>

<div class="bottom-nav-spacer"></div>

<div class="bottom-nav-fixed">
    <a href="?page=input" target="_self" class="{nav_class("input")}">⌂</a>
    <a href="?page=result" target="_self" class="{nav_class("result")}">🚦</a>
    <a href="?page=checklist" target="_self" class="{nav_class("checklist")}">☑</a>
    <a href="?page={last_page}" target="_self" class="{nav_class(last_page)}">{last_icon}</a>
</div>
""", unsafe_allow_html=True)

def split_db_text(value):
    """
    엑셀 셀 안에 여러 문장이 들어간 경우 보기 좋게 나누기 위한 함수.
    줄바꿈, |, ; 기준으로 분리한다.
    """
    if pd.isna(value):
        return []

    text = str(value).strip()

    if not text or text.lower() == "nan":
        return []

    for sep in ["|", ";", "\n", "\r"]:
        text = text.replace(sep, "\n")

    items = [
        x.strip()
        for x in text.split("\n")
        if x.strip()
    ]

    return items if items else [str(value).strip()]


def get_score_style(score):
    if score < 40:
        return {
            "level_text": "안전유의",
            "score_color": "#22c55e",
            "badge_bg": "#22c55e",
            "badge_color": "#111827",
            "green_class": "traffic-light green-on",
            "yellow_class": "traffic-light",
            "red_class": "traffic-light"
        }
    elif score < 70:
        return {
            "level_text": "작업주의",
            "score_color": "#facc15",
            "badge_bg": "#facc15",
            "badge_color": "#111827",
            "green_class": "traffic-light",
            "yellow_class": "traffic-light yellow-on",
            "red_class": "traffic-light"
        }
    else:
        return {
            "level_text": "위험경고",
            "score_color": "#ef4444",
            "badge_bg": "#ef4444",
            "badge_color": "#ffffff",
            "green_class": "traffic-light",
            "yellow_class": "traffic-light",
            "red_class": "traffic-light red-on"
        }


def get_risk_and_measure_messages(result):
    """
    AI 분석 주요 위험요인과 안전 및 사고 예방대책 문구를 DB에서 추출.
    """

    hazard_scores = result.get("hazard_scores", {})
    work_type_display = result.get("작업유형", "")

    material_risk_items = []
    work_risk_items = []

    material_measure_items = []
    work_measure_items = []

    # =========================
    # 1) risk_message_db: 물질군 기준 매칭
    # =========================
    active_hazards = []

    for hazard_name, hazard_score in hazard_scores.items():
        try:
            score_value = float(hazard_score)
        except Exception:
            score_value = 0

        if score_value > 0:
            active_hazards.append(str(hazard_name).strip())

    if active_hazards:
        temp_risk_df = risk_message_df.copy()
        temp_risk_df["물질군"] = temp_risk_df["물질군"].astype(str).str.strip()

        matched_risk = temp_risk_df[
            temp_risk_df["물질군"].isin(active_hazards)
        ]

        for _, row in matched_risk.iterrows():
            material_risk_items.extend(
    split_db_text(row.get("유해위험요인", ""))
)
            material_measure_items.extend(
    split_db_text(row.get("취급시 주의사항 및 예방조치", ""))
)

    # =========================
    # 2) accident_case_db: 작업명 기준 매칭
    # =========================
    temp_accident_df = accident_case_df.copy()

    if "작업명" in temp_accident_df.columns:
        work_col = "작업명"
    elif "작업유형" in temp_accident_df.columns:
        work_col = "작업유형"
    else:
        work_col = None

    if work_col:
        temp_accident_df[work_col] = temp_accident_df[work_col].astype(str).str.strip()

        matched_work = temp_accident_df[
            temp_accident_df[work_col] == str(work_type_display).strip()
        ]

        for _, row in matched_work.iterrows():
            work_risk_items.extend(
    split_db_text(row.get("주요 위험요인", ""))
)
            work_measure_items.extend(
    split_db_text(row.get("안전대책", ""))
)

    # =========================
    # 3) 90% 이상 유사 문구 중복 제거
    # =========================
    def remove_similar_text(items, similarity_threshold=0.90):
        cleaned = []
        seen_keys = []

        def normalize_for_similarity(value):
            text = str(value)

            text = (
                text
                .replace("\n", " ")
                .replace("\r", " ")
                .replace("\t", " ")
                .replace("\u00a0", " ")
                .replace("\u3000", " ")
            )

            text = " ".join(text.split())
            key = re.sub(r"\d+", "", text)

            key = (
                key
                .replace(" ", "")
                .replace(",", "")
                .replace("，", "")
                .replace(".", "")
                .replace("。", "")
                .replace("·", "")
                .replace("ㆍ", "")
                .replace("-", "")
                .replace("–", "")
                .replace("~", "")
                .replace("(", "")
                .replace(")", "")
                .replace("[", "")
                .replace("]", "")
                .replace(":", "")
                .replace(";", "")
                .strip()
            )

            return text, key

        for item in items:
            if item is None:
                continue

            try:
                if pd.isna(item):
                    continue
            except Exception:
                pass

            text, key = normalize_for_similarity(item)

            if not text or text.lower() == "nan":
                continue

            is_duplicate = False

            for old_key in seen_keys:
                similarity = SequenceMatcher(None, key, old_key).ratio()

                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_keys.append(key)
                cleaned.append(text)

        return cleaned

    material_risk_items = remove_similar_text(material_risk_items, similarity_threshold=0.90)
    work_risk_items = remove_similar_text(work_risk_items, similarity_threshold=0.90)
    material_measure_items = remove_similar_text(material_measure_items, similarity_threshold=0.90)
    work_measure_items = remove_similar_text(work_measure_items, similarity_threshold=0.90)

    # =========================
    # 4) 기본 문구
    # =========================
    if not material_risk_items:
        material_risk_items = [
            "입력된 물질정보를 기준으로 누출, 접촉, 흡입 가능성을 확인해야 합니다.."
        ]

    if not work_risk_items:
        work_risk_items = [
            "입력된 작업유형을 기준으로 오조작, 점화원, 작업환경 위험요인을 확인해야 합니다."
        ]

    if not material_measure_items:
        material_measure_items = [
            "작업 전 MSDS 확인, 보호구 착용, 환기 상태 확인이 필요합니다."
        ]

    if not work_measure_items:
        work_measure_items = [
            "작업 전 안전절차 확인, 작업구역 통제, 비상대응 절차 숙지가 필요합니다."
        ]

    return (
    material_risk_items[:5],
    work_risk_items[:5],
    material_measure_items[:5],
    work_measure_items[:5]
)

def generate_ai_text(
    material_risk_items,
    work_risk_items,
    material_measure_items,
    work_measure_items,
    similar_text
):
    material_risk_source = "\n".join(material_risk_items)
    work_risk_source = "\n".join(work_risk_items)
    material_measure_source = "\n".join(material_measure_items)
    work_measure_source = "\n".join(work_measure_items)

    prompt = f"""
너는 화학안전 TBM 전문가다.

아래 원문을 바탕으로 작업 전 TBM 안내문을 작성하라.

[공통 작성 원칙]
- 제공된 원문 내용만 사용할 것
- 새로운 위험요인, 사고사례, 법령, 수치를 만들지 말 것
- 같은 의미의 문장을 반복하지 말 것
- 작업반장이 작업 전 1분 브리핑하듯 작성할 것
- 어려운 전문용어 사용을 최소화할 것
- 작업자가 바로 이해할 수 있도록 짧고 명확하게 작성할 것

[AI 주요 위험요인 작성 원칙]
- 물질군 위험요인과 작업유형 위험요인을 따로 나열하지 말 것
- 반드시 물질의 위험성과 작업유형의 위험상황을 한 문장 안에서 연결해서 설명할 것
- 작업유형과 직접 관련된 위험상황 중심으로 작성할 것
- 일반적인 화학안전 설명보다 현재 작업상황 중심으로 작성할 것
- 개별 위험요인을 단순 나열하지 말고 작업 흐름처럼 연결해서 설명할 것
- 각 항목은 최대 3개까지만 작성할 것
- 한 문장에는 최대 2개의 위험요인만 포함할 것

[안전 및 예방조치 작성 원칙]
- 작업자가 바로 실행할 수 있는 행동 중심으로 작성할 것
- 물질 특성과 작업유형 상황을 함께 고려한 예방조치로 작성할 것
- 각 항목은 최대 3개까지만 작성할 것
- 한 문장에는 최대 2개의 조치만 포함할 것

[유사사고 작성 원칙]
- 사고일시, 지역, 작업유형을 반드시 포함할 것
- 유사사고 문장은 “2021년 5월 충청북도 제천시 소재 사업장에서 정기작업 중 ...” 형태를 기본으로 작성할 것
- 사고내용은 삭제하거나 과도하게 축약하지 말 것
- 사고내용의 핵심 단어를 유지하면서 자연스럽게 문장 형태로 재구성할 것
- 작업 전 주의사항 형태로 마무리할 것
- 최대 2문장으로 작성할 것
- 새로운 사고내용 생성 금지


[물질군 유해위험요인]
{material_risk_source}

[작업유형 주요 위험요인]
{work_risk_source}

[물질군 취급시 주의사항 및 예방조치]
{material_measure_source}

[작업유형 안전대책]
{work_measure_source}

[유사사고 원문]
{similar_text}

[출력 형식]
[AI 주요 위험요인]
- 물질 특성과 작업유형을 연결한 위험요인 3개

[안전 및 예방조치]
- 물질 특성과 작업유형을 연결한 예방조치 3개

[유사사고]
- 유사사고를 작업 전 주의사항 형태로 1~2문장
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "너는 화학안전 전문가다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content

def parse_ai_result(ai_result):
    sections = {
        "risk": "",
        "measure": "",
        "accident": ""
    }

    text = str(ai_result)

    try:
        risk_part = text.split("[AI 주요 위험요인]")[1].split("[안전 및 예방조치]")[0].strip()
        measure_part = text.split("[안전 및 예방조치]")[1].split("[유사사고]")[0].strip()
        accident_part = text.split("[유사사고]")[1].strip()

        sections["risk"] = risk_part
        sections["measure"] = measure_part
        sections["accident"] = accident_part

    except Exception:
        sections["risk"] = text

    return sections

def create_team(
    team_name,
    team_password,
    manager_name,
    manager_password,
    workers
):

    data = {
        "team_name": team_name,
        "password": team_password,
        "manager_name": manager_name,
        "manager_password": manager_password,
        "workers": workers
    }

    result = (
        supabase.table("teams")
        .insert(data)
        .execute()
    )

    return result.data

def login_team(team_name, password):

    result = (
        supabase.table("teams")
        .select("*")
        .eq("team_name", team_name)
        .eq("password", password)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None

def login_manager(team_name, manager_password):

    result = (
        supabase.table("teams")
        .select("*")
        .eq("team_name", st.session_state.get("team_name", ""))
        .execute()
    )

    if result.data:
        return result.data[0]

    return None

def create_work_task(
    team_id,
    team_name,
    work_name,
    work_content,
    work_location,
    work_date,
    scheduled_time,
    tbm_place,
    assigned_workers,
    risk_assessment_done=True
):
    data = {
        "team_id": team_id,
        "team_name": team_name,
        "work_name": work_name,
        "work_content": work_content,
        "work_location": work_location,
        "work_date": work_date,
        "scheduled_time": scheduled_time,
        "tbm_place": tbm_place,
        "assigned_workers": assigned_workers,
        "risk_assessment_done": risk_assessment_done
    }

    result = (
        supabase.table("work_tasks")
        .insert(data)
        .execute()
    )

    return result.data


def get_team_workers(team_id):
    if not team_id:
        return []

    result = (
        supabase.table("teams")
        .select("workers")
        .eq("id", team_id)
        .execute()
    )

    if result.data:
        return result.data[0].get("workers") or []

    return []


def get_today_work_tasks(team_id):
    if not team_id:
        return []

    today = datetime.now().strftime("%Y-%m-%d")

    result = (
        supabase.table("work_tasks")
        .select("*")
        .eq("team_id", team_id)
        .eq("work_date", today)
        .order("created_at", desc=True)
        .execute()
    )

    return result.data if result.data else []

def get_all_work_tasks(team_id):
    if not team_id:
        return []

    result = (
        supabase.table("work_tasks")
        .select("*")
        .eq("team_id", team_id)
        .order("created_at", desc=True)
        .execute()
    )

    return result.data if result.data else []

def generate_tbm_docx(task, logs):
    template_path = "tbm_template.docx"

    doc = DocxTemplate(template_path)

    leader_log = None
    for log in logs:
        if log.get("is_tbm_leader") is True:
            leader_log = log
            break

    if leader_log is None and logs:
        leader_log = logs[0]

    tbm_start = ""
    tbm_end = ""

    if leader_log:
        tbm_start = leader_log.get("tbm_start_time", "")
        tbm_end = leader_log.get("tbm_end_time", "")

    tbm_datetime = ""
    try:
        start_dt = datetime.strptime(tbm_start, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(tbm_end, "%Y-%m-%d %H:%M:%S")

        tbm_datetime = (
            f"{start_dt.strftime('%Y년 %m월 %d일 %H:%M')} "
            f"~ {end_dt.strftime('%H:%M')}"
        )
    except Exception:
        tbm_datetime = f"{tbm_start} ~ {tbm_end}"

    worker_list = [
        log.get("worker_name", "")
        for log in logs
        if log.get("worker_name")
    ]

    daily_check_result = ""
    closing_meeting = ""

    if leader_log:
        daily_check_result = leader_log.get("daily_safety_check_result", "")
        closing_meeting = leader_log.get("closing_meeting_result", "")

    context = {
        "tbm_datetime": tbm_datetime,
        "work_name": task.get("work_name", ""),
        "work_content": task.get("work_content", ""),
        "tbm_location": task.get("tbm_place", ""),
        "daily_check_result": daily_check_result,
        "closing_meeting": closing_meeting,
        "leader_department": leader_log.get("leader_department", "") if leader_log else "",
        "leader_position": leader_log.get("leader_position", "") if leader_log else "",
        "leader_name": leader_log.get("leader_name", "") if leader_log else "",

        "main_hazard_1": leader_log.get("main_hazard_1", "") if leader_log else "",
        "main_hazard_2": leader_log.get("main_hazard_2", "") if leader_log else "",
        "main_hazard_3": leader_log.get("main_hazard_3", "") if leader_log else "",

        "safety_measure_1": leader_log.get("safety_measure_1", "") if leader_log else "",
        "safety_measure_2": leader_log.get("safety_measure_2", "") if leader_log else "",
        "safety_measure_3": leader_log.get("safety_measure_3", "") if leader_log else "",
    }

    doc.render(context)

    # 참석자 확인란 자동 입력
    try:
        attendee_table = doc.tables[0]

        worker_list = [
            log.get("worker_name", "")
            for log in logs
            if log.get("worker_name")
        ]

        # 참석자 입력칸 위치: 22~25행, 각 행 6칸
        attendee_cells = [
            (22, 0), (22, 2), (22, 5), (22, 8), (22, 10), (22, 11),
            (23, 0), (23, 2), (23, 5), (23, 8), (23, 10), (23, 11),
            (24, 0), (24, 2), (24, 5), (24, 8), (24, 10), (24, 11),
            (25, 0), (25, 2), (25, 5), (25, 8), (25, 10), (25, 11),
        ]

        for worker_name, cell_pos in zip(worker_list, attendee_cells):
            row_idx, col_idx = cell_pos
            attendee_table.cell(row_idx, col_idx).text = worker_name

    except Exception as e:
        print("참석자 확인란 입력 오류:", e)

    output = BytesIO()
    doc.save(output)
    output.seek(0)

    return output

def add_worker_to_team(team_id, new_worker_name):
    result = (
        supabase.table("teams")
        .select("workers")
        .eq("id", team_id)
        .execute()
    )

    if not result.data:
        return False, "팀 정보를 찾을 수 없습니다."

    current_workers = result.data[0].get("workers") or []

    if new_worker_name in current_workers:
        return False, "이미 등록된 작업자입니다."

    current_workers.append(new_worker_name)

    supabase.table("teams").update({
        "workers": current_workers
    }).eq("id", team_id).execute()

    return True, "작업자가 추가되었습니다."

def split_ai_bullets(text):
    lines = []

    for line in str(text).splitlines():
        line = line.strip()

        if not line:
            continue

        line = line.lstrip("-").strip()
        lines.append(line)

    return lines

def make_casualty_text(row):
    death_direct = pd.to_numeric(row.get("사망(직접)", 0), errors="coerce")
    death_other = pd.to_numeric(row.get("사망(기타)", 0), errors="coerce")
    injury_direct = pd.to_numeric(row.get("부상(직접)", 0), errors="coerce")
    injury_other = pd.to_numeric(row.get("부상(기타)", 0), errors="coerce")

    death_count = int((0 if pd.isna(death_direct) else death_direct) + (0 if pd.isna(death_other) else death_other))
    injury_count = int((0 if pd.isna(injury_direct) else injury_direct) + (0 if pd.isna(injury_other) else injury_other))

    parts = []

    if death_count > 0:
        parts.append(f"사망자 {death_count}명")

    if injury_count > 0:
        parts.append(f"부상자 {injury_count}명")

    if not parts:
        return ""

    return ", ".join(parts) + "이 발생한 사고."


def find_similar_accident(result):
    df = final_result.copy()

    work_type = str(result.get("작업유형", "")).strip()
    chem_id = str(result.get("chem_id", "")).strip().zfill(6)
    df["CHEMID"] = df["CHEMID"].astype(str).str.strip().str.zfill(6)

    work_time = result.get("작업시간", "")
    try:
        current_month = pd.to_datetime(work_time).month
    except Exception:
        current_month = datetime.now().month

    df["작업유형"] = df["작업유형"].astype(str).str.strip()
    df["CHEMID"] = df["CHEMID"].astype(str).str.strip()

    df["month"] = pd.to_numeric(df["month"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    search_steps = [
        ("작업유형·물질·월 일치", df[
            (df["작업유형"] == work_type) &
            (df["CHEMID"] == chem_id) &
            (df["month"] == current_month)
        ]),
        ("작업유형·물질 일치", df[
            (df["작업유형"] == work_type) &
            (df["CHEMID"] == chem_id)
        ]),
        ("작업유형·월 일치", df[
            (df["작업유형"] == work_type) &
            (df["month"] == current_month)
        ]),
        ("작업유형 일치", df[
            (df["작업유형"] == work_type)
        ]),
    ]

    for match_level, matched_df in search_steps:
        matched_df = matched_df.dropna(subset=["date"])

        if not matched_df.empty:
            latest = matched_df.sort_values("date", ascending=False).iloc[0]
            return latest, match_level

    return None, None


def render_traffic_light(score):
    style = get_score_style(score)

    red_on = "on-red" if "red-on" in style["red_class"] else ""
    yellow_on = "on-yellow" if "yellow-on" in style["yellow_class"] else ""
    green_on = "on-green" if "green-on" in style["green_class"] else ""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: Arial, sans-serif;
        }}

        .result-card {{
            background: #ffffff;
            border: 1px solid #c5c6cd;
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
            box-sizing: border-box;
        }}

        .result-card-title {{
            font-size: 18px;
            font-weight: 900;
            color: #091426;
            margin-bottom: 14px;
        }}

        .traffic-wrap {{
            display: flex;
            justify-content: center;
            padding: 12px 0 6px 0;
        }}

        .traffic-body-horizontal {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 14px;
            background: #080b10;
            padding: 16px 18px;
            border-radius: 42px;
            box-shadow: inset 0 0 12px rgba(255,255,255,0.08), 0 10px 24px rgba(0,0,0,0.22);
        }}

        .traffic-light {{
            width: 66px;
            height: 66px;
            border-radius: 999px;
            border: 4px solid #222;
            background: #111;
            position: relative;
            overflow: hidden;
            opacity: 0.35;
            box-shadow: inset 0 4px 10px rgba(0,0,0,0.7);
        }}

        .traffic-light::before {{
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 35% 25%, rgba(255,255,255,0.55) 0%, transparent 28%),
                repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(0,0,0,0.16) 3px, rgba(0,0,0,0.16) 6px);
        }}

        .on-red {{
            background: #ef4444;
            opacity: 1;
            box-shadow: 0 0 28px rgba(239,68,68,0.9), inset 0 4px 12px rgba(255,255,255,0.35);
        }}

        .on-yellow {{
            background: #facc15;
            opacity: 1;
            box-shadow: 0 0 28px rgba(250,204,21,0.9), inset 0 4px 12px rgba(255,255,255,0.35);
        }}

        .on-green {{
            background: #22c55e;
            opacity: 1;
            box-shadow: 0 0 28px rgba(34,197,94,0.9), inset 0 4px 12px rgba(255,255,255,0.35);
        }}
    </style>
    </head>
    <body>
        <div class="result-card">
            <div class="result-card-title">🚦 실시간 위험 수준</div>
            <div class="traffic-wrap">
                <div class="traffic-body-horizontal">
                    <div class="traffic-light {red_on}"></div>
                    <div class="traffic-light {yellow_on}"></div>
                    <div class="traffic-light {green_on}"></div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    components.html(html, height=180, scrolling=False)


def render_score_card(score):
    style = get_score_style(score)

    dash_offset = 125 - (125 * score / 100)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: Arial, sans-serif;
        }}

        .result-card {{
            background: #ffffff;
            border: 1px solid #c5c6cd;
            border-radius: 18px;
            padding: 20px 16px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
            box-sizing: border-box;
            text-align: center;
        }}

        .score-title {{
            font-size: 12px;
            letter-spacing: 0.22em;
            color: #8b8f98;
            font-weight: 800;
            margin-bottom: 8px;
        }}

        .gauge-box {{
            position: relative;
            width: 250px;
            height: 150px;
            margin: 0 auto;
        }}

        .gauge-box svg {{
            width: 250px;
            height: 150px;
        }}

        .score-center {{
            position: absolute;
            left: 0;
            right: 0;
            top: 58px;
            text-align: center;
        }}

        .score-small-label {{
            font-size: 13px;
            font-weight: 800;
            color: #45474c;
            margin-bottom: -4px;
        }}

        .score-number {{
            font-size: 64px;
            font-weight: 950;
            line-height: 1;
            -webkit-text-stroke: 1.8px #111827;
        }}

        .risk-badge {{
            display: inline-block;
            margin-top: 4px;
            padding: 8px 28px;
            border-radius: 999px;
            font-size: 16px;
            font-weight: 900;
        }}
    </style>
    </head>
    <body>
        <div class="result-card">
            <div class="score-title">SAFETY SCORE</div>

            <div class="gauge-box">
                <svg viewBox="0 0 100 60">
                    <defs>
                        <linearGradient id="safetyScoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#22c55e"/>
                            <stop offset="50%" stop-color="#facc15"/>
                            <stop offset="100%" stop-color="#ef4444"/>
                        </linearGradient>
                    </defs>

                    <path d="M 10 50 A 40 40 0 0 1 90 50"
                        fill="none"
                        stroke="#e5e7eb"
                        stroke-linecap="round"
                        stroke-width="12"/>

                    <path d="M 10 50 A 40 40 0 0 1 90 50"
                        fill="none"
                        stroke="url(#safetyScoreGradient)"
                        stroke-dasharray="125"
                        stroke-dashoffset="{dash_offset}"
                        stroke-linecap="round"
                        stroke-width="12"/>
                </svg>

                <div class="score-center">
                    <div class="score-small-label">위험도</div>
                    <div class="score-number" style="color:{style['score_color']};">{score:.0f}</div>
                </div>
            </div>

            <div class="risk-badge" style="background:{style['badge_bg']}; color:{style['badge_color']};">
                {style['level_text']}
            </div>
        </div>
    </body>
    </html>
    """

    components.html(html, height=250, scrolling=False)

def render_risk_summary_card(score):
    style = get_score_style(score)

    dash_offset = 125 - (125 * score / 100)

    red_on = "on-red" if score >= 70 else ""
    yellow_on = "on-yellow" if 40 <= score < 70 else ""
    green_on = "on-green" if score < 40 else ""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: Arial, sans-serif;
        }}

        .summary-card {{
            background: #ffffff;
            border: 1px solid #c5c6cd;
            border-radius: 18px;
            padding: 20px 16px 18px 16px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
            box-sizing: border-box;
            text-align: center;
        }}

        .score-title {{
            font-size: 11px;
            letter-spacing: 0.22em;
            color: #8b8f98;
            font-weight: 800;
            margin-bottom: 6px;
        }}

        .gauge-box {{
            position: relative;
            width: 230px;
            height: 132px;
            margin: 0 auto;
        }}

        .gauge-box svg {{
            width: 230px;
            height: 132px;
        }}

        .score-center {{
            position: absolute;
            left: 0;
            right: 0;
            top: 50px;
            text-align: center;
        }}

        .score-small-label {{
            font-size: 12px;
            font-weight: 800;
            color: #45474c;
            margin-bottom: -3px;
        }}

        .score-number {{
            font-size: 58px;
            font-weight: 950;
            line-height: 1;
            -webkit-text-stroke: 1.6px #111827;
        }}

        .risk-badge {{
            display: inline-block;
            margin-top: 2px;
            padding: 7px 24px;
            border-radius: 999px;
            font-size: 15px;
            font-weight: 900;
        }}

        .traffic-section {{
            margin-top: 18px;
            padding-top: 14px;
            border-top: 1px solid #e5e7eb;
        }}

        .traffic-label {{
            font-size: 13px;
            font-weight: 900;
            color: #091426;
            margin-bottom: 10px;
        }}

        .traffic-wrap {{
            display: flex;
            justify-content: center;
        }}

        .traffic-body {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 9px;
            background: #080b10;
            padding: 10px 13px;
            border-radius: 999px;
            box-shadow: inset 0 0 10px rgba(255,255,255,0.08), 0 8px 18px rgba(0,0,0,0.18);
        }}

        .traffic-light {{
            width: 42px;
            height: 42px;
            border-radius: 999px;
            border: 3px solid #222;
            background: #111;
            position: relative;
            overflow: hidden;
            opacity: 0.35;
            box-shadow: inset 0 3px 8px rgba(0,0,0,0.7);
        }}

        .traffic-light::before {{
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 35% 25%, rgba(255,255,255,0.55) 0%, transparent 30%),
                repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(0,0,0,0.16) 3px, rgba(0,0,0,0.16) 6px);
        }}

        .on-red {{
            background: #ef4444;
            opacity: 1;
            box-shadow: 0 0 20px rgba(239,68,68,0.9), inset 0 3px 9px rgba(255,255,255,0.35);
        }}

        .on-yellow {{
            background: #facc15;
            opacity: 1;
            box-shadow: 0 0 20px rgba(250,204,21,0.9), inset 0 3px 9px rgba(255,255,255,0.35);
        }}

        .on-green {{
            background: #22c55e;
            opacity: 1;
            box-shadow: 0 0 20px rgba(34,197,94,0.9), inset 0 3px 9px rgba(255,255,255,0.35);
        }}
    </style>
    </head>

    <body>
        <div class="summary-card">
            <div class="score-title">SAFETY SCORE</div>

            <div class="gauge-box">
                <svg viewBox="0 0 100 60">
                    <defs>
                        <linearGradient id="safetyScoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#22c55e"/>
                            <stop offset="50%" stop-color="#facc15"/>
                            <stop offset="100%" stop-color="#ef4444"/>
                        </linearGradient>
                    </defs>

                    <path d="M 10 50 A 40 40 0 0 1 90 50"
                        fill="none"
                        stroke="#e5e7eb"
                        stroke-linecap="round"
                        stroke-width="12"/>

                    <path d="M 10 50 A 40 40 0 0 1 90 50"
                        fill="none"
                        stroke="url(#safetyScoreGradient)"
                        stroke-dasharray="125"
                        stroke-dashoffset="{dash_offset}"
                        stroke-linecap="round"
                        stroke-width="12"/>
                </svg>

                <div class="score-center">
                    <div class="score-small-label">위험도</div>
                    <div class="score-number" style="color:{style['score_color']};">{score:.0f}</div>
                </div>
            </div>

            <div class="risk-badge" style="background:{style['badge_bg']}; color:{style['badge_color']};">
                {style['level_text']}
            </div>

            <div class="traffic-section">
                <div class="traffic-label">실시간 위험 수준</div>
                <div class="traffic-wrap">
                    <div class="traffic-body">
                        <div class="traffic-light {red_on}"></div>
                        <div class="traffic-light {yellow_on}"></div>
                        <div class="traffic-light {green_on}"></div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    components.html(html, height=365, scrolling=False)

def show_risk_result():
    if "ai_result" not in st.session_state:
        st.session_state.ai_result = None

    result = st.session_state.result
    score = float(result["score"])

    material_risk_items, work_risk_items, material_measure_items, work_measure_items = get_risk_and_measure_messages(result)

    similar_accident, match_level = find_similar_accident(result)

    if similar_accident is not None:

        accident_date = similar_accident.get("date", "")
        accident_date_text = pd.to_datetime(accident_date).strftime("%Y-%m-%d")

        sido = str(similar_accident.get("도", "")).strip()
        sigungu = str(similar_accident.get("시군", "")).strip()

        location_text = f"{sido} {sigungu}"

        accident_work_type = str(similar_accident.get("작업유형", "-")).strip()
        accident_content = str(similar_accident.get("사고내용", "-")).strip()

        casualty_text = make_casualty_text(similar_accident)

        similar_text = f"""
    사고일시: {accident_date_text}
    사업장 소재지: {location_text}
    작업유형: {accident_work_type}
    사고내용: {accident_content}
    인명피해: {casualty_text}
    """

    else:
        similar_text = "유사사고 정보 없음"

    if st.session_state.ai_result is None:

        with st.spinner("AI가 TBM 내용을 생성 중입니다..."):

            st.session_state.ai_result = generate_ai_text(
                material_risk_items,
                work_risk_items,
                material_measure_items,
                work_measure_items,
                similar_text
            )

    ai_result = st.session_state.ai_result
   
    ai_sections = parse_ai_result(ai_result)

    risk_items = split_ai_bullets(ai_sections["risk"])
    measure_items = split_ai_bullets(ai_sections["measure"])
    similar_accident_ai_text = ai_sections["accident"]

    main_hazard_1 = risk_items[0] if len(risk_items) > 0 else ""
    main_hazard_2 = risk_items[1] if len(risk_items) > 1 else ""
    main_hazard_3 = risk_items[2] if len(risk_items) > 2 else ""

    safety_measure_1 = measure_items[0] if len(measure_items) > 0 else ""
    safety_measure_2 = measure_items[1] if len(measure_items) > 1 else ""
    safety_measure_3 = measure_items[2] if len(measure_items) > 2 else ""

    st.session_state.work_data["main_hazard_1"] = main_hazard_1
    st.session_state.work_data["main_hazard_2"] = main_hazard_2
    st.session_state.work_data["main_hazard_3"] = main_hazard_3

    st.session_state.work_data["safety_measure_1"] = safety_measure_1
    st.session_state.work_data["safety_measure_2"] = safety_measure_2
    st.session_state.work_data["safety_measure_3"] = safety_measure_3

    topbar_html = '<div class="result-page-topbar"><div class="result-topbar-row"><div class="result-topbar-left"><a href="?page=input" target="_self" style="text-decoration:none;"><div class="result-back-icon">←</div></a><div class="result-app-title">Safety TBM</div></div><a href="?page=result&help=result" target="_self" style="text-decoration:none;"><div style="font-size:22px; color:#45474c;">ℹ️</div></a></div></div>'
    st.markdown(topbar_html, unsafe_allow_html=True)
    render_topbar_spacer()


    # =========================
    # 메인 제목
    # =========================
    st.markdown("""
<div class="result-report-label">RISK ANALYSIS REPORT</div>
<div class="result-title">오늘의 작업 위험도는</div>
<div class="result-subtitle">
    입력한 작업유형과 취급물질 정보를 기준으로 오늘 작업의 위험수준을 분석했습니다.
</div>
""", unsafe_allow_html=True)

    # =========================
    # 위험도 점수 + 신호등 카드
    # =========================
    render_risk_summary_card(score)

    # =========================
    # AI 분석 주요 위험요인 카드
    # =========================
    risk_html = ""

    for i, item in enumerate(risk_items, start=1):
        risk_html += f"""
<div class="message-item">
    <div class="message-num">{i:02d}</div>
    <div class="message-text">{item}</div>
</div>
"""

    html = f"""
<div class="result-card">
    <div class="result-card-header">
        <div class="result-card-icon">🧠</div>
        <div class="result-card-title">AI 분석 주요 위험요인</div>
    </div>
    {risk_html}
</div>
"""

    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)

    # =========================
    # 안전 및 사고 예방대책 카드
    # =========================
    measure_html = ""

    for item in measure_items:
        measure_html += f"""
<div class="measure-item">
    <div class="measure-check">✓</div>
    <div class="measure-text">{item}</div>
</div>
"""

    html = f"""
<div class="result-card">
    <div class="result-card-header">
        <div class="result-card-icon">🛡️</div>
        <div class="result-card-title">안전 및 사고 예방대책</div>
    </div>
    {measure_html}
</div>
"""

    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)
    # =========================
    # 유사 사고사례 카드
    # =========================


    if similar_accident is not None:
        accident_date = similar_accident.get("date", "")

        if pd.notna(accident_date):
            accident_date_text = pd.to_datetime(accident_date).strftime("%Y-%m-%d")
        else:
            accident_date_text = "-"

        sido = str(similar_accident.get("도", "")).strip()
        sigungu = str(similar_accident.get("시군", "")).strip()
        location_text = f"{sido} {sigungu} 소재 사업장".strip()

        accident_work_type = str(similar_accident.get("작업유형", "-")).strip()
        accident_content = str(similar_accident.get("사고내용", "-")).strip()
        casualty_text = make_casualty_text(similar_accident)

        casualty_html = ""
        if casualty_text:
            casualty_html = f'<div class="incident-placeholder-desc"><b>인명피해:</b> {casualty_text}</div>'

        html = f'''
<div class="result-card">
    <div class="result-card-header">
        <div class="result-card-icon">🕒</div>
        <div class="result-card-title">유사 사고사례</div>
    </div>
    <div class="incident-placeholder">
        <div class="incident-placeholder-desc">{similar_accident_ai_text}</div>
    </div>
</div>
'''
    else:
        html = '''
<div class="result-card"><div class="result-card-header"><div class="result-card-icon">🕒</div><div class="result-card-title">유사 사고사례</div></div><div class="incident-placeholder"><div class="incident-placeholder-title">유사 사고사례 없음</div><div class="incident-placeholder-desc">입력한 작업유형과 물질정보를 기준으로 일치하는 사고사례를 찾지 못했습니다.</div></div></div>
'''

    st.markdown(html, unsafe_allow_html=True)

    # =========================
    # 작업물질 정보
    # =========================
    if result.get("chem_name"):
        st.markdown(
            f"""
<div class="result-info-caption">
    작업물질: {result['chem_name']} / CHEMID: {result['chem_id']}
</div>
""",
            unsafe_allow_html=True
        )
    else:
        st.warning("작업물질 정보가 불확실하여 위험도를 보수적으로 산정했습니다.")

    # =========================
    # 체크리스트 이동 버튼
    # =========================
    if st.button("☑️ TBM 체크리스트 확인", use_container_width=True):
        st.session_state.page = "checklist"
        st.rerun()

    show_bottom_nav()

def show_checklist():

    topbar_html = '<div class="checklist-topbar"><div class="checklist-topbar-row"><div class="checklist-topbar-left"><a href="?page=result" target="_self" style="text-decoration:none;"><div class="checklist-back-icon">←</div></a><div class="checklist-app-title">Checklist</div></div><a href="?page=checklist&help=checklist" target="_self" style="text-decoration:none;"><div style="font-size:22px; color:#45474c;">ℹ️</div></a></div></div>'
    st.markdown(topbar_html, unsafe_allow_html=True)
    render_topbar_spacer()

    work_data = st.session_state.get("work_data", {})
    worker_name = work_data.get("작업자명", "미입력")
    work_name = work_data.get("작업명", "미입력")
    work_location = work_data.get("작업장소", "미입력")
    work_type = work_data.get("작업유형", "미입력")
    current_date = datetime.now().strftime("%Y년 %m월 %d일")

    checklist_info_html = f'<div class="checklist-info-card"><div class="checklist-badge">DAILY INSPECTION</div><div class="checklist-title">작업 전 안전점검(TBM)</div><div class="checklist-subtitle">일시: {current_date}<br>점검자: {worker_name}<br>작업명: {work_name}<br>작업장소: {work_location}<br>작업유형: {work_type}</div></div>'
    st.markdown(checklist_info_html, unsafe_allow_html=True)

    checklist_section_html = '<div class="checklist-section-title">☑️ 점검 항목</div>'
    st.markdown(checklist_section_html, unsafe_allow_html=True)

    checklist_items = [
        "오늘 작업의 위험요인을 확인하였다.",
        "오늘 작업의 유사사고를 확인하였다.",
        "오늘 작업 중 사고발생 시 사용하는 보호구와 보호구 위치를 알고 있다.",
        "전날 과도한 음주를 하지 않았다.",
        "피로, 발열 없음 등 오늘 몸상태는 작업에 적절하다.",
        "위험요인, 불안전 발견 시 즉시 멈추고 생각한 후 작업하도록 주지했다.",
        "작업 후 정리정돈 방법을 알고 있다.",
        "사고발생 시 긴급연락처를 알고 있다.",
        "비상대피로 및 집결지를 확인하였다."
    ]

    checked_count = 0

    for idx, item in enumerate(checklist_items, start=1):
        checked = st.checkbox(
            item,
            key=f"tbm_check_{idx}"
        )

        if checked:
            checked_count += 1

    unchecked_items = [
        item for idx, item in enumerate(checklist_items, start=1)
        if not st.session_state.get(f"tbm_check_{idx}", False)
    ]

    all_checked = len(unchecked_items) == 0

    st.markdown(
        f"""
<div class="checklist-save-note">
    현재 {len(checklist_items)}개 항목 중 {checked_count}개 항목을 확인했습니다.
</div>
""",
        unsafe_allow_html=True
    )

    if not all_checked:
        st.warning("모든 점검 항목을 체크해야 TBM을 완료할 수 있습니다.")

    # =========================
    # 특이사항 입력
    # =========================
    st.markdown("""
<div class="checklist-section-title">📝 작업 전 일일 안전점검 시행 결과</div>
""", unsafe_allow_html=True)

    remark = st.text_area(
        "작업 전 일일 안전점검 시행 결과",
        placeholder="작업 전 일일 안전점검 시행 결과를 작성하세요(※ TBM리더 작성 필수).",
        height=140,
        key="checklist_remark",
        label_visibility="collapsed"
    )

    # =========================
    # 저장 버튼
    # =========================
    if st.button("💾 TBM 완료 및 저장", use_container_width=True):
        unchecked_items = [
            item for idx, item in enumerate(checklist_items, start=1)
            if not st.session_state.get(f"tbm_check_{idx}", False)
        ]

        if unchecked_items:
            st.error("모든 체크리스트 항목을 확인해야 TBM을 완료할 수 있습니다.")
            st.write("미확인 항목:")
            for item in unchecked_items:
                st.write(f"- {item}")
            return

        st.session_state.checklist_data = {
            "저장시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "작업자명": worker_name,
            "작업명": work_name,
            "작업장소": work_location,
            "작업유형": work_type,
            "전체항목수": len(checklist_items),
            "확인항목수": checked_count,
            "미확인항목": [],
            "특이사항": remark,
            "TBM완료여부": "완료"
        }

        st.success("TBM 체크리스트가 저장되었습니다.")

        st.session_state.page = "journal"
        st.rerun()

    show_bottom_nav()

def show_journal():

    topbar_html = '<div class="journal-topbar"><div class="journal-topbar-row"><div class="journal-topbar-left"><a href="?page=checklist" target="_self" style="text-decoration:none;"><div class="journal-back-icon">←</div></a><div class="journal-app-title">Safety TBM</div></div><a href="?page=journal&help=journal" target="_self" style="text-decoration:none;"><div style="font-size:22px; color:#45474c;">ℹ️</div></a></div></div>'
    st.markdown(topbar_html, unsafe_allow_html=True)
    render_topbar_spacer()

    # =========================
    # 데이터 불러오기
    # =========================
    work_data = st.session_state.get("work_data", {})


    # =========================
    # 데이터 불러오기
    # =========================
    work_data = st.session_state.get("work_data", {})
    result = st.session_state.get("result", {})
    checklist_data = st.session_state.get("checklist_data", {})

    worker_name = work_data.get("작업자명", "미입력")
    work_name = work_data.get("작업명", "미입력")
    work_location = work_data.get("작업장소", "미입력")
    work_type = work_data.get("작업유형", "미입력")
    chemical = work_data.get("취급물질", "미입력")
    work_time = work_data.get("작업시간", datetime.now().strftime("%Y-%m-%d %H:%M"))

    score = result.get("score", None)
    level = result.get("level", "미산정")
    checklist_remark = checklist_data.get("특이사항", "")

    today_text = datetime.now().strftime("%Y년 %m월 %d일")
    score_text = f"{float(score):.0f}점" if score is not None else "미산정"

    # =========================
    # 제목
    # =========================
    st.markdown(f"""
<div class="journal-title">작업일지 작성</div>
<div class="journal-subtitle">
    {today_text} | TBM 완료 후 작업 내용을 기록합니다.
</div>
""", unsafe_allow_html=True)

    # =========================
    # TBM 요약 정보
    # =========================
    checklist_remark_text = checklist_remark if checklist_remark else "체크리스트 단계에서 입력된 특이사항이 없습니다."

    summary_html = f"""
<div class="journal-card"><div class="journal-card-header"><div class="journal-card-title">TBM 요약 정보</div><div style="font-size:22px; color:#2170e4;">ℹ️</div></div><div class="journal-summary-row"><div class="journal-summary-label">작업자</div><div class="journal-summary-value">{worker_name}</div></div><div class="journal-summary-row"><div class="journal-summary-label">작업명</div><div class="journal-summary-value">{work_name}</div></div><div class="journal-summary-row"><div class="journal-summary-label">작업장소</div><div class="journal-summary-value">{work_location}</div></div><div class="journal-summary-row"><div class="journal-summary-label">작업유형</div><div class="journal-summary-value">{work_type}</div></div><div class="journal-summary-row"><div class="journal-summary-label">취급물질</div><div class="journal-summary-value">{chemical}</div></div><div class="journal-summary-row"><div class="journal-summary-label">위험도</div><div class="journal-summary-value"><span class="journal-risk-badge">{score_text} / {level}</span></div></div><div class="journal-message-box"><b>TBM 체크리스트 특이사항</b><br>{checklist_remark_text}</div></div>
"""

    st.markdown(summary_html, unsafe_allow_html=True)


    # =========================
    # 특이사항 기록 내역
    # =========================
    st.markdown("""
<div class="journal-card">
    <div class="journal-card-header">
        <div class="journal-card-title">작업 전 일일 안전점검 시행 결과</div>
    </div>
    <div class="journal-small-label">작업 후 종료 미팅</div>
</div>
""", unsafe_allow_html=True)

    journal_note = st.text_area(
        "작업 후 종료 미팅",
        placeholder="작업 후 중점위험요인 확인내역을 작성하세요.",
        height=160,
        key="journal_note_input",
        label_visibility="collapsed"
    )

    st.markdown("""
<div class="journal-message-box">
    ✅ 종료 미팅 내역은 안전관리자 작업보드에 기록될 예정입니다.
</div>
""", unsafe_allow_html=True)


    # =========================
    # 제출 카드
    # =========================
    st.markdown("""
<div class="journal-submit-card">
    <div class="journal-submit-title">일지 작성을 완료하시겠습니까?</div>
    <div class="journal-submit-desc">
        작성된 내용은 추후 안전관리자 작업로그 화면에 반영되도록 연결할 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

    if st.button("📤 제출하기", use_container_width=True):

        if st.session_state.work_data.get("TBM리더여부", False):
            st.session_state.work_data["TBM종료시간"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_data = {
            "팀ID": st.session_state.get("team_id", ""),
            "팀명": st.session_state.get("team_name", ""),
            "작업자": worker_name,
            "작업명": work_name,
            "작업장소": work_location,
            "작업유형": work_type,
            "취급물질": chemical,
            "작업시간": work_time,
            "위험도점수": score_text,
            "위험등급": level,
            "TBM완료여부": "완료",

            "작업전일일안전점검결과": checklist_remark,

            "작업후종료미팅": journal_note,

            "TBM리더여부": st.session_state.work_data.get("TBM리더여부", False),
            "리더소속": st.session_state.work_data.get("리더소속", ""),
            "리더직책": st.session_state.work_data.get("리더직책", ""),
            "리더성명": st.session_state.work_data.get("리더성명", ""),

            "task_id": st.session_state.work_data.get("task_id", ""),

            "제출시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "제출상태": "제출완료"
        }

        st.session_state.journal_data = log_data
        st.session_state.work_logs.append(log_data)

        log_df = pd.DataFrame(st.session_state.work_logs)
        log_df.to_csv(
            st.session_state.work_log_csv_path,
            index=False,
            encoding="utf-8-sig"
        )

        try:

            supabase.table("work_logs").insert({

                "team_id": st.session_state.get("team_id", ""),
                "team_name": st.session_state.get("team_name", ""),

                "task_id": st.session_state.work_data.get("task_id", ""),

                "worker_name": worker_name,

                "work_name": work_name,

                "work_location": work_location,

                "work_time": work_time,

                "work_type": st.session_state.work_data.get("작업유형", ""),

                "material_name": chemical,

                "risk_score": float(score) if score is not None else None,

                "risk_level": level,

                "tbm_status": "완료",

                "daily_safety_check_result": checklist_remark,

                "closing_meeting_result": journal_note,

                "is_tbm_leader": st.session_state.work_data.get("TBM리더여부", False),

                "daily_safety_check_result": checklist_remark,

                "closing_meeting_result": journal_note,

                "main_hazard_1": st.session_state.work_data.get("main_hazard_1", ""),
                "main_hazard_2": st.session_state.work_data.get("main_hazard_2", ""),
                "main_hazard_3": st.session_state.work_data.get("main_hazard_3", ""),

                "safety_measure_1": st.session_state.work_data.get("safety_measure_1", ""),
                "safety_measure_2": st.session_state.work_data.get("safety_measure_2", ""),
                "safety_measure_3": st.session_state.work_data.get("safety_measure_3", ""),

                "leader_department": st.session_state.work_data.get("리더소속", ""),

                "leader_position": st.session_state.work_data.get("리더직책", ""),

                "leader_name": st.session_state.work_data.get("리더성명", ""),

                "tbm_start_time": st.session_state.work_data.get("TBM시작시간", ""),

                "tbm_end_time": st.session_state.work_data.get("TBM종료시간", ""),

                "submit_status": "제출완료"

            }).execute()

        except Exception as e:

            st.error("작업로그 DB 저장 실패")
            st.write(str(e))

        st.session_state.journal_submitted = True

        st.success("작업일지가 제출되었습니다.")

    show_bottom_nav()

def show_manager_dashboard():

    if not st.session_state.get("team_id"):
        st.warning("팀 접속 정보가 없습니다. 작업팀 접속 화면에서 다시 접속해 주세요.")

        if st.button("작업팀 접속 화면으로 이동", use_container_width=True):
            st.session_state.page = "team_access"
            st.query_params.clear()
            st.rerun()

        return

    st.markdown("""
<style>
.manager-topbar {
    background: #091426;
    color: white;
    border-radius: 0 0 18px 18px;
    padding: 18px 16px;
    margin: -24px -8px 20px -8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.manager-title {
    font-size: 24px;
    font-weight: 900;
}

.manager-summary-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 24px;
}

.manager-summary-card {
    background: white;
    border: 1px solid #d8dee9;
    border-radius: 16px;
    padding: 14px 10px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(15,23,42,0.07);
}

.manager-summary-label {
    font-size: 12px;
    font-weight: 900;
    color: #45474c;
    margin-bottom: 8px;
}

.manager-summary-value {
    font-size: 28px;
    font-weight: 950;
    color: #091426;
}

.manager-summary-red {
    color: #ef4444;
}

.manager-summary-green {
    color: #16a34a;
}

.manager-section-title {
    font-size: 22px;
    font-weight: 900;
    color: #091426;
    margin: 24px 0 12px 0;
}

.log-card {
    background: white;
    border: 1px solid #d8dee9;
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 10px;
    box-shadow: 0 3px 10px rgba(15,23,42,0.06);
}

.log-top-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}

.log-work-name {
    font-size: 16px;
    font-weight: 900;
    color: #091426;
}

.log-meta {
    font-size: 13px;
    color: #45474c;
    line-height: 1.5;
}

.status-badge {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 900;
}

.status-done {
    background: #dcfce7;
    color: #15803d;
}

.status-progress {
    background: #ffedd5;
    color: #ea580c;
}

.risk-badge-red {
    background: #fee2e2;
    color: #dc2626;
}

.risk-badge-yellow {
    background: #fef3c7;
    color: #d97706;
}

.risk-badge-green {
    background: #dbeafe;
    color: #2563eb;
}

.incomplete-box {
    background: #fff7ed;
    border: 1px solid #fed7aa;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 16px;
}

.incomplete-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: white;
    border-radius: 12px;
    padding: 12px;
    margin-top: 8px;
    border: 1px solid #fed7aa;
}

.incomplete-name {
    font-weight: 900;
    color: #091426;
}

.incomplete-work {
    font-size: 13px;
    color: #45474c;
}
</style>
""", unsafe_allow_html=True)

    st.markdown('<div class="manager-topbar"><div class="manager-title">안전관리자 대시보드</div><a href="?page=manager&help=manager" target="_self" style="text-decoration:none; color:white;"><div style="font-size:26px;">ℹ️</div></a></div>', unsafe_allow_html=True)
    render_topbar_spacer()

    st.markdown('<div class="manager-section-title">오늘 작업 등록</div>', unsafe_allow_html=True)

    workers = get_team_workers(st.session_state.get("team_id", ""))

    task_work_name = st.text_input(
        "작업명",
        placeholder="예: 배관 플랜지 교체 작업",
        key="task_work_name"
    )

    task_work_content = st.text_area(
        "작업내용",
        placeholder="예: 노후 배관 플랜지 분리, 가스켓 교체 및 체결 작업",
        height=100,
        key="task_work_content"
    )

    task_work_location = st.text_input(
        "작업장소",
        placeholder="예: 2공장 반응기실",
        key="task_work_location"
    )


    task_scheduled_time = st.text_input(
        "예정시간",
        placeholder="예: 09:00 ~ 11:00",
        key="task_scheduled_time"
    )

    task_tbm_place = st.text_input(
        "TBM 장소",
        placeholder="예: 현장 작업구역 앞",
        key="task_tbm_place"
    )

    risk_assessment_done = st.checkbox(
        "위험성평가 실시",
        value=True,
        key="task_risk_assessment_done"
    )

    assigned_workers = st.multiselect(
        "작업자 선택",
        workers,
        key="task_assigned_workers"
    )

    if st.button("➕ 오늘 작업 등록", key="create_work_task_btn", use_container_width=True):

        if not task_work_name.strip():
            st.warning("작업명을 입력해 주세요.")
            return

        if not task_work_content.strip():
            st.warning("작업내용을 입력해 주세요.")
            return

        if not task_work_location.strip():
            st.warning("작업장소를 입력해 주세요.")
            return

        if not assigned_workers:
            st.warning("작업자를 1명 이상 선택해 주세요.")
            return

        try:
            saved_task = create_work_task(
                team_id=st.session_state.get("team_id", ""),
                team_name=st.session_state.get("team_name", ""),
                work_name=task_work_name.strip(),
                work_content=task_work_content.strip(),
                work_location=task_work_location.strip(),
                work_date=datetime.now().strftime("%Y-%m-%d"),
                scheduled_time=task_scheduled_time.strip(),
                tbm_place=task_tbm_place.strip(),
                assigned_workers=assigned_workers,
                risk_assessment_done=risk_assessment_done
            )

            if saved_task:
                st.success("오늘 작업이 등록되었습니다.")
                st.rerun()
            else:
                st.error("작업 등록 결과가 비어 있습니다.")

        except Exception as e:
            st.error("작업 등록 중 오류가 발생했습니다.")
            st.write(str(e))

    st.markdown('<div class="manager-section-title">오늘 등록된 작업</div>', unsafe_allow_html=True)

    try:
        today_tasks = get_today_work_tasks(st.session_state.get("team_id", ""))
    except Exception as e:
        st.error("오늘 작업 목록을 불러오지 못했습니다.")
        st.write(str(e))
        today_tasks = []

    if not today_tasks:
        st.caption("아직 등록된 작업이 없습니다.")
    else:
        for task in today_tasks:

            task_workers = ", ".join(task.get("assigned_workers") or [])

            task_card_html = f"""
    <div class="log-card">
    <div class="log-top-row">
    <div class="log-work-name">{task.get("work_name", "-")}</div>
    <span class="status-badge status-progress">
    {task.get("scheduled_time", "-")}
    </span>
    </div>

    <div class="log-meta">
    작업내용: {task.get("work_content", "-")}<br>
    작업장소: {task.get("work_location", "-")}<br>
    TBM 장소: {task.get("tbm_place", "-")}<br>
    작업자: {task_workers}
    </div>
    </div>
    """

            st.markdown(
                task_card_html,
                unsafe_allow_html=True
            )
            try:
                log_result = (
                    supabase.table("work_logs")
                    .select("*")
                    .eq("task_id", task.get("id", ""))
                    .execute()
                )

                task_logs = log_result.data if log_result.data else []

                st.caption(f"제출된 TBM 기록: {len(task_logs)}건")

                docx_file = generate_tbm_docx(task, task_logs)

                st.download_button(
                    label="📄 TBM 회의록 출력하기",
                    data=docx_file,
                    file_name=f"TBM회의록_{task.get('work_name', '작업')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"download_tbm_docx_{task.get('id')}",
                    use_container_width=True
                )

            except Exception as e:
                st.error("TBM 회의록 생성 실패")
                st.write(str(e))

    st.markdown('<div class="manager-section-title">작업자 관리</div>', unsafe_allow_html=True)

    new_worker_name = st.text_input(
        "작업자 추가",
        placeholder="추가할 작업자 이름 입력",
        key="manager_add_worker_input"
    )

    if st.button("➕ 작업자 추가", key="manager_add_worker_btn", use_container_width=True):
        if not new_worker_name.strip():
            st.warning("추가할 작업자 이름을 입력해 주세요.")
        else:
            success, message = add_worker_to_team(
                st.session_state.get("team_id", ""),
                new_worker_name.strip()
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.warning(message)
    try:
        team_id = st.session_state.get("team_id", "")

        if not team_id:
            workers = []
        else:
            team_result = (
                supabase.table("teams")
                .select("workers")
                .eq("id", team_id)
                .execute()
            )

            workers = (
                team_result.data[0].get("workers", [])
                if team_result.data
                else []
            )

        if workers:
            st.write("등록된 작업자")
            for worker in workers:
                st.markdown(f"- {worker}")
        else:
            st.caption("등록된 작업자가 없습니다.")

    except Exception as e:
        st.error("작업자 목록을 불러오지 못했습니다.")
        st.write(str(e))

    try:
        team_id = st.session_state.get("team_id", "")

        if not team_id:
            db_logs = []

        else:
            result = (
                supabase.table("work_logs")
                .select("*")
                .eq("team_id", team_id)
                .order("created_at", desc=True)
                .execute()
            )

            db_logs = result.data if result.data else []

    except Exception as e:
        st.error("작업로그를 불러오는 중 오류가 발생했습니다.")
        st.write(str(e))
        db_logs = []

    logs = []

    for log in db_logs:

        risk_score = log.get("risk_score")

        if isinstance(risk_score, (int, float)):
            risk_score_text = f"{risk_score:.0f}점"
        else:
            risk_score_text = "-"

        logs.append({
            "작업명": log.get("work_name", "-"),
            "작업자": log.get("worker_name", "-"),
            "작업시간": log.get("work_time", "-"),
            "위험도점수": risk_score_text,
            "위험등급": log.get("risk_level", "-"),
            "TBM완료여부": log.get("tbm_status", "-"),
            "TBM특이사항": log.get("checklist_remark", "-"),
            "작업특이사항": log.get("journal_note", "-"),
            "제출상태": log.get("submit_status", "-")
        })

    log_df = pd.DataFrame(logs)

    if "작업명" in log_df.columns:
        total_work_count = log_df["작업명"].nunique()
    else:
        total_work_count = 0

    high_risk_count = log_df[
        log_df["위험등급"].astype(str).str.contains("위험경고|고위험|🔴", na=False)
    ]["작업명"].nunique() if not log_df.empty else 0

    working_count = len(
        log_df[log_df["제출상태"].astype(str) != "제출완료"]
    ) if "제출상태" in log_df.columns else 0

    st.markdown(f"""
<div class="manager-section-title">오늘의 작업 현황</div>
<div class="manager-summary-grid">
    <div class="manager-summary-card">
        <div class="manager-summary-label">우리 팀 작업 수</div>
        <div class="manager-summary-value">{total_work_count}<span style="font-size:14px;">건</span></div>
    </div>
    <div class="manager-summary-card">
        <div class="manager-summary-label">고위험 작업 수</div>
        <div class="manager-summary-value manager-summary-red">{high_risk_count}<span style="font-size:14px;">건</span></div>
    </div>
    <div class="manager-summary-card">
        <div class="manager-summary-label">현재 작업중 팀원</div>
        <div class="manager-summary-value manager-summary-green">{working_count}<span style="font-size:14px;">명</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="manager-section-title">실시간 작업로그</div>', unsafe_allow_html=True)

    csv_df = log_df.copy()
    csv_data = csv_df.to_csv(index=False, encoding="utf-8-sig")

    st.download_button(
        label="📥 CSV 다운로드",
        data=csv_data,
        file_name="safety_tbm_work_logs.csv",
        mime="text/csv",
        use_container_width=True
    )

    for _, row in log_df.iterrows():
        risk_text = str(row.get("위험등급", ""))
        status = str(row.get("TBM완료여부", row.get("제출상태", "진행중")))

        if "위험경고" in risk_text or "고위험" in risk_text or "🔴" in risk_text:
            risk_class = "risk-badge-red"
            risk_label = "고위험"
        elif "작업주의" in risk_text or "중위험" in risk_text or "🟡" in risk_text:
            risk_class = "risk-badge-yellow"
            risk_label = "중위험"
        else:
            risk_class = "risk-badge-green"
            risk_label = "저위험"

        status_class = "status-done" if "완료" in status else "status-progress"
        status_label = "완료 ✓" if "완료" in status else "진행중"

        st.markdown(f"""
<div class="log-card">
    <div class="log-top-row">
        <div>
            <span class="status-badge {risk_class}">{risk_label}</span>
            <span class="log-work-name"> {row.get("작업명", "-")}</span>
        </div>
        <span class="status-badge {status_class}">{status_label}</span>
    </div>
    <div class="log-meta">
        작업자: {row.get("작업자", "-")}<br>
        작업시간: {row.get("작업시간", "-")}<br>
        위험도: {row.get("위험도점수", "-")} / {row.get("위험등급", "-")}<br>
        TBM 특이사항: {row.get("TBM특이사항", "-")}<br>
        작업 특이사항: {row.get("작업특이사항", "-")}
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="manager-section-title">작업 미완료 작업자</div>', unsafe_allow_html=True)

    incomplete_df = log_df[log_df["제출상태"].astype(str) != "제출완료"] if "제출상태" in log_df.columns else pd.DataFrame()

    if incomplete_df.empty:
        st.success("현재 작업 미완료 작업자가 없습니다.")
    else:
        st.markdown("""
<div class="incomplete-box">
    ⏱️ 아래 팀원은 현재 작업을 진행 중이며, 작업로그 제출이 완료되지 않았습니다.
</div>
""", unsafe_allow_html=True)

        for _, row in incomplete_df.iterrows():
            st.markdown(f"""
<div class="incomplete-item">
    <div>
        <div class="incomplete-name">{row.get("작업자", "-")}</div>
        <div class="incomplete-work">{row.get("작업명", "-")}</div>
    </div>
    <div class="status-badge status-progress">진행중</div>
</div>
""", unsafe_allow_html=True)

    show_bottom_nav()

# ---------- OPENAI API키 ----------------
client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =========================
# 2) 기본 설정
# =========================
SERVICE_KEY = st.secrets["DATA_API_KEY"]

strength_mapping = {
    0: 0,
    1: 1,
    2: 3,
    3: 6
}

hazard_features = [
    "금속부식성 물질",
    "급성 독성(흡입)",
    "인화성",
    "급성 수생환경 유해성",
    "산화성",
    "고압가스",
    "자연발화 및 과산화물",
]

col_alias = {
    "급성독성(흡입)": "급성 독성(흡입)",
    "급성 독성(흡입)": "급성 독성(흡입)",
    "금속부식성": "금속부식성 물질",
    "금속부식성 물질": "금속부식성 물질",
    "수생환경": "급성 수생환경 유해성",
    "급성 수생환경 유해성": "급성 수생환경 유해성",
    "자연발화과산화물": "자연발화 및 과산화물",
    "자연발화 및 과산화물": "자연발화 및 과산화물",
    "인화성": "인화성",
    "산화성": "산화성",
    "고압가스": "고압가스",
}

interaction_rules = [
    ("인화성", "work_type_HOT_WORK", "인화성_HOT_WORK"),
    ("인화성", "work_type_MAINTENANCE", "인화성_MAINTENANCE"),
    ("인화성", "work_type_CLEANING", "인화성_CLEANING"),
    ("인화성", "work_type_STARTUP_SHUTDOWN", "인화성_STARTUP_SHUTDOWN"),
    ("고압가스", "work_type_MAINTENANCE", "고압가스_MAINTENANCE"),
    ("고압가스", "work_type_STARTUP_SHUTDOWN", "고압가스_STARTUP_SHUTDOWN"),
    ("산화성", "work_type_HOT_WORK", "산화성_HOT_WORK"),
    ("산화성", "work_type_CLEANING", "산화성_CLEANING"),
    ("산화성", "work_type_MAINTENANCE", "산화성_MAINTENANCE"),
    ("급성 독성(흡입)", "work_type_MAINTENANCE", "급성독성흡입_MAINTENANCE"),
    ("급성 독성(흡입)", "work_type_CLEANING", "급성독성흡입_CLEANING"),
    ("급성 독성(흡입)", "work_type_STARTUP_SHUTDOWN", "급성독성흡입_STARTUP_SHUTDOWN"),
    ("금속부식성 물질", "work_type_MAINTENANCE", "금속부식성_MAINTENANCE"),
    ("금속부식성 물질", "work_type_CLEANING", "금속부식성_CLEANING"),
    ("자연발화 및 과산화물", "work_type_MAINTENANCE", "자연발화과산화물_MAINTENANCE"),
    ("자연발화 및 과산화물", "work_type_CLEANING", "자연발화과산화물_CLEANING"),
    ("자연발화 및 과산화물", "work_type_STARTUP_SHUTDOWN", "자연발화과산화물_STARTUP_SHUTDOWN"),
    ("급성 수생환경 유해성", "work_type_CLEANING", "수생환경_CLEANING"),
    ("급성 수생환경 유해성", "work_type_MAINTENANCE", "수생환경_MAINTENANCE"),
]

# =========================
# 3) API 함수
# =========================
def test_msds_api_by_cas(cas_no, service_key):
    url = "https://apis.data.go.kr/B552468/msdschem/getChemList"
    params = {
        "serviceKey": service_key,
        "searchWrd": cas_no,
        "searchCnd": "1",
        "numOfRows": "10",
        "pageNo": "1"
    }
    response = requests.get(url, params=params, timeout=10)
    return response.status_code, response.text


def get_chemid_by_name(chem_name, service_key):
    url = "https://apis.data.go.kr/B552468/msdschem/getChemList"

    params = {
        "serviceKey": service_key,
        "searchWrd": chem_name,
        "searchCnd": "0",  # 🔥 국문명 검색
        "numOfRows": "10",
        "pageNo": "1"
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        return None, None, f"API 호출 실패: {response.status_code}"

    root = ET.fromstring(response.text)

    if root.findtext(".//resultCode") != "00":
        return None, None, root.findtext(".//resultMsg")

    items = root.findall(".//item")

    if not items:
        return None, None, "검색 결과 없음"

    # 🔥 첫 번째 결과 사용
    chem_id = items[0].findtext("chemId")
    chem_name_kor = items[0].findtext("chemNameKor")

    return chem_id, chem_name_kor, None

    return None, None, "물질명과 정확히 일치하는 물질이 없습니다."


def get_hazard_by_chemid(chem_id, service_key):
    url = "https://apis.data.go.kr/B552468/msdschem/getChemDetail02"
    params = {
        "serviceKey": service_key,
        "chemId": chem_id
    }
    response = requests.get(url, params=params, timeout=10)
    return response.status_code, response.text


def extract_classification_text(detail_xml):
    root = ET.fromstring(detail_xml)

    for item in root.findall(".//item"):
        if item.findtext("msdsItemNameKor") == "유해성·위험성 분류":
            return item.findtext("itemDetail")

    return ""


def parse_api_classification(classification_text):
    rows = []

    if not classification_text:
        return rows

    for item in classification_text.split("|"):
        item = item.strip()

        if ":" not in item:
            continue

        hazard, category = item.split(":", 1)

        rows.append({
            "API_위해성": hazard.strip(),
            "세부분류": category.strip()
        })

    return rows


def normalize_text(x):
    return (
        str(x)
        .replace(" ", "")
        .replace("\u3000", "")
        .replace("\n", "")
        .replace("\r", "")
        .replace("\t", "")
        .strip()
    )


def map_hazard_scores_by_excel(classification_text, mapping_df):
    hazard_scores = {}
    parsed_rows = parse_api_classification(classification_text)

    temp = mapping_df.copy()
    temp["_api_hazard_norm"] = temp["API_위해성"].apply(normalize_text)
    temp["_category_norm"] = temp["세부분류"].apply(normalize_text)

    for row in parsed_rows:
        api_hazard = normalize_text(row["API_위해성"])
        api_category = normalize_text(row["세부분류"])

        matched = temp[
            (temp["_api_hazard_norm"] == api_hazard) &
            (temp["_category_norm"] == api_category)
        ]

        if matched.empty:
            continue

        for _, m in matched.iterrows():
            model_group = str(m["물질군"]).strip()
            raw_score = pd.to_numeric(m["점수"], errors="coerce")

            if pd.isna(raw_score):
                continue

            if model_group not in hazard_scores:
                hazard_scores[model_group] = 0

            hazard_scores[model_group] = max(hazard_scores[model_group], float(raw_score))

    return hazard_scores

# =========================
# 4) 점수 보정 함수
# =========================
def convert_strength_score(raw_score):
    raw_score = pd.to_numeric(raw_score, errors="coerce")

    if pd.isna(raw_score):
        return 0

    raw_score = int(raw_score)
    return strength_mapping.get(raw_score, 0)


def sigmoid_rescale(score, k=0.08, center=30):
    return 100 / (1 + np.exp(-k * (score - center)))


def score_to_level(score):
    if score <= 40:
        return "🟢 안전유의"
    elif score <= 70:
        return "🟡 작업주의"
    else:
        return "🔴 위험경고"


def calculate_final_score(input_df, pred_prob, work_type, time_slot, chem_info_missing=0):
    base_prob = pred_prob

    damage_boost = 0

    if "time_slot_야간" in input_df.columns and input_df.loc[0, "time_slot_야간"] == 1:
        damage_boost += 0.10

    if "인화성" in input_df.columns and input_df.loc[0, "인화성"] > 0:
        damage_boost += 0.05

    uncertainty_boost = 0

    if chem_info_missing == 1:
        work_uncertainty_map = {
            "HOT_WORK": 0.15,
            "MAINTENANCE": 0.12,
            "CLEANING": 0.10,
            "STARTUP_SHUTDOWN": 0.10,
            "ROUTINE": 0.05,
            "IDLE": 0.00
        }

        time_uncertainty_map = {
            "야간": 0.05,
            "저녁": 0.03,
            "주간": 0.00,
            "미상": 0.00,
            "unknown": 0.00
        }

        uncertainty_boost += work_uncertainty_map.get(work_type, 0.05)
        uncertainty_boost += time_uncertainty_map.get(time_slot, 0.03)

    if time_slot in ["미상", "unknown"] and work_type in ["HOT_WORK", "MAINTENANCE"]:
        time_unknown_boost = 0.12
    elif time_slot in ["미상", "unknown"]:
        time_unknown_boost = 0.05
    else:
        time_unknown_boost = 0

    combined_prob = base_prob * (
        1
        + damage_boost
        + uncertainty_boost
        + time_unknown_boost
    )

    combined_prob = np.clip(combined_prob, 0, 1)

    raw_score = combined_prob * 100
    final_score = sigmoid_rescale(raw_score, k=0.08, center=30)
    final_score = float(np.clip(final_score, 0, 100))

    return final_score, score_to_level(final_score), {
        "base_prob": base_prob,
        "damage_boost": damage_boost,
        "uncertainty_boost": uncertainty_boost,
        "time_unknown_boost": time_unknown_boost,
        "combined_prob": combined_prob,
        "raw_score": raw_score
    }
def get_current_time_slot():
    now = datetime.now()
    current_hour = now.hour

    if 7 <= current_hour < 15:
        return "주간", now
    elif 15 <= current_hour < 23:
        return "저녁", now
    else:
        return "야간", now

# =========================
# 5) 모델 입력 생성
# =========================
def make_input_data(work_type, time_slot):
    input_df = pd.DataFrame(columns=model_columns)
    input_df.loc[0] = 0

    work_col = f"work_type_{work_type}"
    if work_col in input_df.columns:
        input_df.loc[0, work_col] = 1

    if work_col == "work_type_IDLE" and work_col in input_df.columns:
        input_df.loc[0, work_col] = 0.5

    time_col = f"time_slot_{time_slot}"
    if time_col in input_df.columns:
        input_df.loc[0, time_col] = 1

    hazard_scores = st.session_state.get("hazard_scores", {})

    for raw_col, raw_score in hazard_scores.items():
        model_col = col_alias.get(raw_col, raw_col)

        if model_col in input_df.columns:
            model_score = convert_strength_score(raw_score)
            input_df.loc[0, model_col] = model_score

    for hazard_col, work_col, new_col in interaction_rules:
        if hazard_col in input_df.columns and work_col in input_df.columns and new_col in input_df.columns:
            input_df.loc[0, new_col] = input_df.loc[0, hazard_col] * input_df.loc[0, work_col]

    input_df = input_df.apply(pd.to_numeric, errors="coerce").fillna(0)

    return input_df

# =========================
# 6) 화면
# =========================

if "hazard_scores" not in st.session_state:
    st.session_state.hazard_scores = {}

if "chem_id" not in st.session_state:
    st.session_state.chem_id = ""

if "chem_name" not in st.session_state:
    st.session_state.chem_name = ""

if "classification_text" not in st.session_state:
    st.session_state.classification_text = ""

if "result" not in st.session_state:
    st.session_state.result = {}

if "checklist_data" not in st.session_state:
    st.session_state.checklist_data = {}

if "checklist_remark" not in st.session_state:
    st.session_state.checklist_remark = ""

if "journal_data" not in st.session_state:
    st.session_state.journal_data = {}

if "journal_submitted" not in st.session_state:
    st.session_state.journal_submitted = False

if "work_logs" not in st.session_state:
    st.session_state.work_logs = []

if "work_log_csv_path" not in st.session_state:
    st.session_state.work_log_csv_path = "safety_tbm_work_logs.csv"



# =========================
# 페이지 실행부
# =========================
if st.session_state.page == "team_access":
    show_team_access()

elif st.session_state.page == "create_team":
    show_create_team()

elif st.session_state.page == "login":
    show_login()

elif st.session_state.page == "input":
    show_work_input()

elif st.session_state.page == "result":
    show_risk_result()

elif st.session_state.page == "checklist":
    show_checklist()

elif st.session_state.page == "journal":
    show_journal()

elif st.session_state.page == "manager":
    show_manager_dashboard()

open_help_if_requested()
show_active_help_popup()
