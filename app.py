from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap

from shared_code.services.curation_service import CurationService

curation_service = CurationService()

app = Flask(__name__)

Bootstrap(app)


@app.route('/')
def index():
	curation_service.reset()
	record = curation_service.get_next_record()
	return redirect(url_for('image', name=record['id']))


@app.route('/image/<name>', methods=['GET'])
def image(name):
	record = curation_service.get_record_by_id(name)
	image_link = curation_service.get_image_url(record)
	return render_template('home.jinja2', link=image_link, content=record, num_remaining=curation_service.get_num_remaining_records())


@app.route('/tag/<name>', methods=['POST'])
def tag(name):
	record = curation_service.get_record_by_id(name)
	tags = request.form['tags']
	tags.split(',')
	record['tags'] = tags
	curation_service.update_record_tag(record)
	image_link = curation_service.get_image_url(record)
	return render_template('home.jinja2', link=image_link, content=record, num_remaining=curation_service.get_num_remaining_records())


@app.route('/curate/', methods=['POST'])
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
		return redirect(url_for('index'))


if __name__ == '__main__':
	app.run()
