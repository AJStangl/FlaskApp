import asyncio
import hashlib
import logging
import os
import threading
import time

import asyncpraw
import requests
from adlfs import AzureBlobFileSystem
import random
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
from shared_code.azure_storage.tables import TableAdapter


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger("diffusers").setLevel(logging.WARNING)
logging.getLogger("azure.storage").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


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
		self.worker_thread = threading.Thread(target=self.run, name="RedditImageCollector", daemon=True)
		self.records_processed = 0

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
		logger.info("Starting Reddit-Image-Collector Poller")
		target = 'curationPrimary'
		random.shuffle(self._subs)
		subreddit_name = "+".join(self._subs)
		extant_data = self._get_extant_data(target)
		reddit = asyncpraw.Reddit(client_id=os.environ['client_id'], client_secret=os.environ['client_secret'],
								  password=os.environ['password'],
								  user_agent="script:%(bot_name)s:v%(bot_version)s (by /u/%(bot_author)s)",
								  username=os.environ["reddit_username"])
		try:
			subreddit = await reddit.subreddit(subreddit_name)
			async for submission in subreddit.stream.submissions(skip_existing=False):
				await submission.load()
				if submission.id in extant_data:
					logger.info("=== Image already acquired ===")
					continue
				if submission is None:
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

						row["model"] = ""
						row["exists"] = exists

						client = self._table_adapter.get_table_client(target)
						client.upsert_entity(row)
						self.records_processed += 1
						client.close()
						extant_data = self._get_extant_data(target)
						logger.info(f"{row}")
		except Exception as e:
			logger.exception(e)
			time.sleep(1)
			await reddit.close()
		finally:
			await reddit.close()

	def wrap_async(self):
		try:
			asyncio.run(self.run_polling_for_new_images())
		except Exception as e:
			logger.exception(e)

	def run(self):
		logger.info("=== Starting Reddit-Image-Collector Runner ===")
		self.wrap_async()

	def stop(self):
		logger.info("=== Stopping Reddit-Image-Collector Runner ===")
		[item.cancel() for item in asyncio.all_tasks(asyncio.get_event_loop())]
		self.worker_thread.join()
