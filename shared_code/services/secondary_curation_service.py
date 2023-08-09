import json
import logging
import random
from adlfs import AzureBlobFileSystem

from shared_code.storage.entity_structure import CuratedRecord
from shared_code.storage.tables import TableAdapter
from shared_code.services.base_curation_service import BaseService
from shared_code.storage.azure_file_system_adapter import AzureFileStorageAdapter


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


# noinspection PyBroadException
class SecondaryCurationService(BaseService):
	def __init__(self, table_name: str):
		super().__init__(table_name)
		self._table_adapter = TableAdapter()
		self._file_system: AzureBlobFileSystem = AzureFileStorageAdapter("data").get_file_storage()
		self.records_to_process = None
		self.total_records = 0

	def get_image_url(self, record_id: str, subreddit: str) -> str:
		client = self.get_table_client()
		try:
			entity = client.get_entity(partition_key=subreddit, row_key=record_id)
			try:
				thumbnail_path = self._file_system.url(entity['remote_path'])
			except Exception as e:
				logger.exception(e)
				thumbnail_path = "/data/nope/"
			return thumbnail_path
		finally:
			client.close()


	def update_record(self, record_id: str, subreddit: str, action: str) -> None:
		client = self.get_table_client()
		try:
			if action == "accept":
				logger.info(f"Accepting Secondary record: {record_id}")
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				stage_record = CuratedRecord(**entity)
				stage_record.accepted = True
				stage_record.curated = True
				client.upsert_entity(entity=stage_record.__dict__)
				return None
			else:
				logger.info(f"Rejecting Secondary record: {record_id}")
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				stage_record = CuratedRecord(**entity)
				stage_record.accepted = False
				stage_record.curated = True
				client.upsert_entity(entity=stage_record.__dict__)
				return None
		finally:
			client.close()





