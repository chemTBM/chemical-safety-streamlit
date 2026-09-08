// 오프라인 캐싱 없이, PWA 설치 판정에 필요한 최소한의 서비스워커만 등록한다.
// Streamlit 정적 파일이 /app/static/ 경로로만 서빙되는 제약 때문에 이 워커의
// 기본 제어범위(scope)도 /app/static/ 로 한정되며, 실제 앱 화면은 제어하지 않는다.
self.addEventListener("install", (event) => {
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    self.clients.claim();
});

self.addEventListener("fetch", () => {
    // 캐싱하지 않고 항상 네트워크로 통과시킨다.
});
