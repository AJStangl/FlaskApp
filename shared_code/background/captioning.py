import sys
import threading
import time, json, requests, os

from adlfs import AzureBlobFileSystem
from azure.data.tables import TableClient
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.azure_storage.tables import TableAdapter
import logging


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
	def create_curation_entity(subreddit: str, record_id: str, title: str, caption: str, path: str,
							   input_type: str) -> dict:
		return {
			"PartitionKey": subreddit,
			"RowKey": f"{record_id}-{input_type}",
			"GPT": f"<|startoftext|><|model|>{subreddit}<|title|>{title}<|caption|>{title}, {caption}, in the style of r/{subreddit}<|endoftext|>",
			"subreddit": subreddit,
			"title": title,
			"format_caption": f"{title}, {caption}, is the style of r/{subreddit}",
			"path": path,
			"type": input_type,
			"training_count": 0
		}

	def auto_azure_thumbnail(self, _image_id: str, crop_type: str, width: int = 512, height: int = 512,
							 smartCropping: bool = True, _file_system: AzureBlobFileSystem = None):
		try:
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
				return f"bruh, {result.status_code}"

			with _file_system.open(f"data/image/768/{crop_type}/{_image_id}.jpg", 'wb') as f:
				f.write(result.content)

			logger.info(f"\nThumbnail {crop_type} Thumbnail created for " + _image_id)
			return f"data/image/768/{crop_type}/{_image_id}.jpg"

		except Exception as ex:
			logger.exception(f'\nError creating {crop_type} thumbnail for {_image_id}: {ex}')
			return f"bruh, {ex}"

	def run(self):
		while True:
			table_client: TableClient = TableAdapter().get_table_service_client().get_table_client("curationSecondary")
			records = list(table_client.query_entities(query_filter="thumbnail_accept eq true and (subreddit ne 'CityPorn' or subreddit ne 'bathandbodyworks' or subreddit ne 'fatsquirrelhate' or sureddit ne 'EarthPorn' or subreddit ne 'itookapicture')"))
			table_client_768 = TableAdapter().get_table_service_client().get_table_client("training768")
			try:
				for record in records:
					smart_path_768 = record.get("large_smart_path")
					azure_path_768 = record.get("large_azure_path")
					if smart_path_768 is not None:
						continue
					else:
						path_smart = self.auto_azure_thumbnail(record.get("id"), "smart", 768, 768, smartCropping=True, _file_system=self.file_system)
						record_1 = self.create_curation_entity(record.get("subreddit"), record.get("id"), record.get("title"), record.get("smart_caption"), path_smart, "smart")
						table_client_768.upsert_entity(entity=record_1)
						time.sleep(10)
					if azure_path_768 is not None:
						continue
					else:
						path_azure = self.auto_azure_thumbnail(record.get("id"), "azure", 768, 768, smartCropping=False, _file_system=self.file_system)
						record_2 = self.create_curation_entity(record.get("subreddit"), record.get("id"), record.get("title"), record.get("azure_caption"), path_azure, "azure")
						table_client_768.upsert_entity(entity=record_2)
						time.sleep(10)
			finally:
				table_client.close()
				table_client_768.close()



	def start(self):
		logger.info("== Starting captioning process ==")
		self.worker_thread.start()

	def stop(self):
		logger.info("== Stopping captioning process ==")
		sys.exit(0)