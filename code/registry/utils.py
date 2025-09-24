# utils.py
import requests

def healthcheck(endpoint: str) -> bool:
    """
    헬스체크: 에이전트의 /health 엔드포인트에 ping
    (에이전트가 /health API를 제공한다고 가정)
    """
    try:
        res = requests.get(f"{endpoint}/health", timeout=2)
        return res.status_code == 200
    except Exception:
        return False

