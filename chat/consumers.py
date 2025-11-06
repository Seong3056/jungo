import json
import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from .models import ChatRoom, Message

# 로그 설정 (콘솔에 출력)
logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.group_name = f'chat_{self.room_id}'
        self.room = await self.get_room(self.room_id)

        user = self.scope['user']
        if not user.is_authenticated or not self.room or not await self.user_in_room(user):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        클라이언트로부터 메시지를 수신할 때 호출됨.
        JSON이 아닌 데이터, 깨진 인코딩, 빈 문자열 등을 모두 안전하게 처리함.
        """
        if not text_data and not bytes_data:
            return

        # ✅ 1. bytes_data로 들어올 경우 UTF-8로 안전하게 디코딩
        if bytes_data:
            try:
                text_data = bytes_data.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"[ChatConsumer] bytes_data decode 실패: {e}")
                return

        # ✅ 2. 혹시 text_data가 bytes 타입일 수도 있음
        if isinstance(text_data, bytes):
            try:
                text_data = text_data.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"[ChatConsumer] text_data decode 실패: {e}")
                return

        # ✅ 3. JSON 파싱
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError as e:
            logger.warning(f"[ChatConsumer] JSON decode 실패: {e}")
            return

        message = (payload.get('message') or '').strip()
        if not message:
            return

        # ✅ 4. DB 저장 및 브로드캐스트
        user = self.scope['user']
        message_payload = await self.create_message(user, message)
        await self.channel_layer.group_send(
            self.group_name,
            {'type': 'chat.message', **message_payload},
        )

    async def chat_message(self, event):
        """
        그룹 내 다른 클라이언트들에게 메시지를 전송
        """
        await self.send(text_data=json.dumps({
            'type': 'chat.message',
            'message': event['content'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def get_room(self, room_id):
        try:
            return ChatRoom.objects.select_related('buyer', 'seller').get(id=room_id)
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def user_in_room(self, user):
        return user == self.room.buyer or user == self.room.seller

    @database_sync_to_async
    def create_message(self, user, content):
        message = Message.objects.create(
            room=self.room,
            sender=user,
            content=content,
        )
        timestamp = timezone.localtime(message.timestamp).strftime('%Y-%m-%d %H:%M')
        return {
            'content': message.content,
            'sender': user.username,
            'sender_id': user.id,
            'timestamp': timestamp,
        }
