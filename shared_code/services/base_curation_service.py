import abc
import json
import logging
import random
from adlfs import AzureBlobFileSystem
from shared_code.storage.tables import TableAdapter

from shared_code.storage.azure_file_system_adapter import AzureFileStorageAdapter

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class BaseService(abc.ABC):
	def __init__(self, table_name: str):
		self.table_name = table_name
		self._table_adapter = TableAdapter()
		self._file_system: AzureBlobFileSystem = AzureFileStorageAdapter("data").get_file_storage()
		self.records_to_process = None
		self.total_records = 0

	def get_table_client(self):
		return self._table_adapter.get_table_client(self.table_name)

	def get_remaining_records(self):
		client = self.get_table_client()
		try:
			records = list(client.query_entities(query_filter="curated eq false"))
			random.shuffle(records)
			if len(records) == 0:
				self.records_to_process = enumerate([])
				self.total_records = 0
				return
			self.records_to_process = enumerate(records)
			self.total_records = len(records)
		finally:
			client.close()

	def reset_records(self):
		self.get_remaining_records()

	def get_next_record(self):
		if self.records_to_process is None:
			self.get_remaining_records()
			return next(self.records_to_process)
		else:
			self.total_records = self.total_records - 1
			return next(self.records_to_process)

	def get_record_by_id(self, subreddit: str, record_id: str) -> dict:
		client = self.get_table_client()
		try:
			entity = client.get_entity(partition_key=subreddit, row_key=record_id)
			return entity
		finally:
			client.close()
