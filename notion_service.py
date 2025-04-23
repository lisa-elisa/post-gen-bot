import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
_client = Client(auth=os.getenv('NOTION_TOKEN'))
DB_ID = os.getenv('NOTION_DB_ID')

def create_page():
    """Создаёт пустую строку в базе и возвращает её ID."""
    page = _client.pages.create(
        parent={'database_id': DB_ID},
        properties={
            'Идея': {'rich_text': []},
            'Черновик': {'rich_text': []},
            'Финал': {'rich_text': []},
            'Напоминание': {'date': None}
        }
    )
    return page['id']

def update_property(page_id: str, prop: str, content):
    """Записывает content в свойство prop указанной страницы."""
    payload = {}
    if prop == 'Напоминание':
        payload[prop] = {'date': {'start': content}}
    else:
        payload[prop] = {'rich_text': [{'text': {'content': content}}]}
    return _client.pages.update(page_id=page_id, properties=payload)
