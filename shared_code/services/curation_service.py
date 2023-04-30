import pandas
import sys
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.services.pyarrow_schema import curation_schema


class CurationService:



	def __init__(self):
		self.file_storage = self._get_file_storage()
		self.data_frame = self._get_data_frame()
		self.records_to_process_iterator = iter(self.get_records_to_process())
		self.current_record = None
		sys.setrecursionlimit(100000000)

	def get_num_remaining_records(self) -> int:
		not_thing = self.data_frame.loc[self.data_frame['curated'] == False]
		return len(not_thing)

	def reset(self):
		self.file_storage = self._get_file_storage()
		self.data_frame = self._get_data_frame()
		self.records_to_process_iterator = iter(self.get_records_to_process())
		self.current_record = None

	def _do_recursion(self, record):
		pass


	def get_next_record(self):
		if self.current_record is None:
			self.current_record = next(self.records_to_process_iterator)
			if self.should_curate(self.current_record):
				return self.current_record
			else:
				return self.get_next_record()
		else:
			self.current_record = next(self.records_to_process_iterator)

			if self.should_curate(self.current_record):
				return self.current_record
			else:
				return self.get_next_record()

	def should_curate(self, record):
		is_curated = record['curated']
		is_accepted = record['accept']
		return not is_curated and not is_accepted


	def get_image_url(self, record):
		return "https://ajdevreddit.blob.core.windows.net/" + record['path']

	def update_record(self, record_id, action, caption):
		record = self.current_record
		if record['id'] != record_id:
			raise Exception("Record Ids Do Not Match")
		if action == "accept":
			record['curated'] = True
			record['accept'] = True
		else:
			record['curated'] = True
			record['accept'] = False

		record['caption'] = caption

		temp = self.data_frame.copy(deep=True)

		temp.loc[temp['id'] == record['id'], 'accept'] = record['accept']
		temp.loc[temp['id'] == record['id'], 'curated'] = record['curated']
		temp.loc[temp['id'] == record['id'], 'caption'] = record['caption']

		temp.to_parquet('data/parquet/back.parquet', engine="pyarrow", filesystem=self.file_storage, schema=curation_schema)
		self.data_frame = temp
		return

	def update_record_tag(self, record):
		temp = self.data_frame.copy(deep=True)
		temp.loc[temp['id'] == record['id'], 'tags'] = record['tags']
		temp.to_parquet('data/parquet/back.parquet', engine="pyarrow", filesystem=self.file_storage, schema=curation_schema)
		self.data_frame = temp
		return

	def get_record_by_id(self, record_id):
		return self.data_frame.loc[self.data_frame['id'] == record_id].to_dict(orient='records')[0]

	def list_subs(self):
		return self.data_frame['subreddit'].unique().tolist()

	def filter_subs(self, sub):
		temp = self.data_frame.loc[self.data_frame['subreddit'] == sub].to_dict(orient='records')
		self.data_frame = pandas.DataFrame(data=temp)
		return


	def get_records_to_process(self):
		return self.data_frame.to_dict(orient='records')

	def _get_data_frame(self):
		data_frame = pandas.read_parquet('data/parquet/back.parquet', filesystem=self.file_storage, engine='pyarrow', schema=curation_schema)
		return data_frame

	def _get_file_storage(self):
		return AzureFileStorageAdapter("data").get_file_storage()
