from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap

from shared_code.services.secondary_curation_service import SecondaryCurationService
from shared_code.services.primary_curation_service import CurationService

primary_curation_service: CurationService = CurationService()

secondary_curation_service: SecondaryCurationService = SecondaryCurationService()

app = Flask(__name__)

Bootstrap(app)


@app.route('/')
def index():
	return render_template("index.jinja2")


@app.route('/primary')
def primary():
	primary_curation_service.reset()
	record = primary_curation_service.get_next_record()
	return redirect(url_for('primary_image', name=record['id']))


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
		primary_curation_service.update_record(image_id, action, caption)
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
	record = secondary_curation_service.get_next_record()
	return redirect(url_for('secondary_image', name=record['id']))


@app.route('/secondary/image/<name>', methods=['GET'])
def secondary_image(name):
	record: dict = secondary_curation_service.get_record_by_id(name)
	if record is None:
		return secondary_image(secondary_curation_service.get_next_record()['id'])
	image_link = secondary_curation_service.get_image_url(record)
	return render_template('secondary.jinja2', link=image_link, content=record,
						   num_remaining=secondary_curation_service.get_num_remaining_records())


@app.route('/secondary/curate/', methods=['POST'])
def secondary_curate():
	image_id = request.form['id']
	action = request.form['action']
	caption = request.form['caption']
	try:
		secondary_curation_service.update_record(image_id, action, caption)
		record = secondary_curation_service.get_next_record()
		return {
			'success': True,
			'message': 'Record Updated',
			'name': f'{record["id"]}'
		}
	except Exception as e:
		print(e)
		return redirect(url_for('secondary'))


if __name__ == '__main__':
	app.run()
