from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from ..models import Todo


class TodoListView(ListView):  # 제너릭뷰
    model = Todo
    template_name = "todo/todo.html"  # 기본값: todo_list.html
    context_object_name = "todos"  # 기본값: object_list
    ordering = ["-created_at"]
    success_url = reverse_lazy("todo:list")


class TodoCreateView(CreateView):
    model = Todo
    # 이 뷰에서 사용할 모델 (Todo 테이블에 데이터 생성)

    fields = ["name", "description", "complete", "exp"]
    # HTML form에서 입력받을 모델 필드 정의

    template_name = "todo/create.html"
    # Todo 생성 화면에 사용할 템플릿 파일

    success_url = reverse_lazy("todo:list")
    # 생성이 성공하면 이동할 URL (todo 목록 페이지)


# 상세보기
class TodoDetailView(DetailView):
    model = Todo
    # 이 뷰에서 사용할 모델 지정 (Todo 테이블의 특정 데이터 조회)

    template_name = "todo/detail.html"
    # 조회한 데이터를 보여줄 HTML 템플릿 파일

    context_object_name = "todo"
    # 템플릿에서 사용할 변수 이름
    # 기본값 object 대신 todo라는 이름으로 전달됨


# 수정하기 화면(View)
class TodoUpdateView(UpdateView):
    model = Todo
    # 수정할 대상 모델 (Todo 테이블의 데이터를 수정)

    fields = ["name", "description", "complete", "exp"]
    # 수정할 때 사용할 모델 필드
    # 이 필드들을 기반으로 HTML form이 자동 생성됨

    template_name = "todo/update.html"
    # 수정 화면에 사용할 HTML 템플릿 파일

    context_object_name = "todo"
    # 템플릿에서 사용할 변수 이름
    # 기본값 object 대신 todo로 전달됨

    success_url = reverse_lazy("todo:list")
    # 수정이 성공하면 이동할 URL (todo 목록 페이지)
