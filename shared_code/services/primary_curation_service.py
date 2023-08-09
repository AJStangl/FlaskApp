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