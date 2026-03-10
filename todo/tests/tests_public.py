from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.test import TestCase

from ..models import Todo


# ---------------------------------------------------------
# 다른 사용자 글 보기 (is_public) 테스트
# ---------------------------------------------------------
# 검증 항목
#
# 1. is_public=True  → 다른 사용자 목록에 노출됨
# 2. is_public=False → 다른 사용자 목록에 노출 안 됨
# 3. is_public=True  → 다른 사용자가 상세 조회 가능
# 4. is_public=False → 다른 사용자가 상세 조회 시 404
# 5. 본인 비공개 글은 본인 목록에 노출됨
# 6. 목록 응답에 작성자 username 포함 확인
# ---------------------------------------------------------
class TodoPublicTests(TestCase):

    LIST_URL = "/todo/viewsets/view/"

    def setUp(self):
        self.client = APIClient()

        # 계정A : 글 작성자
        self.user_a = User.objects.create_user(username="userA", password="pass1234")

        # 계정B : 다른 사용자
        self.user_b = User.objects.create_user(username="userB", password="pass1234")

        # A의 공개 Todo
        self.public_todo = Todo.objects.create(
            name="공개 Todo",
            description="누구나 볼 수 있음",
            user=self.user_a,
            is_public=True,
        )

        # A의 비공개 Todo
        self.private_todo = Todo.objects.create(
            name="비공개 Todo",
            description="본인만 볼 수 있음",
            user=self.user_a,
            is_public=False,
        )

    def _login(self, user):
        """JWT 토큰 발급 후 클라이언트에 인증 설정"""
        res = self.client.post(
            "/api/login/",
            {"username": user.username, "password": "pass1234"},
            format="json",
        )
        token = res.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # =========================================================
    # 1. is_public=True → 다른 사용자 목록에 노출됨
    # =========================================================
    def test_public_todo_visible_to_other_user(self):
        """B가 목록 조회 시 A의 공개 글이 포함되어야 함"""
        self._login(self.user_b)

        res = self.client.get(self.LIST_URL)
        self.assertEqual(res.status_code, 200)

        ids = [item["id"] for item in res.json()["data"]]
        self.assertIn(self.public_todo.id, ids)

    # =========================================================
    # 2. is_public=False → 다른 사용자 목록에 노출 안 됨
    # =========================================================
    def test_private_todo_hidden_from_other_user(self):
        """B가 목록 조회 시 A의 비공개 글이 포함되지 않아야 함"""
        self._login(self.user_b)

        res = self.client.get(self.LIST_URL)
        self.assertEqual(res.status_code, 200)

        ids = [item["id"] for item in res.json()["data"]]
        self.assertNotIn(self.private_todo.id, ids)

    # =========================================================
    # 3. is_public=True → 다른 사용자가 상세 조회 가능
    # =========================================================
    def test_public_todo_detail_accessible_by_other_user(self):
        """B가 A의 공개 글 상세 조회 시 200 반환"""
        self._login(self.user_b)

        res = self.client.get(f"{self.LIST_URL}{self.public_todo.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], self.public_todo.id)

    # =========================================================
    # 4. is_public=False → 다른 사용자가 상세 조회 시 404
    # =========================================================
    def test_private_todo_detail_returns_404_for_other_user(self):
        """B가 A의 비공개 글 상세 조회 시 404 반환"""
        self._login(self.user_b)

        res = self.client.get(f"{self.LIST_URL}{self.private_todo.id}/")
        self.assertEqual(res.status_code, 404)

    # =========================================================
    # 5. 본인 비공개 글은 본인 목록에 노출됨
    # =========================================================
    def test_private_todo_visible_to_owner(self):
        """A가 목록 조회 시 자신의 비공개 글도 포함되어야 함"""
        self._login(self.user_a)

        res = self.client.get(self.LIST_URL)
        self.assertEqual(res.status_code, 200)

        ids = [item["id"] for item in res.json()["data"]]
        self.assertIn(self.private_todo.id, ids)

    # =========================================================
    # 6. 목록 응답에 작성자 username 포함 확인
    # =========================================================
    def test_list_includes_author_username(self):
        """B가 보는 목록에서 A의 공개 글에 username 필드가 있어야 함"""
        self._login(self.user_b)

        res = self.client.get(self.LIST_URL)
        self.assertEqual(res.status_code, 200)

        public_item = next(
            (item for item in res.json()["data"] if item["id"] == self.public_todo.id),
            None,
        )
        self.assertIsNotNone(public_item)
        self.assertEqual(public_item["username"], "userA")
