from shared_code.storage.entity_structure import StageRecord
from shared_code.storage.tables import TableAdapter
from shared_code.services.base_curation_service import BaseService
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class PrimaryCurationService(BaseService):
	def __init__(self, table_name: str):
		super().__init__(table_name)
		self._table_adapter = TableAdapter()

	def get_table_client(self):
		return self._table_adapter.get_table_client(self.table_name)

	def get_num_remaining_records(self) -> int:
		client = self.get_table_client()
		try:
			return len(list(client.query_entities("curated eq false", select=['id'])))
		finally:
			client.close()

	def get_image_url(self, record_id: str, subreddit: str) -> str:
		client = self.get_table_client()
		try:
			entity = client.get_entity(partition_key=subreddit, row_key=record_id)
			return "https://ajdevreddit.blob.core.windows.net" + entity['remote_path']
		finally:
			client.close()

	def update_record(self, record_id: str, subreddit: str, action: str) -> None:
		client = self.get_table_client()
		try:
			if action == "accept":
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				stage_record = StageRecord(**entity)
				stage_record.accepted = True
				stage_record.curated = True
				client.upsert_entity(entity=stage_record.__dict__)
				return None
			else:
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				stage_record = StageRecord(**entity)
				stage_record.accepted = False
				stage_record.curated = True
				client.upsert_entity(entity=stage_record.__dict__)
				return None
		finally:
			client.close()

	def get_record_by_id(self, subreddit: str, record_id: str) -> dict:
		client = self.get_table_client()
		try:
			entity = client.get_entity(partition_key=subreddit, row_key=record_id)
			return entity
		finally:
			client.close()

	def get_next_record(self):
		client = self.get_table_client()
		try:
			entity = client.query_entities(query_filter="curated eq false")
			return next(entity)
		finally:
			client.close()
