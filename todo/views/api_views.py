# ---------------------------------------------------------
# models에서 좋아요 / 북마크 / 댓글 모델 import
# ---------------------------------------------------------
# .. 는 상위 디렉토리를 의미합니다.
# 즉 todo 앱의 models.py 에서 정의된 모델을 가져옵니다.
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from ..models import Todo
from ..serializers import TodoSerializer
from ..pagination import CustomPageNumberPagination
from interaction.models import TodoLike, TodoBookmark, TodoComment


# ---------------------------------------------------------
# DRF action / permission import
# ---------------------------------------------------------
# action
# → ViewSet 안에서 "추가 API"를 만들 때 사용하는 데코레이터
# → 기본 CRUD 외에 커스텀 API를 만들 수 있음
#
# permission
# → API 접근 권한을 제어
# → 로그인 필요 / 누구나 가능 등을 설정
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated


# ---------------------------------------------------------
# 기존 APIView CRUD 클래스 (현재 사용하지 않음)
# ---------------------------------------------------------
# 예전에는 아래처럼 APIView를 사용해서
# List / Create / Retrieve / Update / Delete
# 각각 클래스를 따로 만들어야 했습니다.
#
# 하지만 ViewSet을 사용하면
# CRUD가 자동 생성되기 때문에
# 현재는 사용하지 않는 구조입니다.
# ---------------------------------------------------------
class TodoListAPI(APIView):
    pass


class TodoCreateAPI(APIView):
    pass


class TodoRetrieveAPI(APIView):
    pass


class TodoUpdateAPI(APIView):
    pass


class TodoDeleteAPI(APIView):
    pass


