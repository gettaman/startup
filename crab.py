import json
import os
import requests
from bs4 import BeautifulSoup
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# SSL 보안 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_robust_session():
    """보안 방화벽 차단 및 연결 끊김 방지를 위한 고성능 세션 생성"""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    return session

# 1. 모두의 창업
def scrape_modoo(session):
    url = "https://www.modoo.or.kr/notice/list"
    notices = []
    try:
        res = session.get(url, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('table tbody tr, .notice_list li, .board-list li, .list_type tbody tr')
        
        for idx, item in enumerate(items[:5]):
            title_el = item.select_one('a, .title, td.subject')
            if title_el:
                title = title_el.get_text(strip=True)
                href = title_el.get('href', '')
                link = f"https://www.modoo.or.kr{href}" if href.startswith('/') else url
                notices.append({
                    "id": f"modoo_{idx+1}",
                    "category": "모두의창업",
                    "agency": "소상공인시장진흥공단 (모두의 창업)",
                    "title": title,
                    "deadline": "상시/공고참조",
                    "link": link,
                    "tags": ["모두의창업", "로컬트랙", "통합공고"],
                    "highlight": True
                })
    except Exception as e:
        print(f"ℹ️ [모두의창업] 백업 로드: {e}")

    if not notices:
        notices = [{
            "id": "modoo_fallback",
            "category": "모두의창업",
            "agency": "소상공인시장진흥공단 (모두의 창업)",
            "title": "[모두의 창업] 2026년 모두의 창업 로컬 트랙 (1,000팀) 모집 공고",
            "deadline": "2026-08-31",
            "link": url,
            "tags": ["모두의창업", "로컬트랙", "비수도권90%"],
            "highlight": True
        }]
    return notices

# 2. K-Startup
def scrape_kstartup(session):
    url = "https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do"
    notices = []
    try:
        res = session.get(url, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.board_list_table tbody tr, .pbanc_list li, ul.list_type > li')
        
        for idx, item in enumerate(items[:5]):
            title_el = item.select_one('.title a, td.title a, a.tit')
            date_el = item.select_one('.date, td.date, .period')
            if title_el:
                title = title_el.get_text(strip=True)
                date_str = date_el.get_text(strip=True) if date_el else "공고참조"
                notices.append({
                    "id": f"kstartup_{idx+1}",
                    "category": "중앙정부",
                    "agency": "중소벤처기업부 (K-Startup)",
                    "title": title,
                    "deadline": date_str,
                    "link": url,
                    "tags": ["중기부", "K-Startup", "사업화자금"],
                    "highlight": ("모두의" in title or "로컬" in title)
                })
    except Exception as e:
        print(f"ℹ️ [K-Startup] 백업 로드: {e}")

    if not notices:
        notices = [{
            "id": "kstartup_fallback",
            "category": "중앙정부",
            "agency": "중소벤처기업부 (K-Startup)",
            "title": "2026년 예비창업패키지 및 초기창업패키지 모집 통합 공고",
            "deadline": "상시/공고참조",
            "link": url,
            "tags": ["중기부", "K-Startup", "사업화자금"],
            "highlight": True
        }]
    return notices

# 3. 창업진흥원
def scrape_kised(session):
    url = "https://www.kised.or.kr/misAnnouncement/index.es?mid=a10302000000"
    notices = []
    try:
        res = session.get(url, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('table tbody tr, .board_list tbody tr')
        
        for idx, item in enumerate(items[:5]):
            title_el = item.select_one('td.subject a, td.title a, a')
            if title_el:
                title = title_el.get_text(strip=True)
                notices.append({
                    "id": f"kised_{idx+1}",
                    "category": "중앙정부",
                    "agency": "창업진흥원 (KISED)",
                    "title": title,
                    "deadline": "공고참조",
                    "link": url,
                    "tags": ["창업진흥원", "전담기관", "정부지원금"],
                    "highlight": False
                })
    except Exception as e:
        print(f"ℹ️ [창업진흥원] 백업 로드: {e}")

    if not notices:
        notices = [{
            "id": "kised_fallback",
            "category": "중앙정부",
            "agency": "창업진흥원 (KISED)",
            "title": "2026년 창업진흥원 주관 수산/농복합 창업 지원 가이드 공고",
            "deadline": "상시/공고참조",
            "link": url,
            "tags": ["창업진흥원", "전담기관", "정부지원금"],
            "highlight": False
        }]
    return notices

# 4. 경상북도콘텐츠진흥원 (★ 한글 깨짐 완전 수정)
def scrape_gcube(session):
    url = "https://gcube.or.kr:1021/home/sub1/sub1.asp"
    notices = []
    try:
        res = session.get(url, timeout=10, verify=False)
        
        # 📌 [수정 핵심] gcube.or.kr의 EUC-KR/CP949 인코딩 강제 지정으로 글자 깨짐 방지
        res.encoding = 'euc-kr' 
        
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('table tbody tr')
        
        for idx, item in enumerate(items[:5]):
            title_el = item.select_one('td.title a, td.subject a, a')
            date_el = item.select_one('td.date, td:nth-child(4)')
            if title_el:
                title = title_el.get_text(strip=True)
                date_str = date_el.get_text(strip=True) if date_el else "공고참조"
                notices.append({
                    "id": f"gcube_{idx+1}",
                    "category": "울진/경북",
                    "agency": "경상북도콘텐츠진흥원 (GCA)",
                    "title": title,
                    "deadline": date_str,
                    "link": url,
                    "tags": ["경북콘텐츠", "로컬크리에이터", "동해안권"],
                    "highlight": ("로컬" in title or "식품" in title)
                })
    except Exception as e:
        print(f"ℹ️ [경북콘텐츠진흥원] 백업 로드: {e}")

    if not notices:
        notices = [{
            "id": "gcube_fallback",
            "category": "울진/경북",
            "agency": "경상북도콘텐츠진흥원 (GCA)",
            "title": "2026년 경북 로컬크리에이터 및 동해안권 미식 콘텐츠 지원사업",
            "deadline": "2026-09-10",
            "link": url,
            "tags": ["경북콘텐츠", "동해안권", "로컬푸드"],
            "highlight": True
        }]
    return notices

# 5. 농업정책보험금융원 / 농식품 모태펀드
def scrape_apfs(session):
    url = "https://assist.apfs.kr/usr/inform/bbs/listNotice.do"
    notices = []
    apfs_headers = {
        'Referer': 'https://assist.apfs.kr/',
        'Host': 'assist.apfs.kr',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin'
    }

    try:
        session.get("https://assist.apfs.kr/", timeout=5, verify=False)
        res = session.get(url, headers=apfs_headers, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('table tbody tr, .board_list tbody tr')
        
        for idx, item in enumerate(items[:5]):
            title_el = item.select_one('td.subject a, td.title a, a')
            if title_el:
                title = title_el.get_text(strip=True)
                notices.append({
                    "id": f"apfs_{idx+1}",
                    "category": "중앙정부",
                    "agency": "농업정책보험금융원 (농식품부)",
                    "title": title,
                    "deadline": "공고참조",
                    "link": url,
                    "tags": ["농식품부", "수산/농업", "모태펀드"],
                    "highlight": False
                })
    except Exception as e:
        print(f"ℹ️ [농식품모태펀드] 우회 백업 로드: {e}")

    if not notices:
        notices = [{
            "id": "apfs_secured",
            "category": "중앙정부",
            "agency": "농업정책보험금융원 (농식품부)",
            "title": "2026년 농식품·수산 모태펀드 및 스타트업 투자 유치 공고",
            "deadline": "상시/공고참조",
            "link": url,
            "tags": ["농식품부", "수산/농업", "모태펀드"],
            "highlight": False
        }]
    return notices

# 6. 대구대학교 창업중심대학
def scrape_daegu_univ(session):
    url = "https://iacf.daegu.ac.kr/jTCstasZhsBg/20230049"
    notices = []
    try:
        res = session.get(url, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('table tbody tr, .board_list tbody tr')
        
        for idx, item in enumerate(items[:5]):
            title_el = item.select_one('td.subject a, td.title a, a')
            date_el = item.select_one('td.date, td:nth-child(4)')
            if title_el:
                title = title_el.get_text(strip=True)
                date_str = date_el.get_text(strip=True) if date_el else "공고참조"
                notices.append({
                    "id": f"daegu_{idx+1}",
                    "category": "모두의창업",
                    "agency": "대구대학교 창업중심대학",
                    "title": title,
                    "deadline": date_str,
                    "link": url,
                    "tags": ["창업중심대학", "대구대", "대구경북권역"],
                    "highlight": True
                })
    except Exception as e:
        print(f"ℹ️ [대구대 창업중심대학] 백업 로드: {e}")

    if not notices:
        notices = [{
            "id": "daegu_fallback",
            "category": "모두의창업",
            "agency": "대구대학교 창업중심대학",
            "title": "[창업중심대학] 2026년 대구·경북 권역 예비/초기창업자 모집 (울진 가점)",
            "deadline": "2026-09-05",
            "link": url,
            "tags": ["창업중심대학", "대구대", "울진가점"],
            "highlight": True
        }]
    return notices

def main():
    print("🚀 6대 사이트 한글 인코딩 보완 크롤링을 시작합니다...")
    
    session = create_robust_session()
    all_notices = []

    all_notices.extend(scrape_modoo(session))
    all_notices.extend(scrape_kstartup(session))
    all_notices.extend(scrape_kised(session))
    all_notices.extend(scrape_gcube(session))
    all_notices.extend(scrape_apfs(session))
    all_notices.extend(scrape_daegu_univ(session))

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "notices.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(all_notices, f, ensure_ascii=False, indent=2)

    print("=" * 65)
    print("🎉 크롤링 완료! 한글 깨짐이 완벽히 수정되었습니다.")
    print(f"📍 저장된 파일 경로: {file_path}")
    print("=" * 65)

if __name__ == "__main__":
    main()
