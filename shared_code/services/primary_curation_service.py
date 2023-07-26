from shared_code.storage.entity_structure import StageRecord
from shared_code.storage.tables import TableAdapter
from shared_code.services.base_curation_service import BaseService
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class PrimaryCurationService(BaseService):
	def __init__(self, table_name: str):
		super().__init__(table_name)
		self._table_adapter = TableAdapter()
		self.records_to_process = None
		self.total_records = 0

	def get_table_client(self):
		return self._table_adapter.get_table_client(self.table_name)

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
				logger.info(f"Accepting record: {record_id}")
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				stage_record = StageRecord(**entity)
				stage_record.accepted = True
				stage_record.curated = True
				client.upsert_entity(entity=stage_record.__dict__)
				return None
			else:
				logger.info(f"Rejecting record: {record_id}")
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
		if self.records_to_process is None:
			self.get_remaining_records()
			return next(self.records_to_process)
		else:
			self.total_records = self.total_records - 1
			return next(self.records_to_process)

	def get_remaining_records(self):
		client = self.get_table_client()
		try:
			records = list(client.query_entities(query_filter="curated eq false"))
			random.shuffle(records)
			self.records_to_process = enumerate(records)
			self.total_records = len(records)
		finally:
			client.close()

	def reset_records(self):
		self.get_remaining_records()