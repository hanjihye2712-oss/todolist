from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from todo.models import Todo
from interaction.models import TodoLike, TodoBookmark, TodoComment


# =========================================================
# 공통 setUp 베이스 클래스
# =========================================================
class InteractionTestBase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(username="testuser", password="pass1234")
        self.other_user = User.objects.create_user(
            username="other", password="pass1234"
        )

        self.todo = Todo.objects.create(
            name="테스트 할일",
            description="설명",
            complete=False,
            exp=1,
            user=self.user,
        )

        self.client.force_login(self.user)


# =========================================================
# 좋아요 토글 테스트
# POST /interaction/like/<todo_id>/
# =========================================================
class TodoLikeToggleTests(InteractionTestBase):

    def url(self):
        return f"/interaction/like/{self.todo.id}/"

    # ---------------------------------------------------------
    # 1. 비로그인 → 401
    # ---------------------------------------------------------
    def test_like_requires_login(self):
        """비로그인 상태에서 좋아요 요청 → 401"""
        self.client.logout()
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, 401)

    # ---------------------------------------------------------
    # 2. 처음 좋아요 → liked=True, like_count=1
    # ---------------------------------------------------------
    def test_like_first_time(self):
        """처음 좋아요 → liked=True, like_count=1"""
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["liked"])
        self.assertEqual(data["like_count"], 1)

    # ---------------------------------------------------------
    # 3. 두 번 좋아요 → 취소, liked=False, like_count=0
    # ---------------------------------------------------------
    def test_like_toggle_cancels(self):
        """이미 좋아요한 상태에서 다시 누르면 취소 → liked=False, like_count=0"""
        self.client.post(self.url())
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["liked"])
        self.assertEqual(data["like_count"], 0)

    # ---------------------------------------------------------
    # 4. 여러 사용자 좋아요 → like_count 정확히 집계
    # ---------------------------------------------------------
    def test_like_count_multiple_users(self):
        """두 유저가 각각 좋아요 → like_count=2"""
        self.client.post(self.url())

        self.client.force_login(self.other_user)
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["like_count"], 2)

    # ---------------------------------------------------------
    # 5. 존재하지 않는 Todo → 404
    # ---------------------------------------------------------
    def test_like_nonexistent_todo_returns_404(self):
        """존재하지 않는 todo_id → 404"""
        res = self.client.post("/interaction/like/99999/")
        self.assertEqual(res.status_code, 404)

    # ---------------------------------------------------------
    # 6. DB에 TodoLike 객체 생성/삭제 확인
    # ---------------------------------------------------------
    def test_like_creates_and_deletes_db_record(self):
        """좋아요 시 DB에 TodoLike 생성, 재요청 시 삭제"""
        self.client.post(self.url())
        self.assertEqual(
            TodoLike.objects.filter(todo=self.todo, user=self.user).count(), 1
        )

        self.client.post(self.url())
        self.assertEqual(
            TodoLike.objects.filter(todo=self.todo, user=self.user).count(), 0
        )


# =========================================================
# 북마크 토글 테스트
# POST /interaction/bookmark/<todo_id>/
# =========================================================
class TodoBookmarkToggleTests(InteractionTestBase):

    def url(self):
        return f"/interaction/bookmark/{self.todo.id}/"

    # ---------------------------------------------------------
    # 1. 비로그인 → 401
    # ---------------------------------------------------------
    def test_bookmark_requires_login(self):
        """비로그인 상태에서 북마크 요청 → 401"""
        self.client.logout()
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, 401)

    # ---------------------------------------------------------
    # 2. 처음 북마크 → bookmarked=True, bookmark_count=1
    # ---------------------------------------------------------
    def test_bookmark_first_time(self):
        """처음 북마크 → bookmarked=True, bookmark_count=1"""
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["bookmarked"])
        self.assertEqual(data["bookmark_count"], 1)

    # ---------------------------------------------------------
    # 3. 두 번 북마크 → 취소, bookmarked=False, bookmark_count=0
    # ---------------------------------------------------------
    def test_bookmark_toggle_cancels(self):
        """이미 북마크한 상태에서 다시 누르면 취소 → bookmarked=False, bookmark_count=0"""
        self.client.post(self.url())
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["bookmarked"])
        self.assertEqual(data["bookmark_count"], 0)

    # ---------------------------------------------------------
    # 4. 여러 사용자 북마크 → bookmark_count 정확히 집계
    # ---------------------------------------------------------
    def test_bookmark_count_multiple_users(self):
        """두 유저가 각각 북마크 → bookmark_count=2"""
        self.client.post(self.url())

        self.client.force_login(self.other_user)
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["bookmark_count"], 2)

    # ---------------------------------------------------------
    # 5. 존재하지 않는 Todo → 404
    # ---------------------------------------------------------
    def test_bookmark_nonexistent_todo_returns_404(self):
        """존재하지 않는 todo_id → 404"""
        res = self.client.post("/interaction/bookmark/99999/")
        self.assertEqual(res.status_code, 404)

    # ---------------------------------------------------------
    # 6. DB에 TodoBookmark 객체 생성/삭제 확인
    # ---------------------------------------------------------
    def test_bookmark_creates_and_deletes_db_record(self):
        """북마크 시 DB에 TodoBookmark 생성, 재요청 시 삭제"""
        self.client.post(self.url())
        self.assertEqual(
            TodoBookmark.objects.filter(todo=self.todo, user=self.user).count(), 1
        )

        self.client.post(self.url())
        self.assertEqual(
            TodoBookmark.objects.filter(todo=self.todo, user=self.user).count(), 0
        )


