import json

from shared_code.azure_storage.tables import TableAdapter
from shared_code.services.base_curation_service import BaseService


class SecondaryCurationService(BaseService):
	def __init__(self, table_name: str):
		super().__init__(table_name)
		self._table_adapter = TableAdapter()

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
			return 'https://ajdevreddit.blob.core.windows.net/' + entity['thumbnail_path']
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
			is_sexy = "subreddit' in ('selfies', 'Amicute', 'amihot', 'AmIhotAF', 'HotGirlNextDoor', 'sfwpetite', 'cougars_and_milfs_sfw', 'SFWRedheads', 'SFWNextDoorGirls', 'SunDressesGoneWild', 'ShinyDresses', 'SlitDresses', 'CollaredDresses', 'DressesPorn', 'WomenInLongDresses', 'Dresses', 'realasians', 'KoreanHotties', 'prettyasiangirls', 'AsianOfficeLady', 'AsianInvasion', 'AesPleasingAsianGirls', 'sexygirls', 'PrettyGirls', 'gentlemanboners' 'hotofficegirls', 'tightdresses', 'DLAH', 'TrueFMK')"
			query = f"{is_curated} and {is_accepted} and {is_sexy}"
			entity = client.query_entities(query)
			return next(entity)
		finally:
			client.close()

	def get_dense_captions(self, name):
		captions_table = TableAdapter().get_table_client('denseCaptions')
		dense_captions = list(captions_table.query_entities('PartitionKey eq ' + name))
		return dense_captions

	def get_relevant_tags(self, name):
		relevant_tags = TableAdapter().get_table_client('relevantTags')
		tags = list(relevant_tags.query_entities('PartitionKey eq ' + name))
		return tags
