import logging
import os
import random
from typing import Union
from unittest import result
import json
import requests
from PIL import Image
import pandas
from adlfs import AzureBlobFileSystem
from azure.ai.vision import VisionServiceOptions, VisionSource, ImageAnalysisOptions, ImageAnalysisFeature, \
	ImageAnalyzer, ImageAnalysisResultDetails, ImageAnalysisResultReason, ImageAnalysisResult, ImageAnalysisErrorDetails

import shared_code.schemas.pyarrow_schema
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter


class AzureCaption(object):
	def __init__(self):
		self.__subscription_key: str = "2ee8459a379c4b73aef287d1cf1c4b73"
		self.__endpoint: str = "https://aj-vision-ai.cognitiveservices.azure.com/"

	def run_image_process(self, image_id: str):
		fs = AzureFileStorageAdapter("data").get_file_storage()
		try:
			fs.download(f"data/image/{image_id}.jpg", "temp.jpg")
			image_analyzer: ImageAnalyzer = self._get_image_analyzer(image_path="temp.jpg")
			out_path = f"data/caption/{image_id}.json"
			if fs.exists(out_path):
				print(f"File already exists: {out_path}")
				return out_path
			try:
				image_analysis_result: ImageAnalysisResult = image_analyzer.analyze()
				if image_analysis_result.reason == ImageAnalysisResultReason.ANALYZED:
					image_json_result: ImageAnalysisResultDetails = ImageAnalysisResultDetails.from_result(
						image_analysis_result)
					if image_json_result is not None:
						json_result = image_json_result.json_result
						with fs.open(out_path, 'w', encoding='utf-8') as handle:
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



