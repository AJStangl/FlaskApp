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
		self.current_record = None

	def get_next_record(self):
		if self.current_record is None:
			self.current_record = next(self.records_to_process)
		else:
			self.current_record = next(self.records_to_process)
		return self.current_record

	def get_data_frame(self):
		files = self.file_storage.ls("/data/parquet")[0:100]
		data = []
		for file in tqdm(files, total=len(files), desc=":: Reading Files"):
			temp = pandas.read_parquet(f"{file}", engine="pyarrow", filesystem=self.file_storage)
			if temp.shape[0] != 1:
				continue
			foo = temp.to_dict(orient='records')[0]
			try:
				if foo['curated'] and foo['approved']:
					continue
				if foo['curated'] and not foo['approved']:
					continue
				else:
					data.append(foo)
			except Exception as e:
				continue
		return pandas.DataFrame(data=data)

	def update_record(self, record_id, action):
		record = self.current_record
		if record['id'] != record_id:
			raise Exception("Record Ids Do Not Match")
		if action == "accept":
			record['curated'] = True
			record['accept'] = True
		else:
			record['curated'] = True
			record['accept'] = False
		out_df = pandas.DataFrame(data=[record])
		out_df.to_parquet(f"/data/parquet/{record['id']}.parquet", engine="pyarrow", filesystem=self.file_storage)

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


@app.route('/refresh/', methods=['GET', 'POST'])
def refresh():
	curation_service.data_frame = curation_service.get_data_frame()
	curation_service.data_frame_filtered = curation_service.data_frame.where(~curation_service.data_frame['curated']).dropna()
	curation_service.records_to_process = iter(curation_service.data_frame_filtered.to_dict(orient='records'))
	return render_template('home.jinja2', content=request.data)


if __name__ == '__main__':
	app.run()