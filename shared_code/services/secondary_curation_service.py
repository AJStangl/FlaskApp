import json

from adlfs import AzureBlobFileSystem

from shared_code.azure_storage.tables import TableAdapter
from shared_code.services.base_curation_service import BaseService
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter


# noinspection PyBroadException
class SecondaryCurationService(BaseService):
	def __init__(self, table_name: str):
		super().__init__(table_name)
		self._table_adapter = TableAdapter()
		self._file_system: AzureBlobFileSystem = AzureFileStorageAdapter("data").get_file_storage()

	def get_table_client(self):
		return self._table_adapter.get_table_client(self.table_name)

	def add_new_entry(self, primary_entity: dict) -> None:
		client = self.get_table_client()
		try:
			reddit_caption = primary_entity['subreddit'] + "," + primary_entity['title']
			entity = {
				'PartitionKey': primary_entity['subreddit'],
				'RowKey': primary_entity['id'],
				'id': primary_entity['id'],
				'subreddit': primary_entity['subreddit'],
				'author': primary_entity['author'],
				'title': primary_entity['title'],
				'caption': primary_entity['caption'],
				'hash': primary_entity['hash'],
				'permalink': primary_entity['permalink'],
				'original_url': primary_entity['original_url'],
				'image_name': primary_entity['image_name'],
				'path': primary_entity['path'],
				'model': primary_entity['model'],
				'exists': primary_entity['exists'],
				'curated': primary_entity['curated'],
				'accept': primary_entity['accept'],
				'tags': primary_entity['tags'],
				'azure_caption': '',
				'thumbnail_path': '',
				'thumbnail_exists': False,
				'thumbnail_curated': False,
				'thumbnail_accept': False,
				'additional_captions': '',
				'smart_caption': '',
				'best_caption': '',
				'reddit_caption': reddit_caption,
				'pil_crop_accept': False,
				'azure_crop_accept': False,
				'smart_crop_accept': False,
				'pil_thumbnail_path': '',
				'azure_thumbnail_path': '',
			}
			client.upsert_entity(entity)
			return None
		finally:
			client.close()

	def get_num_remaining_records(self) -> int:
		client = self.get_table_client()
		try:
			old_query = 'thumbnail_curated eq false'
			query = "(pil_crop_accept eq false and azure_crop_accept eq false and smart_crop_accept eq false and thumbnail_curated eq true and thumbnail_accept eq true) or (thumbnail_curated eq false and thumbnail_accept eq false)"
			return len(list(client.query_entities(query, select=["id"])))
		finally:
			client.close()

	def get_image_url(self, record_id: str, subreddit: str) -> str:
		client = self.get_table_client()
		try:
			entity = client.get_entity(partition_key=subreddit, row_key=record_id)
			try:
				thumbnail_path = self._file_system.url(entity['thumbnail_path'])
			except Exception as e:
				print(e)
				thumbnail_path = "/data/nope/"
			try:
				azure_thumbnail = self._file_system.url(entity['azure_thumbnail_path'])
			except Exception as e:
				print(e)
				azure_thumbnail = "/data/nope/"
			try:
				pil_thumbnail = self._file_system.url(entity['pil_thumbnail_path'])
			except Exception as e:
				print(e)
				pil_thumbnail = "/data/nope/"
			return thumbnail_path, azure_thumbnail, pil_thumbnail
		finally:
			client.close()


	def update_record(self,
					  record_id: str,
					  subreddit: str,
					  action: str,
					  reddit_caption: str,
					  smart_caption: str,
					  azure_caption: str,
					  best_caption: str,
					  pil_crop_accept: bool,
					  azure_crop_accept: bool,
					  smart_crop_accept: bool,
					  additional_captions: list[str],
					  relevant_tags: list[str]) -> None:

		client = self.get_table_client()
		try:
			if action == 'accept':
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				entity['thumbnail_curated'] = True
				entity['thumbnail_accept'] = True
				entity['azure_caption'] = azure_caption
				entity['smart_caption'] = smart_caption
				entity['best_caption'] = best_caption
				entity['reddit_caption'] = reddit_caption
				entity['pil_crop_accept'] = pil_crop_accept
				entity['azure_crop_accept'] = azure_crop_accept
				entity['smart_crop_accept'] = smart_crop_accept
				entity['additional_captions'] = json.dumps(additional_captions)
				entity['tags'] = json.dumps(relevant_tags)
				client.update_entity(entity=entity)
				return None
			else:
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				entity['thumbnail_curated'] = True
				entity['thumbnail_accept'] = False
				entity['azure_caption'] = azure_caption
				entity['smart_caption'] = smart_caption
				entity['best_caption'] = best_caption
				entity['reddit_caption'] = reddit_caption
				entity['pil_crop_accept'] = pil_crop_accept
				entity['azure_crop_accept'] = azure_crop_accept
				entity['smart_crop_accept'] = smart_crop_accept
				entity['additional_captions'] = json.dumps(additional_captions)
				entity['tags'] = json.dumps(relevant_tags)
				print(json.dumps(entity, indent=4))
				client.update_entity(entity=entity)
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

	def list_subs(self) -> list:
		client = self.get_table_client()
		try:
			entity = client.list_entities(select='subreddit')
			return list(set(entity))
		finally:
			client.close()

	def get_next_record(self):
		client = self.get_table_client()
		try:
			is_curated = 'thumbnail_curated eq false'
			is_accepted = 'thumbnail_accept eq false'
			is_pil_accepted = 'pil_crop_accept eq false'
			is_azure_accepted = 'azure_crop_accept eq false'
			is_smart_accepted = 'smart_crop_accept eq false'
			query = "(pil_crop_accept eq false and azure_crop_accept eq false and smart_crop_accept eq false and thumbnail_curated eq true and thumbnail_accept eq true) or (thumbnail_curated eq false and thumbnail_accept eq false)"
			entity = client.query_entities(query)
			return next(entity)
		finally:
			client.close()

	def get_dense_captions(self, name):
		captions_table = TableAdapter().get_table_client('denseCaptions')
		dense_captions = list(captions_table.query_entities(f"PartitionKey eq '{name}'"))
		return dense_captions

	def get_relevant_tags(self, name):
		relevant_tags = TableAdapter().get_table_client('relevantTags')
		tags = list(relevant_tags.query_entities(f"PartitionKey eq '{name}'"))
		return tags
