from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap

from shared_code.services.secondary_curation_service import SecondLayerCurationService
from shared_code.services.curation_service import CurationService

curation_service = CurationService()

secondary_curation_service = SecondLayerCurationService()

app = Flask(__name__)

Bootstrap(app)


@app.route('/primary')
def primary():
	curation_service.reset()
	record = curation_service.get_next_record()
	return redirect(url_for('primary_image', name=record['id']))


@app.route('/primary/image/<name>', methods=['GET'])
def image(name):
	record = curation_service.get_record_by_id(name)
	image_link = curation_service.get_image_url(record)
	return render_template('primary.jinja2', link=image_link, content=record, num_remaining=curation_service.get_num_remaining_records())


@app.route('/primary/tag/<name>', methods=['POST'])
def tag(name):
	record = curation_service.get_record_by_id(name)
	tags = request.form['tags']
	tags.split(',')
	record['tags'] = tags
	curation_service.update_record_tag(record)
	image_link = curation_service.get_image_url(record)
	return render_template('primary.jinja2', link=image_link, content=record, num_remaining=curation_service.get_num_remaining_records())


@app.route('/primary/curate/', methods=['POST'])
def curate():
	image_id = request.form['id']
	action = request.form['action']
	caption = request.form['caption']
	try:
		curation_service.update_record(image_id, action, caption)
		record = curation_service.get_next_record()
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
	record = secondary_curation_service.get_record_by_id(name)
	image_link = secondary_curation_service.get_image_url(record)
	return render_template('secondary.jinja2', link=image_link, content=record, num_remaining=secondary_curation_service.get_num_remaining_records())


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