# =========================================================
# 댓글 등록 테스트
# POST /interaction/comment/<todo_id>/
# =========================================================
class TodoCommentCreateTests(InteractionTestBase):

    def url(self):
        return f"/interaction/comment/{self.todo.id}/"

    # ---------------------------------------------------------
    # 1. 비로그인 → 401
    # ---------------------------------------------------------
    def test_comment_requires_login(self):
        """비로그인 상태에서 댓글 작성 → 401"""
        self.client.logout()
        res = self.client.post(self.url(), {"content": "댓글"}, format="json")
        self.assertEqual(res.status_code, 401)

    # ---------------------------------------------------------
    # 2. 정상 댓글 등록 → 201 or 200, 응답 필드 확인
    # ---------------------------------------------------------
    def test_comment_create_success(self):
        """정상 댓글 등록 → 200, id/content/username/created_at 포함"""
        res = self.client.post(
            self.url(), {"content": "좋은 할일이네요"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["content"], "좋은 할일이네요")
        self.assertEqual(data["username"], "testuser")
        self.assertIn("id", data)
        self.assertIn("created_at", data)

    # ---------------------------------------------------------
    # 3. 빈 content → 400
    # ---------------------------------------------------------
    def test_comment_empty_content_returns_400(self):
        """content가 빈 문자열이면 400"""
        res = self.client.post(self.url(), {"content": ""}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("detail", res.json())

    # ---------------------------------------------------------
    # 4. content 공백만 → 400
    # ---------------------------------------------------------
    def test_comment_whitespace_only_returns_400(self):
        """content가 공백만 있으면 400"""
        res = self.client.post(self.url(), {"content": "   "}, format="json")
        self.assertEqual(res.status_code, 400)

    # ---------------------------------------------------------
    # 5. content 키 없음 → 400
    # ---------------------------------------------------------
    def test_comment_missing_content_returns_400(self):
        """content 키가 아예 없으면 400"""
        res = self.client.post(self.url(), {}, format="json")
        self.assertEqual(res.status_code, 400)

    # ---------------------------------------------------------
    # 6. 존재하지 않는 Todo → 404
    # ---------------------------------------------------------
    def test_comment_nonexistent_todo_returns_404(self):
        """존재하지 않는 todo_id → 404"""
        res = self.client.post(
            "/interaction/comment/99999/", {"content": "댓글"}, format="json"
        )
        self.assertEqual(res.status_code, 404)

    # ---------------------------------------------------------
    # 7. DB에 TodoComment 생성 확인
    # ---------------------------------------------------------
    def test_comment_creates_db_record(self):
        """댓글 등록 후 DB에 TodoComment 생성됨"""
        self.client.post(self.url(), {"content": "DB 확인"}, format="json")
        self.assertEqual(TodoComment.objects.filter(todo=self.todo).count(), 1)


# =========================================================
# 댓글 목록 조회 테스트
# GET /interaction/comment/<todo_id>/list/
# =========================================================
class TodoCommentListTests(InteractionTestBase):

    def url(self):
        return f"/interaction/comment/{self.todo.id}/list/"

    def setUp(self):
        super().setUp()
        # 댓글 3개 미리 생성
        for i in range(1, 4):
            TodoComment.objects.create(
                todo=self.todo,
                user=self.user,
                content=f"댓글 {i}",
            )

    # ---------------------------------------------------------
    # 1. 비로그인도 조회 가능 (AllowAny 아닌 경우엔 인증 필요하지 않음)
    # ---------------------------------------------------------
    def test_comment_list_returns_200(self):
        """댓글 목록 조회 → 200"""
        res = self.client.get(self.url())
        self.assertEqual(res.status_code, 200)

    # ---------------------------------------------------------
    # 2. 댓글 개수 확인
    # ---------------------------------------------------------
    def test_comment_list_count(self):
        """미리 생성한 댓글 3개가 모두 반환되는지 확인"""
        res = self.client.get(self.url())
        self.assertEqual(len(res.json()), 3)

    # ---------------------------------------------------------
    # 3. 최신순 정렬 확인
    # ---------------------------------------------------------
    def test_comment_list_ordered_by_latest(self):
        """최신 댓글이 먼저 오는지 확인 (댓글 3이 가장 앞)"""
        res = self.client.get(self.url())
        data = res.json()
        self.assertEqual(data[0]["content"], "댓글 3")

    # ---------------------------------------------------------
    # 4. 응답 필드 확인
    # ---------------------------------------------------------
    def test_comment_list_response_fields(self):
        """응답에 id, todo, user, username, content, created_at 포함"""
        res = self.client.get(self.url())
        item = res.json()[0]
        for field in ("id", "todo", "user", "username", "content", "created_at"):
            self.assertIn(field, item, msg=f"응답에 '{field}' 필드가 없습니다.")

    # ---------------------------------------------------------
    # 5. 댓글 없는 Todo → 빈 리스트
    # ---------------------------------------------------------
    def test_comment_list_empty(self):
        """댓글 없는 Todo 조회 → 빈 리스트"""
        empty_todo = Todo.objects.create(
            name="빈 할일",
            description="",
            complete=False,
            exp=0,
            user=self.user,
        )
        res = self.client.get(f"/interaction/comment/{empty_todo.id}/list/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), [])

    # ---------------------------------------------------------
    # 6. 존재하지 않는 Todo → 404
    # ---------------------------------------------------------
    def test_comment_list_nonexistent_todo_returns_404(self):
        """존재하지 않는 todo_id → 404"""
        res = self.client.get("/interaction/comment/99999/list/")
        self.assertEqual(res.status_code, 404)
