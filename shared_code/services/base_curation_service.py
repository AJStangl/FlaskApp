from abc import ABC, abstractmethod

import pandas
from adlfs import AzureBlobFileSystem


class BaseService(ABC):
	def __init__(self, parquet_path: str):
		self.parquet_path = parquet_path

	@abstractmethod
	def get_num_remaining_records(self) -> int:
		pass

	@abstractmethod
	def reset(self):
		pass

	@abstractmethod
	def get_next_record(self) -> dict:
		pass

	@abstractmethod
	def _should_curate(self, record: dict) -> bool:
		pass

	@abstractmethod
	def get_image_url(self, record: dict) -> str:
		pass

	@abstractmethod
	def update_record(self, record_id: str, action: str, caption: str, additional_captions: list[str],
					  relevant_tags: list[str]) -> None:
		pass

	@abstractmethod
	def update_record_tag(self, record: dict) -> None:
		pass

	@abstractmethod
	def get_record_by_id(self, record_id) -> dict:
		pass

	@abstractmethod
	def list_subs(self) -> list:
		pass

	@abstractmethod
	def filter_subs(self, sub) -> None:
		pass

	def get_records_to_process(self) -> list[dict]:
		pass

	@abstractmethod
	def _get_data_frame(self) -> pandas.DataFrame:
		pass

	@abstractmethod
	def _get_file_storage(self) -> AzureBlobFileSystem:
		pass

