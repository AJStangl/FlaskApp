from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap

from shared_code.services.azure_caption_process import AzureCaption
from shared_code.services.secondary_curation_service import SecondaryCurationService
from shared_code.services.primary_curation_service import CurationService

primary_curation_service: CurationService = CurationService()

secondary_curation_service: SecondaryCurationService = SecondaryCurationService()

azure_caption: AzureCaption = AzureCaption()

app = Flask(__name__)

Bootstrap(app)


@app.route('/')
def index():
	return render_template("index.jinja2")


@app.route('/primary')
def primary():
	primary_curation_service.reset()
	try:
		record = primary_curation_service.get_next_record()
		if record is None:
			return render_template('error.jinja2', error="No more records to process")
		return redirect(url_for('primary_image', name=record['id']))
	except Exception:
		return render_template('error.jinja2', error="An error has happened, woops")


@app.route('/primary/image/<name>', methods=['GET'])
def primary_image(name):
	record = primary_curation_service.get_record_by_id(name)
	image_link = primary_curation_service.get_image_url(record)
	return render_template('primary.jinja2', link=image_link, content=record,
						   num_remaining=primary_curation_service.get_num_remaining_records())


@app.route('/primary/tag/<name>', methods=['POST'])
def tag(name):
	record = primary_curation_service.get_record_by_id(name)
	tags = request.form['tags']
	tags.split(',')
	record['tags'] = tags
	primary_curation_service.update_record_tag(record)
	image_link = primary_curation_service.get_image_url(record)
	return render_template('primary.jinja2', link=image_link, content=record,
						   num_remaining=primary_curation_service.get_num_remaining_records())


@app.route('/primary/curate/', methods=['POST'])
def curate():
	image_id = request.form['id']
	action = request.form['action']
	caption = request.form['caption']
	try:
		if action == 'accept':
			azure_caption.run_image_process(image_id)
			primary_curation_service.update_record(image_id, action, caption, [], [])
			record = primary_curation_service.get_record_by_id(image_id)
			secondary_curation_service.add_new_record(record)
		else:
			primary_curation_service.update_record(image_id, action, caption, [], [])

		record = primary_curation_service.get_next_record()

		return {
			'success': True,
			'message': 'Record Updated',
			'name': f'{record["id"]}'
		}
	except Exception as e:
		print(e)
		return redirect(url_for('primary'))


@app.route('/secondary')
def secondary():
	secondary_curation_service.reset()
	try:
		record = secondary_curation_service.get_next_record()
		if record is None:
			return render_template('error.jinja2', error="No more records to process")
		return redirect(url_for('secondary_image', name=record['id']))
	except Exception:
		return render_template('error.jinja2', error="An error has happened, woops")


@app.route('/secondary/image/<name>', methods=['GET'])
def secondary_image(name):
	record: dict = secondary_curation_service.get_record_by_id(name)
	dense_captions: list[dict] = secondary_curation_service.get_dense_captions(name)
	relevant_tags: list[dict] = secondary_curation_service.get_relevant_tags(name)
	if record is None:
		return secondary_image(secondary_curation_service.get_next_record()['id'])
	image_link = secondary_curation_service.get_image_url(record)

	record['dense_captions'] = dense_captions
	record['tags'] = relevant_tags

	return render_template('secondary.jinja2', link=image_link, content=record,
						   num_remaining=secondary_curation_service.get_num_remaining_records())


@app.route('/secondary/curate/', methods=['POST'])
def secondary_curate():
	image_id = request.form['id']
	action = request.form['action']
	caption = request.form['caption']
	additional_captions = request.form['additional_captions'].split(',')
	additional_tags = request.form['additional_tags'].split(',')
	try:
		secondary_curation_service.update_record(image_id, action, caption, additional_captions, additional_tags)
		record = secondary_curation_service.get_next_record()
		return {
			'success': True,
			'message': 'Record Updated',
			'name': f'{record["id"]}'
		}
	except Exception as e:
		print(e)
		return redirect(url_for('secondary'))


@app.route('/secondary/analysis/', methods=['POST'])
def secondary_analysis():
	image_id = request.form['id']
	try:
		out = azure_caption.run_image_process(image_id)
		return {'success': True, 'message': 'Record Updated', 'name': f'{image_id}', 'out': out}
	except Exception as e:
		print(e)
		return redirect(url_for('secondary'))


if __name__ == '__main__':
	app.run()
