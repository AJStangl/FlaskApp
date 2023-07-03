import torch
from PIL import Image
import requests
from adlfs import AzureBlobFileSystem
from azure.data.tables import TableClient
from transformers import BlipProcessor, BlipForConditionalGeneration

from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.azure_storage.tables import TableAdapter


class BlipCaption:
	def __init__(self):
		self.__processor: BlipProcessor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
		self.__device = torch.device("cpu")
		self.__model: BlipForConditionalGeneration = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large").to(self.__device)
		self.__table_adapter: TableAdapter = TableAdapter()

	def caption_image(self, image_id):
		table_client: TableClient = self.__table_adapter.get_table_client("curationSecondary")
		file_system = AzureFileStorageAdapter("data").get_file_storage()
		try:
			query_result = table_client.query_entities(query_filter=f"RowKey eq '{image_id}'")
			result = list(query_result)
			if len(result) != 1:
				print("Query has returned an incorrect number of records")
				return ""
			else:
				record = result[0]
				thumbnail_path = record['thumbnail_path']
				pil_thumbnail_path = record['pil_thumbnail_path']

				smart_caption = ""
				caption = ""
				pil_caption = ""

				if file_system.exists(thumbnail_path):
					image_url = file_system.url(thumbnail_path)
					smart_caption = self._caption_image_from_url(image_url)
					if smart_caption.startswith("ara"):
						smart_caption = " ".join(smart_caption.split(" ")[1:])

				if file_system.exists(pil_thumbnail_path):
					pil_url = file_system.url(pil_thumbnail_path)
					pil_caption = self._caption_image_from_url(pil_url)
					if pil_caption.startswith("ara"):
						pil_caption = " ".join(pil_caption.split(" ")[1:])

				record["smart_caption"] = smart_caption
				record["caption"] = caption
				record["pil_caption"] = pil_caption

				table_client.upsert_entity(entity=record)

		finally:
			table_client.close()



	def _caption_image_from_url(self,  image_url: str) -> str:
		try:
			image = Image.open(requests.get(image_url, stream=True).raw)
			device = torch.device("cpu")
			inputs = self.__processor(image, return_tensors="pt").to(device)
			out = self.__model.generate(**inputs)
			return self.__processor.decode(out[0], skip_special_tokens=True, max_new_tokens=200)
		except Exception as e:
			print(e)
			return ""
