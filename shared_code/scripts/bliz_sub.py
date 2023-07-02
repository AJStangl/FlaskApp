if __name__ == '__main__':
	from tqdm import tqdm
	from shared_code.azure_storage.tables import TableAdapter, TableClient

	all_subs = ['AesPleasingAsianGirls',
				'AmIhotAF',
				'Amicute',
				'AsianInvasion',
				'AsianOfficeLady',
				'CityPorn',
				'CollaredDresses',
				'DLAH',
				'Dresses',
				'DressesPorn',
				'EarthPorn',
				'HotGirlNextDoor',
				'Ifyouhadtopickone',
				'KoreanHotties',
				'PrettyGirls',
				'SFWNextDoorGirls',
				'SFWRedheads',
				'SlitDresses',
				'TrueFMK',
				'WomenInLongDresses',
				'amihot',
				'bathandbodyworks',
				'celebrities',
				'cougars_and_milfs_sfw',
				'fatsquirrelhate',
				'gentlemanboners',
				'hotofficegirls',
				'itookapicture',
				'memes',
				'mildlypenis',
				'prettyasiangirls',
				'realasians',
				'selfies',
				'sexygirls',
				'sfwpetite',
				'spaceporn',
				'tightdresses',
				'trippinthroughtime',
				'wallstreetbets']

	table_client: TableClient = TableAdapter().get_table_client("curationSecondary")
	memes = list(table_client.query_entities("subreddit eq 'trippinthroughtime'"))
	for meme in tqdm(memes, total=len(memes)):
		meme['thumbnail_accept'] = False
		meme['thumbnail_curated'] = True
		table_client.upsert_entity(meme)