# ---------------------------------------------------------
# 핵심 ViewSet
# ---------------------------------------------------------
# ModelViewSet
#
# 아래 CRUD가 자동 생성됩니다.
#
# GET    /todos/          → list
# POST   /todos/          → create
# GET    /todos/{id}/     → retrieve
# PUT    /todos/{id}/     → update
# DELETE /todos/{id}/     → destroy
#
# 즉 CRUD API를 자동으로 만들어주는 클래스입니다.
# ---------------------------------------------------------
class TodoViewSet(viewsets.ModelViewSet):

    # -----------------------------------------------------
    # serializer 지정
    # -----------------------------------------------------
    serializer_class = TodoSerializer

    # -----------------------------------------------------
    # 기본 permission
    # -----------------------------------------------------
    # 로그인한 사용자만 접근 가능
    permission_classes = [IsAuthenticated]

    # -----------------------------------------------------
    # 페이지네이션
    # -----------------------------------------------------
    pagination_class = CustomPageNumberPagination

    # -----------------------------------------------------
    # queryset
    # -----------------------------------------------------
    # 공개 Todo 또는 내 Todo만 조회
    def get_queryset(self):
        user = self.request.user
        return Todo.objects.filter(Q(is_public=True) | Q(user=user)).order_by(
            "-created_at"
        )

    # -----------------------------------------------------
    # list API 커스터마이징
    # -----------------------------------------------------
    # 기본 list 응답
    #
    # [
    #   {...},
    #   {...}
    # ]
    #
    # 하지만 JS에서 사용하기 편하도록
    # 아래처럼 응답 구조를 변경했습니다.
    #
    # {
    #   data: [...],
    #   current_page: 1,
    #   page_count: 5,
    #   next: true,
    #   previous: false
    # }
    # -----------------------------------------------------
    def list(self, request, *args, **kwargs):

        # queryset 필터링
        qs = self.filter_queryset(self.get_queryset())

        # pagination 처리
        page = self.paginate_queryset(qs)

        # ---------------------------------------------
        # pagination이 적용된 경우
        # ---------------------------------------------
        if page is not None:

            # serializer 실행
            serializer = self.get_serializer(
                page,
                many=True,
                context={"request": request},
            )

            return Response(
                {
                    "data": serializer.data,
                    # 현재 페이지에 포함된 데이터 개수
                    "page_size": len(serializer.data),
                    # 전체 데이터 개수
                    "total_count": self.paginator.page.paginator.count,
                    # 현재 페이지
                    "current_page": self.paginator.page.number,
                    # 전체 페이지 수
                    "page_count": self.paginator.page.paginator.num_pages,
                    # 다음 페이지 URL (없으면 None)
                    "next": self.paginator.get_next_link(),
                    # 이전 페이지 URL (없으면 None)
                    "previous": self.paginator.get_previous_link(),
                }
            )

        # ---------------------------------------------
        # pagination이 없는 경우
        # ---------------------------------------------
        serializer = self.get_serializer(
            qs,
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "data": serializer.data,
                "page_size": len(serializer.data),
                "total_count": len(serializer.data),
                "current_page": 1,
                "page_count": 1,
                "next": None,
                "previous": None,
            }
        )

    # -----------------------------------------------------
    # 좋아요 토글 API
    # -----------------------------------------------------
    # URL
    #
    # POST /todo/viewsets/view/<id>/like/
    #
    # detail=True
    # → 특정 Todo 대상 API
    #
    # permission_classes=[IsAuthenticated]
    # → 로그인한 사용자만 가능
    #
    # get_or_create 패턴
    # → 없으면 생성
    # → 있으면 삭제
    #
    # 즉
    # 좋아요 ON / OFF 토글 기능
    # -----------------------------------------------------
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):

        # 현재 Todo 가져오기
        todo = self.get_object()

        # 로그인한 사용자
        user = request.user

        # 좋아요 존재 확인
        obj, created = TodoLike.objects.get_or_create(todo=todo, user=user)

        # 새로 생성된 경우 → 좋아요 ON
        if created:
            liked = True

        # 이미 존재 → 삭제 → 좋아요 OFF
        else:
            obj.delete()
            liked = False

        # 전체 좋아요 개수 계산
        like_count = TodoLike.objects.filter(todo=todo).count()

        # 응답
        return Response({"liked": liked, "like_count": like_count})

    # -----------------------------------------------------
    # 북마크 토글 API
    # -----------------------------------------------------
    # URL
    #
    # POST /todo/viewsets/view/<id>/bookmark/
    #
    # 좋아요와 동일한 구조
    # -----------------------------------------------------
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def bookmark(self, request, pk=None):

        # 현재 Todo
        todo = self.get_object()

        # 로그인 사용자
        user = request.user

        # 북마크 생성 또는 조회
        obj, created = TodoBookmark.objects.get_or_create(todo=todo, user=user)

        # 북마크 ON
        if created:
            bookmarked = True

        # 북마크 OFF
        else:
            obj.delete()
            bookmarked = False

        # 전체 북마크 수
        bookmark_count = TodoBookmark.objects.filter(todo=todo).count()

        return Response({"bookmarked": bookmarked, "bookmark_count": bookmark_count})

    # -----------------------------------------------------
    # 댓글 등록 API
    # -----------------------------------------------------
    # URL
    #
    # POST /todo/viewsets/view/<id>/comments/
    #
    # request.data
    # → 클라이언트에서 보낸 JSON 데이터
    #
    # {
    #   "content": "댓글 내용"
    # }
    # -----------------------------------------------------
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def comments(self, request, pk=None):

        # Todo 가져오기
        todo = self.get_object()

        # 로그인 사용자
        user = request.user

        # 댓글 내용 가져오기
        content = (request.data.get("content") or "").strip()

        # 댓글 내용 검증
        if not content:
            return Response({"detail": "content is required"}, status=400)

        # 댓글 생성
        TodoComment.objects.create(todo=todo, user=user, content=content)

        # 댓글 개수 계산
        comment_count = TodoComment.objects.filter(todo=todo).count()

        return Response({"comment_count": comment_count})

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
