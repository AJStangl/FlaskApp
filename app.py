import json

import pandas
from tqdm import tqdm
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from shared_code.azure_storage.azure_file_system_adapter import AzureFileStorageAdapter


class CurationService:
	def __init__(self):
		self.file_storage = self.get_file_storage()
		self.data_frame = self.get_data_frame()
		self.data_frame_filtered = self.data_frame.where(~self.data_frame['curated']).dropna()
		self.records_to_process = iter(self.data_frame_filtered.to_dict(orient='records'))

	def get_next_record(self):
		return next(self.records_to_process)

	def get_data_frame(self):
		files = self.file_storage.ls("/data/parquet")[0:100]
		data = []
		for file in tqdm(files, total=len(files), desc=":: Reading Files"):
			temp = pandas.read_parquet(f"{file}", engine="pyarrow", filesystem=self.file_storage)
			foo = temp.to_dict(orient='records')[0]
			if foo['curated'] and foo['approved']:
				continue
			if foo['curated'] and not foo['approved']:
				continue
			else:
				data.append(foo)
		return pandas.DataFrame(data=data)

	def update_record(self, record_id, action):
		record = self.data_frame.where(self.data_frame['id'] == record_id).dropna().to_dict(orient='records')[0]
		if action == "accept":
			record['curated'] = True
			record['accept'] = True
		else:
			record['curated'] = True
			record['accept'] = False
		self.data_frame.to_parquet(f"/data/parquet/{record['id']}.parquet", engine="pyarrow", filesystem=self.file_storage)

	def get_file_storage(self):
		return AzureFileStorageAdapter("data").get_file_storage()


curation_service = CurationService()

app = Flask(__name__)

Bootstrap(app)


@app.route('/')
def index():
	record = curation_service.get_next_record()
	image = "https://ajdevreddit.blob.core.windows.net/" + record['path']
	return render_template('home.jinja2', title='Curate', content=record, link=image)


@app.route('/curate/', methods=['GET', 'POST'])
def curate():
	image_id = request.form['id']
	action = request.form['action']
	curation_service.update_record(image_id, action)
	return render_template('home.jinja2', content=request.data)


if __name__ == '__main__':
	app.run()