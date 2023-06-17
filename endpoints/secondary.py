from flask import Blueprint, render_template, redirect, url_for, request

from shared_code.services.secondary_curation_service import SecondaryCurationService

secondary_bp = Blueprint('secondary', __name__)

secondary_curation_service: SecondaryCurationService = SecondaryCurationService("curationSecondary")


@secondary_bp.route('/secondary/')
def secondary():
	try:
		record = secondary_curation_service.get_next_record()
		if record is None:
			return render_template('error.jinja2', error="No more records to process")

		name = record['id']
		subreddit = record['subreddit']
		return redirect(url_for('secondary.secondary_image', name=name, subreddit=subreddit))

	except Exception as e:
		return render_template('error.jinja2', error=e)


@secondary_bp.route('/secondary/image/<name>/<subreddit>', methods=['GET'])
def secondary_image(name, subreddit):
	try:
		record = secondary_curation_service.get_record_by_id(record_id=name, subreddit=subreddit)
		image_link = secondary.get_image_url(record_id=record.get('id'), subreddit=record.get('subreddit'))
		dense_captions: list[dict] = secondary_curation_service.get_dense_captions(name)
		relevant_tags: list[dict] = secondary_curation_service.get_relevant_tags(name)

		record['dense_captions'] = dense_captions
		record['tags'] = relevant_tags

		return render_template('secondary.jinja2',
							   link=image_link,
							   content=record,
							   num_remaining=secondary_curation_service.get_num_remaining_records())
	except Exception as e:
		return render_template('error.jinja2', error=e)


@secondary_bp.route('/secondary/curate/', methods=['POST'])
def secondary_curate():
	image_id = request.form['id']
	subreddit = request.form['subreddit']
	action = request.form['action']
	caption = request.form['caption']
	additional_captions = request.form['additional_captions'].split(',')
	additional_tags = request.form['additional_tags'].split(',')
	try:
		secondary_curation_service.update_record(
			record_id=image_id,
			subreddit=subreddit,
			action=action,
			caption=caption,
			additional_captions=additional_captions,
			relevant_tags=additional_tags)

		resp = {"redirect": url_for('secondary.secondary')}
		return resp
	except Exception as e:
		print(e)
		return redirect(url_for('secondary.secondary'))


@secondary_bp.route('/secondary/analysis/', methods=['POST'])
def secondary_analysis():
	image_id = request.form['id']
	try:
		return {'success': True, 'message': 'Record Updated', 'name': f'{image_id}', 'out': "Not implemented"}
	except Exception as e:
		print(e)
		return redirect(url_for('secondary'))