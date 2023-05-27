import sys
from typing import Optional

import pandas
from adlfs import AzureBlobFileSystem

from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.services.base_curation_service import BaseService

from shared_code.schemas.pyarrow_schema import secondary_curation_schema


class SecondaryCurationService(BaseService):
	def __init__(self):
		super().__init__('data/parquet/thumbnail_curation.parquet')
		self.file_storage: AzureBlobFileSystem = self._get_file_storage()
		self.data_frame: pandas.DataFrame = self._get_data_frame()
		self.records_to_process_iterator: iter = iter(self.get_records_to_process())
		self.current_record: Optional[dict] = None
		sys.setrecursionlimit(100000000)

	def get_num_remaining_records(self) -> int:
		not_thing = self.data_frame.loc[self.data_frame['thumbnail_curated'] == False]
		return len(not_thing)

	def reset(self):
		self.file_storage = self._get_file_storage()
		self.data_frame = self._get_data_frame()
		self.records_to_process_iterator = iter(self.get_records_to_process())
		self.current_record = None

	def get_next_record(self) -> dict:
		while True:
			if self.current_record is None:
				self.current_record = next(self.records_to_process_iterator)
				if self._should_curate(self.current_record):
					return self.current_record
				else:
					continue
			else:
				if self._should_curate(self.current_record):
					return self.current_record
				else:
					self.current_record = next(self.records_to_process_iterator)
					continue

	def _should_curate(self, record: dict) -> bool:
		is_curated = record['thumbnail_curated']
		is_accepted = record['thumbnail_accept']
		return not is_curated and not is_accepted

	def get_image_url(self, record: dict) -> str:
		return "https://ajdevreddit.blob.core.windows.net/" + record['thumbnail_path']

	def update_record(self, record_id: str, action: str, caption: str) -> None:
		record = self.current_record
		if record['id'] != record_id:
			raise Exception("Record Ids Do Not Match")
		if action == "accept":
			record['thumbnail_curated'] = True
			record['thumbnail_accept'] = True
		else:
			record['thumbnail_curated'] = True
			record['thumbnail_accept'] = False

		record['azure_caption'] = caption

		temp: pandas.DataFrame = self.data_frame.copy(deep=True)

		temp.loc[temp['id'] == record['id'], 'thumbnail_accept'] = record['thumbnail_accept']
		temp.loc[temp['id'] == record['id'], 'thumbnail_curated'] = record['thumbnail_curated']
		temp.loc[temp['id'] == record['id'], 'azure_caption'] = record['azure_caption']

		temp.to_parquet(self.parquet_path, engine="pyarrow", filesystem=self.file_storage, schema=secondary_curation_schema)
		self.data_frame: pandas.DataFrame = temp
		return None

	def update_record_tag(self, record: dict) -> None:
		temp: pandas.DataFrame = self.data_frame.copy(deep=True)
		temp.loc[temp['id'] == record['id'], 'tags']: [] = record['tags']
		temp.to_parquet(self.parquet_path, engine="pyarrow", filesystem=self.file_storage, schema=secondary_curation_schema)
		self.data_frame: pandas.DataFrame = temp
		return None

	def get_record_by_id(self, record_id) -> dict:
		return self.data_frame.loc[self.data_frame['id'] == record_id].to_dict(orient='records')[0]

	def list_subs(self) -> list:
		return self.data_frame['subreddit'].unique().tolist()

	def filter_subs(self, sub) -> None:
		temp = self.data_frame.loc[self.data_frame['subreddit'] == sub].to_dict(orient='records')
		self.data_frame = pandas.DataFrame(data=temp)
		return

	def get_records_to_process(self) -> list[dict]:
		return self.data_frame.to_dict(orient='records')

	def _get_data_frame(self) -> pandas.DataFrame:
		data_frame = pandas.read_parquet(self.parquet_path, filesystem=self.file_storage,
										 engine='pyarrow', schema=secondary_curation_schema)
		return data_frame

	def _get_file_storage(self) -> AzureBlobFileSystem:
		return AzureFileStorageAdapter("data").get_file_storage()
