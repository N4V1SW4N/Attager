# storage.py
from typing import Dict, List, Optional
from models import AgentCard

class InMemoryStorage:
    def __init__(self):
        self._registry: Dict[str, AgentCard] = {}

    def register(self, card: AgentCard):
        """에이전트 카드 등록"""
        self._registry[card.name] = card

    def get(self, name: str) -> Optional[AgentCard]:
        """에이전트 이름으로 조회"""
        return self._registry.get(name)

    def list_all(self) -> List[AgentCard]:
        """모든 에이전트 반환"""
        return list(self._registry.values())

    def unregister(self, name: str) -> bool:
        """에이전트 해제"""
        if name in self._registry:
            del self._registry[name]
            return True
        return False

# 전역 스토리지 인스턴스
storage = InMemoryStorage()

