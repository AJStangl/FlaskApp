import io
import json
import os

import requests
from PIL import Image
from adlfs import AzureBlobFileSystem
from azure.ai.vision import VisionServiceOptions, VisionSource, ImageAnalysisOptions, ImageAnalysisFeature, \
	ImageAnalyzer, ImageAnalysisResultDetails, ImageAnalysisResultReason, ImageAnalysisResult, ImageAnalysisErrorDetails

from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.azure_storage.tables import TableAdapter


class AzureCaption(object):
	def __init__(self):
		self.__subscription_key: str = os.environ["AZURE_VISION_API_KEY"]
		self.__endpoint: str = os.environ["AZURE_VISION_ENDPOINT"]
		self.__file_system: AzureBlobFileSystem = AzureFileStorageAdapter("data").get_file_storage()
		self.__table_adapter: TableAdapter = TableAdapter()

	def run_image_process(self, image_id: str) -> str:
		try:
			out_path = f"data/caption/{image_id}.json"
			temp_url = "https://ajdevreddit.blob.core.windows.net/data/image/" + image_id + ".jpg"
			if self.__file_system.exists(out_path):
				print(f"File already exists: {out_path}")
				return out_path
			image_analyzer: ImageAnalyzer = self._get_image_analyzer(image_url=temp_url)

			try:
				image_analysis_result: ImageAnalysisResult = image_analyzer.analyze()
				if image_analysis_result.reason == ImageAnalysisResultReason.ANALYZED:
					image_json_result: ImageAnalysisResultDetails = ImageAnalysisResultDetails.from_result(
						image_analysis_result)
					if image_json_result is not None:
						json_result = image_json_result.json_result
						with self.__file_system.open(out_path, 'w', encoding='utf-8') as handle:
							handle.write(json_result)
							return out_path
					else:
						print("No image analysis result")
						return None

				if image_analysis_result.reason == ImageAnalysisResultReason.ERROR:
					error_details = ImageAnalysisErrorDetails.from_result(image_analysis_result)
					print(f"Error: {error_details}")
					return None

			except Exception as e:
				print(e)
				return None

			finally:
				del image_analyzer

			if image_analysis_result is not None:
				print("Image Analysis Result: ", image_analysis_result)
				return image_analysis_result
			else:
				print("Image Analysis Result: ", image_analysis_result)
				return None

		except Exception as e:
			print(e)
			raise Exception("Bruh")

	def run_analysis(self, image_id):
		try:
			dense_caption_table_client = self.__table_adapter.get_table_client("denseCaptions")

			relevant_tags_table_client = self.__table_adapter.get_table_client("relevantTags")

			secondary_curation_table_client = self.__table_adapter.get_table_client("curationSecondary")

			current_captions = self.__file_system.exists(f"data/caption/{image_id}.json")

			print(f"=== current caption files: {current_captions} ===")

			if not current_captions:
				print("No caption file found, no analysis to run")
				return

			caption_data = json.loads(self.__file_system.read_text(f"data/caption/{image_id}.json", encoding='utf-8'))

			caption_data["id"] = image_id

			dense_caption_result = caption_data.get('denseCaptionsResult')

			metadata = caption_data.get('metadata')

			tags_result = caption_data.get('tagsResult')

			smart_crop_result = caption_data.get('smartCropsResult')

			basic_caption = caption_data.get('captionResult')

			filtered_data = {
				"id": image_id,
				"captions": basic_caption,
				"dense_captions": dense_caption_result['values'],
				"meta": metadata,
				"tags": tags_result['values'],
				"smart_crop": smart_crop_result['values']
			}

			# Update the dense captions table and the relevant tags table
			for i, item in enumerate(filtered_data.get('dense_captions')):
				dense_entity = {
					'PartitionKey': str(image_id),
					'RowKey': str(i),
					'boundingBox_x': item['boundingBox']['x'],
					'boundingBox_y': item['boundingBox']['y'],
					'boundingBox_w': item['boundingBox']['w'],
					'boundingBox_h': item['boundingBox']['h'],
					'confidence': item['confidence'],
					'id': image_id,
					'text': item['text']
				}
				dense_caption_table_client.upsert_entity(dense_entity)

			# Update the relevant tags table
			for i, item in enumerate(filtered_data.get('tags')):
				tag_entity = {
					'PartitionKey': str(image_id),
					'RowKey': str(i),
					'id': str(image_id),
					'name': item['name'],
					'confidence': item['confidence']
				}
				relevant_tags_table_client.upsert_entity(tag_entity)

			# Find the table record for the image
			entity = list(secondary_curation_table_client.query_entities(f"RowKey eq '{image_id}'"))
			if len(entity) == 0:
				print(f"No entity found for {image_id}")
				return
			if len(entity) > 1:
				print(f"Multiple entities found for {image_id}")
				return

			# Now we have the entity, we can update it with the new data
			entity = entity[0]

			entity['azure_caption'] = filtered_data['captions']['text']

			entity['tags'] = json.dumps([item['name'] for item in filtered_data['tags']])

			cropping = filtered_data['smart_crop'][0]

			thumbnail_path = self._create_thumbnail(image_id, cropping, entity['path'])

			azure_thumbnail_path = self._auto_azure_thumbnail(image_id)

			pil_thumbnail_path = self._create_pil_thumbnail(image_id)
			if pil_thumbnail_path is not None:
				entity['pil_thumbnail_path'] = pil_thumbnail_path

			if azure_thumbnail_path is not None:
				entity['azure_thumbnail_path'] = azure_thumbnail_path

			if self.__file_system.exists(thumbnail_path):
				entity['thumbnail_path'] = thumbnail_path
				entity['thumbnail_exists'] = True
			else:
				entity['thumbnail_exists'] = False

			secondary_curation_table_client.upsert_entity(entity)

		except Exception as e:
			print(e)
			raise e

	def _get_image_analyzer(self, image_path: str = None, image_url: str = None) -> ImageAnalyzer:
		service_options: VisionServiceOptions = VisionServiceOptions(self.__endpoint, self.__subscription_key)
		vision_source: VisionSource = VisionSource(filename=image_path, url=image_url)
		analysis_options: ImageAnalysisOptions = ImageAnalysisOptions()

		analysis_options.features = (
				ImageAnalysisFeature.CROP_SUGGESTIONS |
				ImageAnalysisFeature.CAPTION |
				ImageAnalysisFeature.DENSE_CAPTIONS |
				ImageAnalysisFeature.OBJECTS |
				ImageAnalysisFeature.PEOPLE |
				ImageAnalysisFeature.TEXT |
				ImageAnalysisFeature.TAGS
		)

		analysis_options.cropping_aspect_ratios = [1.0, 1.0]
		analysis_options.language = "en"

		analysis_options.model_version = "latest"
		analysis_options.gender_neutral_caption = False

		image_analyzer: ImageAnalyzer = ImageAnalyzer(service_options, vision_source, analysis_options)

		return image_analyzer

	def _get_aspect_ratio(self, x: dict):
		return x['crops'][0]['aspectRatio']

	def _get_bounding_box(self, x: dict):
		return x['crops'][0]['boundingBox']

	def _create_thumbnail(self, target_image_id: str, cropping_information: dict, parent_image_path: str):
		_file_system: AzureBlobFileSystem = AzureFileStorageAdapter('data').get_file_storage()
		out_path = f"data/image/thumbnail/{target_image_id}.jpg"
		try:
			image_url = _file_system.url(parent_image_path)
			original_image = Image.open(requests.get(image_url, stream=True).raw)
			copied_image = original_image.copy()
			original_image.close()

			cropped = copied_image.crop((cropping_information['boundingBox']['x'],
										 cropping_information['boundingBox']['y'],
										 cropping_information['boundingBox']['x'] +
										 cropping_information['boundingBox']['w'],
										 cropping_information['boundingBox']['y'] +
										 cropping_information['boundingBox']['h']))
			copied_image.close()
			resized = cropped.resize((512, 512), 1)
			cropped.close()
			img_byte_arr = io.BytesIO()
			resized.save(img_byte_arr, format='JPEG')
			resized.close()
			with _file_system.open(out_path, 'wb', encoding='utf-8') as handle:
				handle.write(img_byte_arr.getvalue())
			resized.close()
			print(f'Thumbnail created for {target_image_id}')
			return out_path

		except Exception as ex:
			print(f'Error creating thumbnail for {target_image_id}: {ex}')
			return "/data/nope"

	def _auto_azure_thumbnail(self, image_id: str, width: int = 512, height: int = 512, smartCropping: bool = True):
		try:
			endpoint = f"vision/v3.1/generateThumbnail?width={width}&height={height}&smartCropping={smartCropping}"
			base = os.environ["AZURE_VISION_ENDPOINT"]
			url = f"{base}{endpoint}"
			headers = {
				"Ocp-Apim-Subscription-Key": os.environ["AZURE_VISION_API_KEY"],
			}
			data = {

				"url": "https://ajdevreddit.blob.core.windows.net/data/image/" + image_id + ".jpg"
			}
			result = requests.post(url, headers=headers, data=json.dumps(data))

			if result.status_code != 200:
				print(f"Error creating Azure thumbnail for {image_id}: {result.status_code}")
				print(result.content)
				return None

			with self.__file_system.open(f"data/image/azure/{image_id}.jpg", 'wb') as f:
				f.write(result.content)

			print("Thumbnail Azure Thumbnail created for " + image_id)
			return f"data/image/azure/{image_id}.jpg"
		except Exception as ex:
			print(f'Error creating Azure thumbnail for {image_id}: {ex}')
			return None

	def _create_pil_thumbnail(self, image_id: str):
		try:
			pil_thumbnail_path = f"data/image/pil_thumbnail/{image_id}.jpg"
			image_path = f"data/image/{image_id}.jpg"
			with self.__file_system.open(image_path, 'rb') as f:
				image = Image.open(f)
				copied_image = image.copy()
				image.close()
				copied_image.thumbnail((512, 512), Image.BOX, reducing_gap=3.0)
				read_bytes_buffer = io.BytesIO()
				copied_image.save(read_bytes_buffer, format='JPEG')
				with self.__file_system.open(pil_thumbnail_path, 'wb') as out:
					out.write(read_bytes_buffer.getvalue())
				copied_image.close()
				return pil_thumbnail_path
		except Exception as e:
			print(e)
			return None
