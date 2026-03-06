import base64
import io
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from PIL import Image

from ..models import Todo


def make_image(name="test.png"):
    """테스트용 가짜 이미지 파일 생성"""
    buf = io.BytesIO()
    img = Image.new("RGB", (10, 10), color="red")
    img.save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")


# ---------------------------------------------------------
# ✅ 이미지 업로드 관련 기능을 검증하는 테스트 클래스
# ---------------------------------------------------------
class TodoImageTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        # 기본 Todo 1개 생성 (이미지 없음)
        self.todo = Todo.objects.create(
            name="운동",
            description="스쿼트 50회",
            complete=False,
            exp=10,
        )

    # -----------------------------------------------------
    # 1️⃣ 이미지 없이 Todo 생성 → image 필드가 빈값이어야 함
    # -----------------------------------------------------
    def test_create_without_image(self):
        payload = {
            "name": "독서",
            "description": "책 10페이지",
            "complete": False,
            "exp": 5,
        }
        res = self.client.post("/todo/viewsets/view/", payload, format="multipart")

        self.assertEqual(res.status_code, 201)
        # image 필드가 null 또는 빈 문자열인지 확인
        self.assertFalse(res.json().get("image"))

    # -----------------------------------------------------
    # 2️⃣ 이미지와 함께 Todo 생성 → image URL이 응답에 포함되어야 함
    # -----------------------------------------------------
    def test_create_with_image(self):
        payload = {
            "name": "그림 그리기",
            "description": "스케치",
            "complete": False,
            "exp": 15,
            "image": make_image("create_test.png"),
        }
        res = self.client.post("/todo/viewsets/view/", payload, format="multipart")

        self.assertEqual(res.status_code, 201)
        # image 필드에 값이 있는지 확인
        self.assertTrue(res.json().get("image"))
        # 이미지 경로에 'todo_images/'가 포함되어 있는지 확인
        self.assertIn("todo_images/", res.json()["image"])

    # -----------------------------------------------------
    # 3️⃣ 기존 Todo에 이미지 추가 (PATCH)
    # -----------------------------------------------------
    def test_patch_add_image(self):
        payload = {"image": make_image("patch_test.png")}
        res = self.client.patch(
            f"/todo/viewsets/view/{self.todo.id}/", payload, format="multipart"
        )

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("image"))
        self.assertIn("todo_images/", res.json()["image"])

        # DB에도 저장됐는지 확인
        self.todo.refresh_from_db()
        self.assertTrue(self.todo.image)

    # -----------------------------------------------------
    # 4️⃣ 이미지가 있는 Todo 조회 → image URL 반환 확인
    # -----------------------------------------------------
    def test_retrieve_with_image(self):
        # 이미지가 있는 Todo 생성
        todo_with_img = Todo.objects.create(
            name="사진 찍기",
            description="풍경 사진",
            complete=False,
            exp=20,
            image=make_image("retrieve_test.png"),
        )

        res = self.client.get(f"/todo/viewsets/view/{todo_with_img.id}/")

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("image"))

    # -----------------------------------------------------
    # 5️⃣ 이미지 없는 Todo 조회 → image 필드가 빈값이어야 함
    # -----------------------------------------------------
    def test_retrieve_without_image(self):
        res = self.client.get(f"/todo/viewsets/view/{self.todo.id}/")

        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json().get("image"))

    # -----------------------------------------------------
    # 6️⃣ PUT으로 이미지 포함 전체 수정
    # -----------------------------------------------------
    def test_put_with_image(self):
        payload = {
            "name": "운동(수정)",
            "description": "런닝 30분",
            "complete": False,
            "exp": 20,
            "image": make_image("put_test.png"),
        }
        res = self.client.put(
            f"/todo/viewsets/view/{self.todo.id}/", payload, format="multipart"
        )

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("image"))
        self.assertIn("todo_images/", res.json()["image"])


