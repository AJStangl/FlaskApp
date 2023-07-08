import io

from shared_code.storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.storage.tables import TableAdapter
from PIL import Image

if __name__ == '__main__':
	from tqdm import tqdm

	file_system = AzureFileStorageAdapter('data').get_file_storage()

	client_dense_table = TableAdapter().get_table_client('denseCaptions')
	with tqdm(total=len(list(client_dense_table.list_entities(select='id')))) as pbar:
		for item in client_dense_table.list_entities():
			try:
				image_from_caption_path = f"data/image/dense/{item['id']}/{item['text'].replace(' ', '-')}.jpg"
				image_path = f"data/image/{item['id']}.jpg"
				if file_system.exists(image_from_caption_path):
					item['image_from_caption_path'] = image_from_caption_path
					client_dense_table.upsert_entity(item)
					continue
				else:
					with file_system.open(image_path, 'rb') as f:
						image = Image.open(f)
						copied_image = image.copy()
						image.close()

						boundingBox_x = item['boundingBox_x']
						boundingBox_y = item['boundingBox_y']
						boundingBox_w = item['boundingBox_w']
						boundingBox_h = item['boundingBox_h']

						cropped_image = copied_image.crop((boundingBox_x, boundingBox_y, boundingBox_x + boundingBox_w, boundingBox_y + boundingBox_h))
						resized_image = cropped_image.resize((512, int(512 * (cropped_image.height / cropped_image.width))))
						copied_image.close()
						cropped_image.close()
						read_bytes_buffer = io.BytesIO()
						resized_image.save(read_bytes_buffer, format='JPEG')
						with file_system.open(image_from_caption_path, 'wb') as out:
							out.write(read_bytes_buffer.getvalue())
						resized_image.close()
						item['image_from_caption_path'] = image_from_caption_path
						client_dense_table.upsert_entity(item)
			finally:
				pbar.update(1)




