import sys
from typing import Optional

import pandas

from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.services.pyarrow_schema import curation_schema, tagging_schema


class SecondLayerCurationService:
	def __init__(self):
		self.file_storage: AzureFileStorageAdapter = self._get_file_storage()
		self.data_frame: pandas.DataFrame = self._get_data_frame()
		self.records_to_process_iterator: iter = iter(self.get_records_to_process())
		self.current_record: Optional[dict] = None
		sys.setrecursionlimit(100000000)

	def get_image_url(self, record: dict) -> str:
		return "https://ajdevreddit.blob.core.windows.net/" + record['thumbnail_path']
	def get_num_remaining_records(self) -> int:
		not_thing = self.data_frame.loc[self.data_frame['thumbnail_curated'] == False]
		return len(not_thing)

	def _get_data_frame(self) -> pandas.DataFrame:
		data_frame = pandas.read_parquet("data/parquet/thumbnail_curation.parquet", engine='pyarrow',
										 filesystem=self.file_storage, schema=tagging_schema)
		return data_frame

	def _get_file_storage(self) -> AzureFileStorageAdapter:
		return AzureFileStorageAdapter("data").get_file_storage()

	def get_records_to_process(self) -> list[dict]:
		return self.data_frame.to_dict(orient='records')

	def reset(self):
		self.file_storage = self._get_file_storage()
		self.data_frame = self._get_data_frame()
		self.records_to_process_iterator = iter(self.get_records_to_process())
		self.current_record = None

	def get_record_by_id(self, record_id) -> dict:
		return self.data_frame.loc[self.data_frame['id'] == record_id].to_dict(orient='records')[0]

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

		temp.to_parquet('data/parquet/thumbnail_curation.parquet', engine="pyarrow", filesystem=self.file_storage,
						schema=curation_schema)
		self.data_frame: pandas.DataFrame = temp
		return None