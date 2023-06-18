import json

from adlfs import AzureBlobFileSystem

from shared_code.azure_storage.tables import TableAdapter
from shared_code.services.base_curation_service import BaseService
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter





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
				'additional_captions': ''
			}
			client.upsert_entity(entity)
			return None
		finally:
			client.close()

	def get_num_remaining_records(self) -> int:
		client = self.get_table_client()
		try:
			return len(list(client.query_entities('thumbnail_curated eq false')))
		finally:
			client.close()

	def get_image_url(self, record_id: str, subreddit: str) -> str:
		client = self.get_table_client()
		try:
			entity = client.get_entity(partition_key=subreddit, row_key=record_id)
			try:
				thumbnail_path = self._file_system.url(entity['thumbnail_path'])
			except:
				thumbnail_path = "/data/nope/"
			try:
				original_path = self._file_system.url(entity['path'])
			except:
				original_path = "/data/nope/"
			try:
				alternate_path = self._file_system.url(entity['azure_thumbnail_path'])
			except:
				alternate_path = "/data/nope/"
			return thumbnail_path, original_path, alternate_path
		finally:
			client.close()

	def update_record(self, record_id: str, subreddit: str, action: str, caption: str, additional_captions: list[str], relevant_tags: list[str]) -> None:
		client = self.get_table_client()
		try:
			if action == 'accept':
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				entity['thumbnail_curated'] = True
				entity['thumbnail_accept'] = True
				entity['azure_caption'] = caption
				entity['additional_captions'] = json.dumps(additional_captions)
				entity['tags'] = json.dumps(relevant_tags)
				client.update_entity(entity=entity)
				return None
			else:
				entity = client.get_entity(partition_key=subreddit, row_key=record_id)
				entity['thumbnail_curated'] = True
				entity['thumbnail_accept'] = False
				entity['azure_caption'] = caption
				entity['additional_captions'] = json.dumps(additional_captions)
				entity['tags'] = json.dumps(relevant_tags)
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
			# is_sexy = "subreddit eq 'selfies' or subreddit eq 'Amicute' or subreddit eq 'amihot' or subreddit eq 'AmIhotAF' or subreddit eq 'HotGirlNextDoor' or subreddit eq 'sfwpetite' or subreddit eq 'cougars_and_milfs_sfw' or subreddit eq 'SFWRedheads' or subreddit eq 'SFWNextDoorGirls' or subreddit eq 'SunDressesGoneWild' or subreddit eq 'ShinyDresses' or subreddit eq 'SlitDresses' or subreddit eq 'CollaredDresses' or subreddit eq 'DressesPorn' or subreddit eq 'WomenInLongDresses' or subreddit eq 'Dresses' or subreddit eq 'realasians' or subreddit eq 'KoreanHotties' or subreddit eq 'prettyasiangirls' or subreddit eq 'AsianOfficeLady' or subreddit eq 'AsianInvasion' or subreddit eq 'AesPleasingAsianGirls' or subreddit eq 'sexygirls' or subreddit eq 'PrettyGirls' or subreddit eq 'gentlemanboners' or subreddit eq 'hotofficegirls' or subreddit eq 'tightdresses' or subreddit eq 'DLAH' or subreddit eq 'TrueFMK'"
			query = f"{is_curated} and {is_accepted}"
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
