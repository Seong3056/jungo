from django.apps import AppConfig
class ChatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chat"
    def ready(self):
        # 알림(Notifications) 관련 시그널 등록 제거
        pass