# ---------------------------------------------------------
# ✅ Base64 인코딩/디코딩 방식으로 이미지를 다루는 테스트 클래스
#
# [Base64 방식이란?]
# 이미지(바이너리) → base64 인코딩 → 문자열 (JSON에 담을 수 있음)
# 문자열           → base64 디코딩 → 이미지(바이너리) 복원
#
# multipart 방식:  파일을 직접 form-data로 첨부해서 전송
# base64 방식:     이미지를 문자열로 변환해서 JSON body에 넣어 전송
# ---------------------------------------------------------
class TodoBase64ImageTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def make_base64_image(self):
        """PIL 이미지 → PNG 바이너리 → base64 문자열 변환"""
        buf = io.BytesIO()
        img = Image.new("RGB", (10, 10), color="blue")
        img.save(buf, format="PNG")
        buf.seek(0)
        # 바이너리 → base64 인코딩 → UTF-8 문자열
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        # 브라우저/API에서 쓰는 표준 형식으로 앞에 헤더 붙이기
        return f"data:image/png;base64,{encoded}"

    # -----------------------------------------------------
    # 1️⃣ base64 인코딩 결과가 문자열인지 확인
    # -----------------------------------------------------
    def test_base64_encode_returns_string(self):
        result = self.make_base64_image()

        # 결과가 문자열인지 확인
        self.assertIsInstance(result, str)
        # base64 이미지 문자열의 표준 헤더로 시작하는지 확인
        self.assertTrue(result.startswith("data:image/png;base64,"))

    # -----------------------------------------------------
    # 2️⃣ base64 디코딩 → 원본 이미지 복원 (라운드트립 검증)
    # -----------------------------------------------------
    def test_base64_decode_restores_image(self):
        # 원본 이미지 바이너리 생성
        buf = io.BytesIO()
        img = Image.new("RGB", (10, 10), color="blue")
        img.save(buf, format="PNG")
        original_bytes = buf.getvalue()

        # 인코딩
        encoded = base64.b64encode(original_bytes).decode("utf-8")

        # 디코딩
        decoded_bytes = base64.b64decode(encoded)

        # 원본과 디코딩 결과가 동일한지 확인
        self.assertEqual(original_bytes, decoded_bytes)

    # -----------------------------------------------------
    # 3️⃣ base64 문자열에서 헤더 분리 → 실제 데이터 추출
    # -----------------------------------------------------
    def test_base64_header_split(self):
        base64_str = self.make_base64_image()

        # "data:image/png;base64,iVBOR..." 형식에서 헤더와 데이터 분리
        header, imgstr = base64_str.split(";base64,")

        # 헤더에서 확장자 추출
        ext = header.split("/")[-1]

        self.assertEqual(ext, "png")
        # imgstr 이 실제 base64 데이터인지 확인 (디코딩 가능한지)
        decoded = base64.b64decode(imgstr)
        self.assertIsInstance(decoded, bytes)
        self.assertGreater(len(decoded), 0)

    # -----------------------------------------------------
    # 4️⃣ base64로 만든 이미지를 파일 객체로 변환 후 DB 저장
    #    (base64 → 디코딩 → 파일 객체 → Todo.image 저장)
    # -----------------------------------------------------
    def test_base64_to_file_and_save(self):
        base64_str = self.make_base64_image()

        # 헤더 분리 후 base64 디코딩
        _, imgstr = base64_str.split(";base64,")
        image_bytes = base64.b64decode(imgstr)

        # 바이너리 → Django 파일 객체로 변환
        image_file = SimpleUploadedFile(
            "base64_image.png", image_bytes, content_type="image/png"
        )

        # Todo에 이미지 저장
        todo = Todo.objects.create(
            name="base64 테스트",
            description="base64 이미지 저장",
            complete=False,
            exp=5,
            image=image_file,
        )

        # DB에 저장됐는지 확인
        todo.refresh_from_db()
        self.assertTrue(todo.image)
        self.assertIn("todo_images/", todo.image.name)
