from rest_framework.pagination import CursorPagination, PageNumberPagination


class StandardPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ChannelMessageCursorPagination(CursorPagination):
    ordering = ("-created_at", "-id")
    page_size = 20
