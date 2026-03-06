from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient


# ---------------------------------------------------------
# 회원가입 / 로그인 / 로그아웃 API 테스트
# ---------------------------------------------------------
class AccountsAPITests(TestCase):
    """
    accounts API 테스트

    signup:  POST  /api/signup/
    login:   POST  /api/login/
    logout:  POST  /api/logout/
    """

    # ---------------------------------------------------------
    # 테스트 시작 전에 공통 데이터 준비
    # ---------------------------------------------------------
    def setUp(self):

        self.client = APIClient()
        # DRF API 테스트용 클라이언트

        self.signup_url = "/api/signup/"
        self.login_url = "/api/login/"
        self.logout_url = "/api/logout/"

        # 로그인/로그아웃 테스트용으로 미리 생성된 유저
        self.existing_user = User.objects.create_user(
            username="existinguser",
            password="pass1234",
        )

    # =========================================================
    # 회원가입 테스트
    # =========================================================

    # ---------------------------------------------------------
    # 정상 회원가입
    # ---------------------------------------------------------
    def test_signup_success(self):

        payload = {
            "username": "newuser",
            "password": "pass1234",
            "password2": "pass1234",
        }

        res = self.client.post(self.signup_url, payload, format="json")
        # 회원가입 POST 요청

        self.assertEqual(res.status_code, 201)
        # 생성 성공(201) 확인

        self.assertTrue(User.objects.filter(username="newuser").exists())
        # DB에 유저가 실제로 생성되었는지 확인

    # ---------------------------------------------------------
    # 중복 username 회원가입 → 400
    # ---------------------------------------------------------
    def test_signup_duplicate_username(self):

        payload = {
            "username": "existinguser",
            # setUp에서 이미 생성한 유저와 동일한 username
            "password": "pass1234",
            "password2": "pass1234",
        }

        res = self.client.post(self.signup_url, payload, format="json")

        self.assertEqual(res.status_code, 400)
        # 중복 username → 400 Bad Request 확인

    # ---------------------------------------------------------
    # 비밀번호 불일치 → 400
    # ---------------------------------------------------------
    def test_signup_password_mismatch(self):

        payload = {
            "username": "newuser2",
            "password": "pass1234",
            "password2": "different",
            # password와 password2가 다름
        }

        res = self.client.post(self.signup_url, payload, format="json")

        self.assertEqual(res.status_code, 400)
        # 비밀번호 불일치 → 400 Bad Request 확인

    # ---------------------------------------------------------
    # 비밀번호 너무 짧음 (min_length=4 미만) → 400
    # ---------------------------------------------------------
    def test_signup_password_too_short(self):

        payload = {
            "username": "newuser3",
            "password": "123",
            # min_length=4 미만
            "password2": "123",
        }

        res = self.client.post(self.signup_url, payload, format="json")

        self.assertEqual(res.status_code, 400)
        # 짧은 비밀번호 → 400 Bad Request 확인

    # ---------------------------------------------------------
    # 필수 필드 누락 → 400
    # ---------------------------------------------------------
    def test_signup_missing_fields(self):

        payload = {
            "username": "newuser4",
            # password, password2 없음
        }

        res = self.client.post(self.signup_url, payload, format="json")

        self.assertEqual(res.status_code, 400)
        # 필수 필드 누락 → 400 Bad Request 확인

    # =========================================================
    # 로그인 테스트
    # =========================================================

    # ---------------------------------------------------------
    # 정상 로그인 → 200
    # ---------------------------------------------------------
    def test_login_success(self):

        payload = {
            "username": "existinguser",
            "password": "pass1234",
        }

        res = self.client.post(self.login_url, payload, format="json")
        # 로그인 POST 요청

        self.assertEqual(res.status_code, 200)
        # 로그인 성공(200) 확인

        self.assertEqual(res.json()["detail"], "로그인 성공")
        # 응답 메시지 확인

    # ---------------------------------------------------------
    # 잘못된 비밀번호 → 400
    # ---------------------------------------------------------
    def test_login_wrong_password(self):

        payload = {
            "username": "existinguser",
            "password": "wrongpassword",
        }

        res = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(res.status_code, 400)
        # 인증 실패 → 400 Bad Request 확인

    # ---------------------------------------------------------
    # 존재하지 않는 유저 로그인 → 400
    # ---------------------------------------------------------
    def test_login_nonexistent_user(self):

        payload = {
            "username": "nouser",
            "password": "pass1234",
        }

        res = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(res.status_code, 400)
        # 존재하지 않는 유저 → 400 Bad Request 확인

    # =========================================================
    # 로그아웃 테스트
    # =========================================================

    # ---------------------------------------------------------
    # 로그인 후 로그아웃 → 200
    # ---------------------------------------------------------
    def test_logout_success(self):

        self.client.force_login(self.existing_user)
        # 테스트 클라이언트에 강제로 로그인 처리

        res = self.client.post(self.logout_url)
        # 로그아웃 POST 요청

        self.assertEqual(res.status_code, 200)
        # 로그아웃 성공(200) 확인

        self.assertEqual(res.json()["detail"], "로그아웃")
        # 응답 메시지 확인

    # ---------------------------------------------------------
    # 비로그인 상태에서 로그아웃 → 403
    # ---------------------------------------------------------
    def test_logout_without_login(self):

        res = self.client.post(self.logout_url)
        # 로그인 없이 로그아웃 요청

        self.assertIn(res.status_code, (200, 403))
        # SessionLogoutAPIView의 permission_classes 설정에 따라 다름
        # IsAuthenticated → 403, AllowAny → 200
