import hashlib
import os
import threading

from retry import retry
import requests
import pandas
import asyncpraw
import requests
from PIL import Image
from adlfs import AzureBlobFileSystem
from azure.data.tables import TableClient
import io
import asyncio
import time
import asyncpraw
import requests
import os
import hashlib
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.azure_storage.tables import TableAdapter


class RedditImageCollector(threading.Thread):
	def __init__(self):
		super().__init__(daemon=True, name="RedditImageCollector")
		self._table_adapter: TableAdapter = TableAdapter()
		self._file_system: AzureBlobFileSystem = AzureFileStorageAdapter('data').get_file_storage()
		self._subs: [str] = [
			"tightdresses",
			"Dresses",
			"SlitDresses",
			"CollaredDresses",
			"DressesPorn",
			"WomenInLongDresses",
			"TrueFMK",
			"DLAH",
			"SFWRedheads",
			"sfwpetite",
			"SFWNextDoorGirls",
			"realasians",
			"KoreanHotties",
			"prettyasiangirls",
			"AsianOfficeLady",
			"AsianInvasion",
			"AesPleasingAsianGirls"
			"sexygirls",
			"PrettyGirls",
			"gentlemanboners",
			"hotofficegirls",
			"Ifyouhadtopickone"
		]
		self._sources: [dict] = [
			{"name": "CityDiffusion", "data": ["CityPorn"]},
			{"name": "NatureDiffusion", "data": ["EarthPorn"]},
			{"name": "CosmicDiffusion", "data": ["spaceporn"]},
			{"name": "ITAPDiffusion", "data": ["itookapicture"]},
			{"name": "MemeDiffusion", "data": ["memes"]},
			{"name": "TTTDiffusion", "data": ["trippinthroughtime"]},
			{"name": "WallStreetDiffusion", "data": ["wallstreetbets"]},
			{"name": "SexyDiffusion", "data": ["selfies", "Amicute", "amihot", "AmIhotAF", "HotGirlNextDoor"]},
			{"name": "FatSquirrelDiffusion", "data": ["fatsquirrelhate"]},
			{"name": "CelebrityDiffusion", "data": ["celebrities"]},
			{"name": "OldLadyDiffusion", "data": ["oldladiesbakingpies"]},
			{"name": "MildlyPenisDiffusion", "data": ["mildlypenis"]},
			{"name": "SWFPetite", "data": ["sfwpetite"]},
			{"name": "SFWMilfs", "data": ["cougars_and_milfs_sfw"]},
			{"name": "RedHeadDiffusion", "data": ["SFWRedheads"]},
			{"name": "NextDoorGirlsDiffusion", "data": ["SFWNextDoorGirls"]},
			{"name": "SexyDressDiffusion", "data": ["SunDressesGoneWild", "ShinyDresses", "SlitDresses", "CollaredDresses", "DressesPorn", "WomenInLongDresses", "Dresses", "tightdresses", "DLAH"]},
			{"name": "SexyAsianDiffusion", "data": ["realasians", "KoreanHotties", "prettyasiangirls", "AsianOfficeLady", "AsianInvasion", "AesPleasingAsianGirls"]},
			{"name": "PrettyGirlDiffusion", "data": ["sexygirls", "PrettyGirls", "gentlemanboners", "hotofficegirls", "TrueFMK", "Ifyouhadtopickone"]},
			{"name": "CandleDiffusion", "data": ["bathandbodyworks"]}
		]
		self._worker_thread = threading.Thread(target=self.run, name="RedditImageCollector", daemon=True)

	def _make_table_row(self, submission, image_hash):
		table_row = {
			'PartitionKey': str(submission.subreddit),
			'RowKey': submission.id,
			'id': submission.id,
			'subreddit': str(submission.subreddit),
			'author': str(submission.author),
			'title': submission.title,
			'caption': "",
			'hash': image_hash,
			'permalink': submission.permalink,
			'original_url': submission.url,
			'image_name': f"{submission.id}.jpg",
			'path': f"data/image/{submission.id}.jpg",
			'model': "",
			'exists': False,
			'curated': False,
			'accept': False,
			'tags': "",
		}
		return table_row

	def _add_source(self, x: dict, source_list) -> str:
		sub_reddit = x['subreddit']
		for source in source_list:
			data_source = [item.lower() for item in source['data']]
			source_name = source['name']
			if sub_reddit.lower() in data_source:
				return source_name
		return ""

	def _get_extant_data(self, target: str) -> [str]:
		client = self._table_adapter.service.get_table_client(target)
		extant_ids = list(client.list_entities(select=['id']))
		extant_ids = [item["id"] for item in extant_ids]
		client.close()
		return extant_ids

	async def run_polling_for_new_images(self):
		print("Starting Reddit-Image-Collector Poller")
		target = 'curationPrimary'

		# Target subreddit
		subreddit_name = "+".join(self._subs)
		extant_data = self._get_extant_data(target)
		# Create a Reddit instance
		reddit = asyncpraw.Reddit(site_name='KimmieBotGPT')
		try:
			subreddit = await reddit.subreddit(subreddit_name)

			async for submission in subreddit.stream.submissions(skip_existing=False):
				await submission.load()
				if submission.id in extant_data:
					# print("Image already acquired")
					continue
				if submission is None:
					time.sleep(1)
					continue
				else:
					if submission.url.endswith(('.jpg', '.jpeg', '.png')):
						image_url = submission.url
						response = requests.get(image_url)
						image_hash = hashlib.md5(response.content).hexdigest()
						row = self._make_table_row(submission, image_hash)
						with self._file_system.open(row['path'], "wb") as file:
							file.write(response.content)

						exists = self._file_system.exists(row['path'])

						row["model"] = self._add_source(row, self._sources)
						row["exists"] = exists

						client = self._table_adapter.get_table_client(target)
						client.upsert_entity(row)
						client.close()
						extant_data = self._get_extant_data(target)
		except Exception as e:
			print(e)
			time.sleep(1)
			await reddit.close()
			raise Exception("RedditImageCollector: Error in run_polling_for_new_images")


	def wrap_async(self):
		try:
			asyncio.run(self.run_polling_for_new_images())
		except Exception as e:
			print(e)
			asyncio.run(self.run_polling_for_new_images())

	def run(self):
		print("Starting Reddit-Image-Collector Runner")
		self.wrap_async()
