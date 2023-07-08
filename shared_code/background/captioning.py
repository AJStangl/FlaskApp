import json
import logging
import os
import requests
import sys
import threading
import time

from adlfs import AzureBlobFileSystem
from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableClient
import pandas
from shared_code.storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.storage.tables import TableAdapter

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger("diffusers").setLevel(logging.WARNING)
logging.getLogger("azure.storage").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class CaptioningProcesses(threading.Thread):
	def __init__(self, name="captioning-background-process"):
		super().__init__(name=name, daemon=True)
		self.file_system: AzureBlobFileSystem = AzureFileStorageAdapter("data").get_file_storage()
		self.worker_thread = threading.Thread(target=self.run, daemon=True)

	@staticmethod
	def create_curation_entity(subreddit: str, record_id: str, title: str, caption: str, path: str, input_type: str, tags_to_use: str) -> dict:

		image_description = f"{caption}, {tags_to_use}"
		gpt_string = f"<|startoftext|><|model|>{subreddit}<|title|>{title}<|caption|>{image_description}<|endoftext|>"
		return {
			"PartitionKey": subreddit,
			"RowKey": f"{record_id}-{input_type}",
			"id": record_id,
			"subreddit": subreddit,
			"title": title,
			"GPT": f"{gpt_string}",
			"format_caption": f"{image_description}",
			"path": path,
			"type": input_type,
			"training_count": 0
		}

	def auto_azure_thumbnail(self, _image_id: str, crop_type: str, width: int = 512, height: int = 512,
							 smartCropping: bool = True, _file_system: AzureBlobFileSystem = None):
		try:
			logger.info(f"== Calling for Azure 768 Thumbnail Creation On: {_image_id} ==")
			endpoint = f"vision/v3.1/generateThumbnail?width={width}&height={height}&smartCropping={smartCropping}"
			base = os.environ["AZURE_VISION_ENDPOINT"]
			url = f"{base}{endpoint}"
			headers = {
				"Ocp-Apim-Subscription-Key": os.environ["AZURE_VISION_API_KEY"],
			}
			data = {
				"url": "https://ajdevreddit.blob.core.windows.net/data/image/" + _image_id + ".jpg"
			}
			result = requests.post(url, headers=headers, data=json.dumps(data))

			if result.status_code != 200:
				logger.info(f"\nError creating Azure thumbnail for {_image_id}: {result.status_code}")
				logger.info(result.content)
				return f"bruh"

			with _file_system.open(f"data/image/768/{crop_type}/{_image_id}.jpg", 'wb') as f:
				f.write(result.content)

			logger.info(f"\nThumbnail {crop_type} Thumbnail created for " + _image_id)
			return f"data/image/768/{crop_type}/{_image_id}.jpg"

		except Exception as ex:
			logger.exception(f'\nError creating {crop_type} thumbnail for {_image_id}: {ex}')
			return f"bruh"

	def get_tags(self, _image_id: str, _client):
		try:
			tags = list(_client.query_entities(query_filter=f"id eq '{_image_id}' and confidence gt 0.75", select=["id, name"]))
			df_tags = pandas.DataFrame(data=tags)
			tags_to_use = ", ".join([item.get("name") for item in df_tags.where(df_tags["id"] == _image_id).dropna().to_dict(orient='records')])
			return tags_to_use
		except Exception as ex:
			logger.exception(ex)
			return ""

	def run(self):
		while True:
			table_client_tags = TableAdapter().get_table_service_client().get_table_client("relevantTags")
			table_client: TableClient = TableAdapter().get_table_service_client().get_table_client("curationSecondary")
			query = "thumbnail_accept eq true and (subreddit ne 'mildlypenis' or subreddit ne 'CityPorn' or subreddit ne 'bathandbodyworks' or subreddit ne 'fatsquirrelhate' or subreddit ne 'EarthPorn' or subreddit ne 'itookapicture')"
			records = list(table_client.query_entities(query_filter=query))
			table_client_768 = TableAdapter().get_table_service_client().get_table_client("training768")
			try:
				for record in records:
					if record.get("path").__contains__("bruh"):
						continue

					if record.get("PartitionKey") in ["CityPorn", "bathandbodyworks", "fatsquirrelhate", "EarthPorn", "itookapicture", "mildlypenis"]:
						continue

					smart_path_768 = record.get("large_smart_path")
					azure_path_768 = record.get("large_azure_path")
					if smart_path_768 is not None:
						continue

					else:
						record_id = record.get("id")
						smart_id = f"{record_id}-smart"
						subreddit = record.get("subreddit")
						try:
							extant_1 = table_client_768.get_entity(partition_key=subreddit, row_key=smart_id)
							continue
						except ResourceNotFoundError: # pass as this indicates the record does not exist
							pass

						tags = self.get_tags(record_id, table_client_tags)
						path_smart = self.auto_azure_thumbnail(record.get("id"), "smart", 768, 768, smartCropping=True, _file_system=self.file_system)
						record_1 = self.create_curation_entity(record.get("subreddit"), record.get("id"), record.get("title"), record.get("smart_caption"), path_smart, "smart", tags)
						table_client_768.upsert_entity(entity=record_1)
						time.sleep(1)
					if azure_path_768 is not None:
						continue
					else:
						subreddit = record.get("PartitionKey")
						record_id = record.get("id")
						azure_id = f"{record_id}-azure"
						try:
							extant_2 = table_client_768.get_entity(subreddit, row_key=azure_id)
							continue
						except ResourceNotFoundError:  # pass as this indicates the record does not exist
							pass

						tags = self.get_tags(record_id, table_client_tags)
						path_azure = self.auto_azure_thumbnail(record.get("id"), "azure", 768, 768, smartCropping=False, _file_system=self.file_system)
						record_2 = self.create_curation_entity(record.get("subreddit"), record.get("id"), record.get("title"), record.get("azure_caption"), path_azure, "azure", tags)
						table_client_768.upsert_entity(entity=record_2)
						time.sleep(1)
			finally:
				table_client.close()
				table_client_768.close()
				table_client_tags.close()

	def start(self):
		logger.info("== Starting captioning process ==")
		self.worker_thread.start()

	def stop(self):
		logger.info("== Stopping captioning process ==")
		sys.exit(0)
