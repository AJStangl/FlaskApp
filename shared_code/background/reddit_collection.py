# import hashlib
# import os
# from retry import retry
# import requests
# import pandas
# import praw
# import requests
# from PIL import Image
# from adlfs import AzureBlobFileSystem
# from azure.data.tables import TableClient
#
# from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter
# from shared_code.azure_storage.tables import TableAdapter
#
#
# class RedditImageCollector:
# 	client_id = '5hVavL0PIRyM_1JSvqT6UQ'
# 	client_secret = 'BjD2kS3WNLnJc59RKY-JJUuc_Z9-JA',
# 	user_agent = 'script:%(bot_name)s:v%(bot_version)s (by /u/%(bot_author)s)',
# 	check_for_async = False
# 	file_system: AzureBlobFileSystem = AzureFileStorageAdapter('data').get_file_storage()
# 	table_adapter: TableAdapter = TableAdapter()
#
# 	client: TableClient = table_adapter.get_table_client(table_name="curationPrimary")
#
# 	subs = [
# 		"tightdresses",
# 		"Dresses",
# 		"SlitDresses",
# 		"CollaredDresses",
# 		"DressesPorn",
# 		"WomenInLongDresses",
# 		"TrueFMK",
# 		"DLAH",
# 		"SFWRedheads",
# 		"sfwpetite",
# 		"SFWNextDoorGirls",
# 		"realasians",
# 		"KoreanHotties",
# 		"prettyasiangirls",
# 		"AsianOfficeLady",
# 		"AsianInvasion",
# 		"AesPleasingAsianGirls",
# 		"sexygirls",
# 		"PrettyGirls",
# 		"gentlemanboners",
# 		"hotofficegirls",
# 		"Ifyouhadtopickone"
# 	]
# 	sources = [
# 		{"name": "CityDiffusion", "data": ["CityPorn"]},
# 		{"name": "NatureDiffusion", "data": ["EarthPorn"]},
# 		{"name": "CosmicDiffusion", "data": ["spaceporn"]},
# 		{"name": "ITAPDiffusion", "data": ["itookapicture"]},
# 		{"name": "MemeDiffusion", "data": ["memes"]},
# 		{"name": "TTTDiffusion", "data": ["trippinthroughtime"]},
# 		{"name": "WallStreetDiffusion", "data": ["wallstreetbets"]},
# 		{"name": "SexyDiffusion", "data": ["selfies", "Amicute", "amihot", "AmIhotAF", "HotGirlNextDoor"]},
# 		{"name": "FatSquirrelDiffusion", "data": ["fatsquirrelhate"]},
# 		{"name": "CelebrityDiffusion", "data": ["celebrities"]},
# 		{"name": "OldLadyDiffusion", "data": ["oldladiesbakingpies"]},
# 		{"name": "SWFPetite", "data": ["sfwpetite"]},
# 		{"name": "SFWMilfs", "data": ["cougars_and_milfs_sfw"]},
# 		{"name": "RedHeadDiffusion", "data": ["SFWRedheads"]},
# 		{"name": "NextDoorGirlsDiffusion", "data": ["SFWNextDoorGirls"]},
# 		{"name": "SexyDressDiffusion",
# 		 "data": ["SunDressesGoneWild", "ShinyDresses", "SlitDresses", "CollaredDresses", "DressesPorn",
# 				  "WomenInLongDresses", "Dresses", "tightdresses", "DLAH"]},
# 		{"name": "SexyAsianDiffusion",
# 		 "data": ["realasians", "KoreanHotties", "prettyasiangirls", "AsianOfficeLady", "AsianInvasion",
# 				  "AesPleasingAsianGirls"]},
# 		{"name": "MildlyPenisDiffusion", "data": ["mildlypenis"]},
# 		{"name": "PrettyGirlDiffusion",
# 		 "data": ["sexygirls", "PrettyGirls", "gentlemanboners", "hotofficegirls", "TrueFMK", "Ifyouhadtopickone"]},
# 		{"name": "CandleDiffusion", "data": ["bathandbodyworks"]}
# 	]
# 	sources_df = pandas.DataFrame.from_records(sources)
#
# 	def __init__(self):
# 		self.reddit = praw.Reddit(client_id=self.client_id,
# 								  client_secret=self.client_secret,
# 								  user_agent=self.user_agent,
# 						  check_for_async=self.check_for_async)
#
# 	@retry(Exception, tries=10, delay=3, jitter=2)
# 	def make_trouble(self, url):
# 		return requests.get(self, url, stream=True)
#
# 	def get_hash_from_path(self, in_path: str):
# 		if os.path.exists(in_path):
# 			with open(in_path, 'rb') as f_:
# 				content = f_.read()
# 				result = hashlib.md5(content).hexdigest()
# 				return result, content
# 		else:
# 			return ""
#
# 	def fetch_image(self, x: object, file_system__) -> str:
# 		try:
# 			url = x['original_url']
# 			subreddit = x['subreddit']
# 			image_id = x['id']
# 			os.makedirs(f"temp/image/{subreddit}", exist_ok=True)
# 			temp_path = f"temp/image/{subreddit}/{image_id}.jpg"
# 			out_path = f"data/image/{image_id}.jpg"
# 			if file_system__.exists(out_path):
# 				with self.file_system.open(out_path, 'rb') as f_:
# 					content = f_.read()
# 					md5 = hashlib.md5(content).hexdigest()
# 					if md5 != "f17b01901c752c1bb04928131d1661af" or md5 != "d835884373f4d6c8f24742ceabe74946":
# 						# TODO: For another weekend
# 						# with open(out_path, 'wb') as f_:
# 							# f_.write(content)
# 						pass
#
# 					else:
# 						print("I fucked up")
# 			else:
# 				response = requests.get(url)
# 				md5 = hashlib.md5(response.content).hexdigest()
# 				if md5 != "f17b01901c752c1bb04928131d1661af" or md5 != "d835884373f4d6c8f24742ceabe74946":
# 					try:
# 						pass
# 						# raw_image = Image.open(self.make_trouble(url).raw)
# 						# if raw_image.mode in ("RGBA", "P"):
# 						# 	raw_image = raw_image.convert("RGB")
# 						# raw_image.save(temp_path)
# 						# raw_image.close()
# 						# file_system__.upload(temp_path, out_path)
# 		except Exception as ex:
# 			message = f"{x['id']}, {x['subreddit']}, Failure in fetch_image, {ex}"
# 			print(message)
# 			return ""
#
# 	def get_table_records_per_sub(self, sub):
# 		return list(self.client.query_entities(f"PartitionKey eq '{sub}'", select="RowKey"))
#
# 	def iterate_through_subreddits(self, sub):
# 		try:
# 			subreddit_stream = list(self.reddit.subreddit(display_name=sub).new())
# 			for submission in subreddit_stream:
# 				if submission is None:
# 					continue
# 				else:
# 					if submission.id in self.get_table_records_per_sub(sub):
# 						continue
# 					else:
# 						try:
# 							sub_id = submission.id
# 							author_name = 'Unknown'
# 							subreddit_name = sub
# 							sub_title = submission.title
# 							perma_link = submission.permalink
# 							sub_url = submission.url
# 							try:
# 								author_name = submission.author.name
# 							except Exception as e:
# 								author_name = 'Unknown'
# 								pass
# 							record = {
# 								'id': sub_id,
# 								'subreddit': subreddit_name,
# 								'author': author_name,
# 								'title': sub_title,
# 								'caption': '',
# 								'hash': '',
# 								'permalink': perma_link,
# 								'original_url': sub_url,
# 								'image_name': '',
# 								'path': '',
# 								'thumbnail_path': '',
# 								'exists': False,
# 								'curated': False,
# 								'Tags': ''
# 							}
# 							self.fetch_image(record, self.file_system)
# 						except Exception as e:
# 							log = f"{submission.id}, {sub}, Error Writing Post, {e}"
# 							print(log)
# 							continue
# 		except Exception as e:
# 			log = f"{sub}, Error Getting Posts For SubReddit, {e}"
# 			print(log)
#
# 	def collect_images_from_subreddit(self, subreddit_name, limit=10, save_directory="data/image"):
# 		subreddit = self.reddit.subreddit(subreddit_name)
# 		self.file_system.mkdir(save_directory, exist_ok=True)
#
# 		for submission in subreddit.hot(limit=limit):
# 			if submission.url.endswith(('.jpg', '.jpeg', '.png')):
# 				image_url = submission.url
# 				image_name = submission.title.replace(" ", "_").lower()
# 				image_extension = os.path.splitext(image_url)[1]
# 				image_path = os.path.join(save_directory, f"{image_name}{image_extension}")
#
# 				try:
# 					response = requests.get(image_url)
# 					response.raise_for_status()
# 					with open(image_path, "wb") as file:
# 						file.write(response.content)
# 					print(f"Saved image: {image_name}")
# 				except requests.exceptions.RequestException as e:
# 					print(f"Failed to download image: {image_name}")
# 					print(f"Error: {str(e)}")
#
#
# # Usage example
# if __name__ == "__main__":
# 	client_id = "YOUR_CLIENT_ID"
# 	client_secret = "YOUR_CLIENT_SECRET"
# 	user_agent = "YOUR_USER_AGENT"
#
# 	collector = RedditImageCollector(client_id, client_secret, user_agent)
# 	collector.collect_images_from_subreddit("pics", limit=10, save_directory="reddit_images")
