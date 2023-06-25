import io
import json
import os

import requests
from PIL import ImageFilter, Image
from PIL.ImageOps import contain
from adlfs import AzureBlobFileSystem

from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
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


def run_azure():
	from tqdm import tqdm
	client = TableAdapter().get_table_client('curationSecondary')
	file_system = AzureFileStorageAdapter('data').get_file_storage()
	extant = file_system.ls('data/image')
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

def _pad(image, size, centering=(0.5, 0.5)):
	resized = contain(image, size)
	temp_blur = image.resize((512, 512)).filter(ImageFilter.GaussianBlur(10))
	if resized.size == size:
		out = resized
	else:
		out = temp_blur
		if resized.palette:
			out.putpalette(resized.getpalette())
		if resized.width != size[0]:
			x = round((size[0] - resized.width) * max(0, min(centering[0], 1)))
			out.paste(resized, (x, 0))
		else:
			y = round((size[1] - resized.height) * max(0, min(centering[1], 1)))
			out.paste(resized, (0, y))
	return out


def _create_pil_thumbnail(_image_id: str, _file_system: AzureBlobFileSystem):
	try:
		pil_thumbnail_path = f"data/image/pil_thumbnail/{_image_id}.jpg"
		image_path = f"data/image/{_image_id}.jpg"
		with _file_system.open(image_path, 'rb') as f:
			image = Image.open(f)
			copied_image = image.copy()
			image.close()
			padded_image = _pad(copied_image, (512, 512))
			read_bytes_buffer = io.BytesIO()
			padded_image.save(read_bytes_buffer, format='JPEG')
			with _file_system.open(pil_thumbnail_path, 'wb') as out:
				out.write(read_bytes_buffer.getvalue())
			padded_image.close()
			copied_image.close()
			return pil_thumbnail_path
	except Exception as e:
		print(e)
		return None


if __name__ == '__main__':
	from tqdm import tqdm

	client = TableAdapter().get_table_client('curationSecondary')
	file_system = AzureFileStorageAdapter('data').get_file_storage()
	extant = [os.path.basename(x) for x in file_system.ls('data/image')]
	entities = client.query_entities("thumbnail_exists eq true")
	entities = list(entities)
	for entity in tqdm(entities, total=len(entities)):
		image_id = entity['id']
		if f"{image_id}.jpg" in extant:
			entity['pil_thumbnail_path'] = _create_pil_thumbnail(image_id, file_system)
			client.upsert_entity(entity)
			continue
	client.close()
