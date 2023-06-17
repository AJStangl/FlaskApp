from shared_code.azure_storage.tables import TableAdapter
from shared_code.schemas.table_schema import PrimaryCurationEntity
from shared_code.services.base_curation_service import BaseService


class PrimaryCurationService(BaseService):
	def __init__(self, table_name: str):
		super().__init__(table_name)
		self._table_adapter = TableAdapter()

	def get_table_client(self):
		return self._table_adapter.get_table_client(self.table_name)

	def get_num_remaining_records(self) -> int:
		client = self.get_table_client()
		try:
			return len(list(client.query_entities("curated eq false")))
		finally:
			client.close()

	def get_image_url(self, record_id: str, subreddit: str) -> str:
		client = self.get_table_client()
		try:
			entity: PrimaryCurationEntity = client.get_entity(partition_key=subreddit, row_key=record_id)
			return "https://ajdevreddit.blob.core.windows.net/" + entity['path']
		finally:
			client.close()

	def update_record(self, record_id: str, subreddit: str, action: str, caption: str, additional_captions: list[str], relevant_tags: list[str]) -> None:
		client = self.get_table_client()
		try:
			if action == "accept":
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				entity['caption'] = caption
				entity['accept'] = True
				entity['curated'] = True
				client.update_entity(entity=entity)
				return None
			else:
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				entity['accept'] = False
				entity['curated'] = True
				client.update_entity(entity=entity)
				return None
		finally:
			client.close()

	def get_record_by_id(self, subreddit: str, record_id: str) -> dict:
		client = self.get_table_client()
		try:
			entity: PrimaryCurationEntity = client.get_entity(partition_key=subreddit, row_key=record_id)
			return entity
		finally:
			client.close()

	def list_subs(self) -> list:
		client = self.get_table_client()
		try:
			entity = client.list_entities(select="subreddit")
			return list(set(entity))
		finally:
			client.close()

	def get_next_record(self):
		client = self.get_table_client()
		try:
			entity = client.query_entities("curated eq false")
			return next(entity)
		finally:
			client.close()