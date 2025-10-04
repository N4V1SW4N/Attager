import json
from typing import Any, Dict, List


class CustomerTool:
    """고객 관리 툴: 미리 정의된 리스트에서 고객 정보 + 구매 내역 조회"""

    def __init__(self):
        # 고객 기본 정보
        self.customers: List[Dict[str, Any]] = [
            {
                "customer_id": "5001",
                "name": "홍길동",
                "age": 32,
                "address": "서울 강남구",
                "phone": "010-1234-5678"
            },
            {
                "customer_id": "5002",
                "name": "김철수",
                "age": 28,
                "address": "부산 해운대구",
                "phone": "010-2345-6789"
            },
            {
                "customer_id": "5003",
                "name": "이영희",
                "age": 41,
                "address": "대구 수성구",
                "phone": "010-3456-7890"
            },
        ]

        # 상품 정보
        self.items: List[Dict[str, Any]] = [
            {"item_id": "1001", "name": "전자부품A", "price": 12000},
            {"item_id": "1002", "name": "센서C", "price": 35000},
            {"item_id": "1003", "name": "모듈D", "price": 22000},
        ]

        # 주문 내역
        self.orders: List[Dict[str, Any]] = [
            {"order_id": "8001", "customer_id": "5001", "item_id": "1001", "quantity": 2, "order_date": "2025-09-20"},
            {"order_id": "8002", "customer_id": "5002", "item_id": "1002", "quantity": 1, "order_date": "2025-09-21"},
            {"order_id": "8003", "customer_id": "5003", "item_id": "1003", "quantity": 3, "order_date": "2025-09-22"},
        ]

    def get_customer_info(self, name: str) -> Dict[str, Any]:
        """고객 이름으로 고객 기본 정보 조회"""
        for customer in self.customers:
            if customer["name"] == name:
                return customer
        return {}

    def get_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        """고객 ID로 구매 내역 조회"""
        orders = []
        for order in self.orders:
            if order["customer_id"] == customer_id:
                # 상품 정보 붙이기
                item = next((i for i in self.items if i["item_id"] == order["item_id"]), None)
                if item:
                    order_with_item = dict(order)
                    order_with_item["item_name"] = item["name"]
                    order_with_item["price"] = item["price"]
                    orders.append(order_with_item)
        return orders

    def query(self, name: str) -> Dict[str, Any]:
        """최종 질의: 이름 → 고객 정보 + 구매 내역"""
        customer = self.get_customer_info(name)
        if not customer:
            return {"error": f"'{name}' 고객을 찾을 수 없습니다."}
        orders = self.get_orders(customer["customer_id"])
        return {
            "customer": customer,
            "orders": orders
        }


# 단독 실행 테스트용
if __name__ == "__main__":
    tool = CustomerTool()
    result = tool.query("홍길동")
    print(json.dumps(result, ensure_ascii=False, indent=2))
