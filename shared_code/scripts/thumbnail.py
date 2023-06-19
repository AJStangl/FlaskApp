import io

from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.azure_storage.tables import TableAdapter
from PIL import Image

if __name__ == '__main__':
	from tqdm import tqdm

	file_system = AzureFileStorageAdapter('data').get_file_storage()

	curation_secondary_table_client = TableAdapter().get_table_client('curationSecondary')
	with tqdm(total=len(list(curation_secondary_table_client.list_entities(select='id')))) as pbar:
		for item in curation_secondary_table_client.list_entities():
			try:
				pil_thumbnail_path = f"data/image/pil_thumbnail/{item['id']}.jpg"
				image_path = f"data/image/{item['id']}.jpg"
				if file_system.exists(pil_thumbnail_path):
					item['pil_thumbnail_path'] = pil_thumbnail_path
					curation_secondary_table_client.upsert_entity(item)
					continue
				else:
					with file_system.open(image_path, 'rb') as f:
						image = Image.open(f)
						copied_image = image.copy()
						image.close()
						copied_image.thumbnail((512, 512), Image.LANCZOS)
						read_bytes_buffer = io.BytesIO()
						copied_image.save(read_bytes_buffer, format='JPEG')
						with file_system.open(pil_thumbnail_path, 'wb') as out:
							out.write(read_bytes_buffer.getvalue())
						copied_image.close()
						item['pil_thumbnail_path'] = pil_thumbnail_path
						curation_secondary_table_client.upsert_entity(item)
					pass
			except Exception as e:
				print(e)
				continue
			finally:
				pbar.update(1)




