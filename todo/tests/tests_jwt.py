from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.test import TestCase


# ---------------------------------------------------------
# JWT 인증 방식 테스트
# ---------------------------------------------------------
class JWTAuthTests(TestCase):
    """
    JWT 기반 로그인/토큰 재발급/로그아웃 API 테스트

    login:          POST  /api/login/          → access + refresh 발급
    token refresh:  POST  /api/token/refresh/  → access 재발급
    logout:         POST  /api/logout/         → 세션 정리
    """

    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/login/"
        self.refresh_url = "/api/token/refresh/"
        self.logout_url = "/api/logout/"

        self.user = User.objects.create_user(
            username="testuser",
            password="pass1234",
        )

    # =========================================================
    # 로그인 (토큰 발급)
    # =========================================================

    def test_login_returns_jwt_tokens(self):
        """정상 로그인 시 access, refresh 토큰 반환"""
        res = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)

    def test_login_wrong_password_returns_401(self):
        """잘못된 비밀번호 → 401"""
        res = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    def test_login_nonexistent_user_returns_401(self):
        """존재하지 않는 유저 → 401"""
        res = self.client.post(
            self.login_url,
            {"username": "nouser", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    # =========================================================
    # 토큰 재발급
    # =========================================================

    def _get_tokens(self):
        """로그인해서 access/refresh 토큰 반환 (헬퍼)"""
        res = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "pass1234"},
            format="json",
        )
        return res.json()

    def test_token_refresh_returns_new_access(self):
        """유효한 refresh 토큰으로 새 access 토큰 발급"""
        tokens = self._get_tokens()
        res = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.json())

    def test_token_refresh_with_invalid_token_returns_401(self):
        """잘못된 refresh 토큰 → 401"""
        res = self.client.post(
            self.refresh_url,
            {"refresh": "invalid.token.value"},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    # =========================================================
    # access 토큰으로 인증된 요청
    # =========================================================

    def test_authenticated_request_with_access_token(self):
        """access 토큰을 Authorization 헤더에 담아 보호된 엔드포인트 접근"""
        tokens = self._get_tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        res = self.client.get("/todo/viewsets/")
        # 인증 통과 → 200 (데이터 없으면 빈 목록)
        self.assertEqual(res.status_code, 200)

    def test_request_without_token_returns_401(self):
        """토큰 없이 보호된 엔드포인트 접근 → 401"""
        res = self.client.get("/todo/viewsets/")
        self.assertEqual(res.status_code, 401)

    # =========================================================
    # 로그아웃
    # =========================================================

    def test_logout_with_login_returns_200(self):
        """로그인 후 로그아웃 → 200, 메시지 확인"""
        self.client.force_login(self.user)
        res = self.client.post(self.logout_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["detail"], "로그아웃(세션 정리)")

    def test_logout_without_login_returns_401(self):
        """비로그인 상태에서 로그아웃 → 401 (IsAuthenticated)"""
        res = self.client.post(self.logout_url)
        self.assertEqual(res.status_code, 401)
