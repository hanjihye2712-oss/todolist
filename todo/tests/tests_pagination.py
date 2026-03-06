from django.test import TestCase
from rest_framework.test import APIClient

from ..models import Todo


# ---------------------------------------------------------
# CustomPageNumberPagination 동작을 검증하는 테스트 클래스
# ---------------------------------------------------------
class TodoPaginationTests(TestCase):
    """
    CustomPageNumberPagination 페이지네이션 테스트

    settings.py의 PAGE_SIZE = 3 (기본 페이지 크기)
    대상 URL: GET /todo/viewsets/view/

    응답 구조:
        {
            "data": [...],
            "page_size": int,
            "total_count": int,
            "page_count": int,
            "current_page": int,
            "next": str | null,
            "previous": str | null,
        }
    """

    BASE_URL = "/todo/viewsets/view/"

    # ---------------------------------------------------------
    # 테스트 시작 전 공통 데이터 준비
    # ---------------------------------------------------------
    def setUp(self):
        self.client = APIClient()

        # 총 7개의 Todo 생성 (기본 page_size=3 기준으로 3페이지 구성)
        for i in range(1, 8):
            Todo.objects.create(
                name=f"할일 {i}",
                description=f"설명 {i}",
                complete=False,
                exp=i,
            )

    # ---------------------------------------------------------
    # 1. 기본 응답 구조 검증
    # ---------------------------------------------------------
    def test_response_has_pagination_keys(self):
        """페이지네이션 응답에 필수 키가 모두 포함되어 있는지 확인"""
        res = self.client.get(self.BASE_URL)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        for key in (
            "data",
            "page_size",
            "total_count",
            "page_count",
            "current_page",
            "next",
            "previous",
        ):
            self.assertIn(key, data, msg=f"응답에 '{key}' 키가 없습니다.")

    # ---------------------------------------------------------
    # 2. 기본 page_size(3) 적용 확인
    # ---------------------------------------------------------
    def test_default_page_size(self):
        """기본 page_size=3 으로 한 페이지에 3개 반환되는지 확인"""
        res = self.client.get(self.BASE_URL)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(len(data["data"]), 3)
        self.assertEqual(data["page_size"], 3)

    # ---------------------------------------------------------
    # 3. total_count / page_count 정확성
    # ---------------------------------------------------------
    def test_total_count_and_page_count(self):
        """total_count=7, page_count=3 인지 확인"""
        res = self.client.get(self.BASE_URL)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data["total_count"], 7)
        self.assertEqual(data["page_count"], 3)  # ceil(7/3) = 3

    # ---------------------------------------------------------
    # 4. current_page 번호 확인
    # ---------------------------------------------------------
    def test_current_page_number(self):
        """첫 번째 페이지 요청 시 current_page=1, 두 번째 페이지 요청 시 current_page=2"""
        res1 = self.client.get(self.BASE_URL, {"page": 1})
        self.assertEqual(res1.json()["current_page"], 1)

        res2 = self.client.get(self.BASE_URL, {"page": 2})
        self.assertEqual(res2.json()["current_page"], 2)

    # ---------------------------------------------------------
    # 5. next / previous 링크 확인
    # ---------------------------------------------------------
    def test_next_link_on_first_page(self):
        """1페이지: next 링크가 존재하고 previous는 null"""
        res = self.client.get(self.BASE_URL, {"page": 1})
        data = res.json()

        self.assertIsNotNone(data["next"])
        self.assertIsNone(data["previous"])

    def test_previous_link_on_last_page(self):
        """마지막 페이지: previous 링크가 존재하고 next는 null"""
        res = self.client.get(self.BASE_URL, {"page": 3})
        data = res.json()

        self.assertIsNotNone(data["previous"])
        self.assertIsNone(data["next"])

    def test_both_links_on_middle_page(self):
        """중간 페이지: next와 previous 모두 존재"""
        res = self.client.get(self.BASE_URL, {"page": 2})
        data = res.json()

        self.assertIsNotNone(data["next"])
        self.assertIsNotNone(data["previous"])

    # ---------------------------------------------------------
    # 6. page_size 쿼리 파라미터로 크기 변경
    # ---------------------------------------------------------
    def test_custom_page_size(self):
        """?page_size=5 로 요청 시 5개 반환"""
        res = self.client.get(self.BASE_URL, {"page_size": 5})
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(len(data["data"]), 5)
        self.assertEqual(data["page_size"], 5)

    def test_page_size_1(self):
        """?page_size=1 로 요청 시 1개 반환, page_count=7"""
        res = self.client.get(self.BASE_URL, {"page_size": 1})
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["page_count"], 7)

    # ---------------------------------------------------------
    # 7. page_size=all → 전체 데이터 반환
    # ---------------------------------------------------------
    def test_page_size_all(self):
        """?page_size=all 요청 시 모든 데이터(7개) 반환"""
        res = self.client.get(self.BASE_URL, {"page_size": "all"})
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(len(data["data"]), 7)
        self.assertEqual(data["total_count"], 7)
        self.assertEqual(data["page_count"], 1)

    # ---------------------------------------------------------
    # 8. 잘못된 page_size → 기본값(3) 사용
    # ---------------------------------------------------------
    def test_invalid_page_size_falls_back_to_default(self):
        """?page_size=abc 처럼 숫자가 아닌 값이면 기본 page_size=3 사용"""
        res = self.client.get(self.BASE_URL, {"page_size": "abc"})
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(len(data["data"]), 3)

    # ---------------------------------------------------------
    # 9. 데이터가 없을 때 빈 배열 반환
    # ---------------------------------------------------------
    def test_empty_queryset(self):
        """Todo가 없을 때 data가 빈 리스트인지 확인"""
        Todo.objects.all().delete()

        res = self.client.get(self.BASE_URL)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data["data"], [])
        self.assertEqual(data["total_count"], 0)

    # ---------------------------------------------------------
    # 10. 마지막 페이지 데이터 개수 확인 (나머지)
    # ---------------------------------------------------------
    def test_last_page_has_remaining_items(self):
        """마지막 페이지(3페이지)에 나머지 1개(7 % 3 = 1)만 반환되는지 확인"""
        res = self.client.get(self.BASE_URL, {"page": 3})
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(len(data["data"]), 1)
