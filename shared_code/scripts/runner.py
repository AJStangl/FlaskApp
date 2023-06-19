import time

from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
import os
import requests
import json

from shared_code.azure_storage.tables import TableAdapter


def auto_azure_thumbnail(_image_id: str, width: int = 512, height: int = 512, smartCropping: bool = False):
	try:
		_file_system = AzureFileStorageAdapter('data').get_file_storage()
		endpoint = f"vision/v3.1/generateThumbnail?width={width}&height={height}&smartCropping={smartCropping}"
		base = os.environ["AZURE_VISION_ENDPOINT"]
		url = f"{base}{endpoint}"
		headers = {
			"Ocp-Apim-Subscription-Key": os.environ["AZURE_VISION_API_KEY"],
		}
		data = {
			"url": _file_system.url(f"data/image/{image_id}.jpg")
		}
		result = requests.post(url, headers=headers, data=json.dumps(data))

		if result.status_code != 200:
			print(f"Error creating Azure thumbnail for {image_id}: {result.status_code}")
			print(result.content)
			return None

		with _file_system.open(f"data/image/azure/{image_id}.jpg", 'wb') as f:
			f.write(result.content)

		print("Thumbnail Azure Thumbnail created for " + image_id)
		return f"data/image/azure/{image_id}.jpg"
	except Exception as ex:
		print(f'Error creating Azure thumbnail for {image_id}: {ex}')
		return None



if __name__ == '__main__':
	from tqdm import tqdm
	client = TableAdapter().get_table_client('curationSecondary')
	file_system = AzureFileStorageAdapter('data').get_file_storage()
	extant = file_system.ls('data/image/azure')
	extant = [os.path.basename(x) for x in extant]
	entities = client.query_entities("thumbnail_exists eq true")
	entities = list(entities)
	for entity in tqdm(entities, total=len(entities)):
		image_id = entity['id']
		if f"{image_id}.jpg" in extant:
			entity['azure_thumbnail_path'] = f"data/image/azure/{image_id}.jpg"
			client.upsert_entity(entity)
			continue
		azure_thumbnail_path = auto_azure_thumbnail(_image_id=entity['id'], smartCropping=False)
		if azure_thumbnail_path is not None:
			entity['azure_thumbnail_path'] = azure_thumbnail_path
		else:
			entity['azure_thumbnail_path'] = ""
		client.upsert_entity(entity)
	client.close()