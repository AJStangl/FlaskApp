import logging

from adlfs import AzureBlobFileSystem
from shared_code.azure_storage.tables import TableAdapter
from shared_code.schemas.table_schema import TableFactory
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class TrainingService:
	def __init__(self):
		self.table_adapter: TableAdapter = TableAdapter()
		self.file_system: AzureBlobFileSystem = AzureFileStorageAdapter("data").get_file_storage()

	def get_table_client(self, table_name: str):
		return self.table_adapter.get_table_client(table_name)

	def get_secondary_my_id(self, subreddit, submission_id):
		table_client = self.get_table_client("curationSecondary")
		try:
			entity = table_client.get_entity(partition_key=subreddit, row_key=submission_id)
			return entity
		except Exception as e:
			logger.exception(e)
			return None
		finally:
			table_client.close()

	def upsert_data_record(self, subreddit, submission_id):
		training_table_client = self.table_adapter.get_table_client("training")
		try:
			secondary_entry: dict = self.get_secondary_my_id(subreddit, submission_id)

			# For azure
			azure_thumbnail_path = secondary_entry.get("azure_thumbnail_path")
			azure_caption = secondary_entry.get("azure_caption")
			azure: dict = self.make_entity(caption=azure_caption, path=azure_thumbnail_path, _type="azure",
										   entity=secondary_entry)
			if azure is not None:
				if azure['exists']:
					training_table_client.upsert_entity(azure)

			# For Pil
			pil_caption = secondary_entry.get("pil_caption")
			pil_thumbnail_path = secondary_entry.get("pil_thumbnail_path")
			pil: dict = self.make_entity(caption=pil_caption, path=pil_thumbnail_path, _type="pil",
										 entity=secondary_entry)
			if pil is not None:
				if pil['exists']:
					training_table_client.upsert_entity(pil)

			# For Smart
			smart_path = secondary_entry.get("thumbnail_path")
			smart_caption = secondary_entry.get("smart_caption")
			smart: dict = self.make_entity(caption=smart_caption, path=smart_path, _type="smart",
										   entity=secondary_entry)
			if smart is not None:
				if smart['exists']:
					training_table_client.upsert_entity(smart)
		finally:
			training_table_client.close()

	def create_curation_entity(self, subreddit: str, record_id: str, title: str, caption: str, path: str, input_type: str) -> dict:
		return {
			"PartitionKey": subreddit,
			"RowKey": f"{record_id}-{input_type}",
			"GPT": f"<|startoftext|><|model|>{subreddit}<|title|>{title}<|caption|>{title}, {caption}, in the style of r/{subreddit}<|endoftext|>",
			"subreddit": subreddit,
			"title": title,
			"format_caption": f"{title}, {caption}, is the style of r/{subreddit}",
			"path": path,
			"type": input_type,
		}

	def make_entity(self, caption: str, path: str, _type: str, entity: dict):
		try:
			exists = self.file_system.exists(path)
			subreddit = entity.get("PartitionKey")
			submission_id = entity.get("RowKey")
			title = entity.get("title")
			return TableFactory.create_tertiary_entity(subreddit=subreddit, submission_id=submission_id, _type=_type,
													   title=title, caption=caption, path=path, exists=exists,
													   training_count=0)
		except Exception as e:
			logger.exception(e)
			return None
