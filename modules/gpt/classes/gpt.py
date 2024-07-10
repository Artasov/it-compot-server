from enum import Enum

import aiohttp


class Model(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4O = "gpt-4o"  # Example, replace with actual model name if different


class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class Chat:
    def __init__(self, chat_id: str):
        self.chat_id = chat_id
        self.messages: list[Message] = []

    def add_message(self, role: str, content: str):
        self.messages.append(Message(role, content))

    def get_messages(self) -> list[dict[str, str]]:
        return [{'role': message.role, 'content': message.content} for message in self.messages]


class GPTAssistant:
    def __init__(self, token: str, proxy: str | None = None, model: Model = Model.GPT_3_5_TURBO):
        self.token = token
        self.proxy = proxy
        self.model = model
        self.chats: dict[str, Chat] = {}

    async def _send_request(
            self, url: str,
            method: str = "POST",
            headers: dict[str, str] = None,
            json: dict = None,
            data: dict = None
    ) -> dict:
        async with aiohttp.ClientSession() as session:
            if self.proxy:
                conn = aiohttp.ProxyConnector.from_url(self.proxy)
            else:
                conn = aiohttp.TCPConnector()

            async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    data=data,
                    connector=conn
            ) as response:
                response_data = await response.json()
                return response_data

    async def start_new_chat(self, chat_id: str) -> Chat:
        chat = Chat(chat_id)
        chat.add_message("system", "You are a helpful assistant.")
        self.chats[chat_id] = chat
        return chat

    async def send_message(self, chat: Chat, content: str) -> str:
        chat.add_message('user', content)
        messages = chat.get_messages()

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        json_data = {
            "model": self.model.value,
            "messages": messages
        }

        response_data = await self._send_request(
            url="https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data
        )

        reply = response_data['choices'][0]['message']['content']
        chat.add_message('assistant', reply)
        return reply

    async def get_chat_history(self, chat_id: str) -> list[dict[str, str]]:
        if chat_id in self.chats:
            return self.chats[chat_id].get_messages()
        else:
            return []
