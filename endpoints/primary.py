from flask import Blueprint, render_template, redirect, url_for, request

from shared_code.services.azure_caption_process import AzureCaption
from shared_code.services.primary_curation_service import PrimaryCurationService
from shared_code.services.secondary_curation_service import SecondaryCurationService

primary_curation_service: PrimaryCurationService = PrimaryCurationService("curationPrimary")
secondary_curation_service: SecondaryCurationService = SecondaryCurationService("curationSecondary")
azure_caption: AzureCaption = AzureCaption()

primary_bp = Blueprint('primary', __name__)


@primary_bp.route('/primary/')
def primary():
	try:
		record = primary_curation_service.get_next_record()
		if record is None:
			return render_template('error.jinja2', error="No more records to process")

		name = record['id']
		subreddit = record['subreddit']
		return redirect(url_for('primary.primary_image', name=name, subreddit=subreddit))

	except Exception as e:
		return render_template('error.jinja2', error=e)


@primary_bp.route('/primary/image/<name>/<subreddit>', methods=['GET'])
def primary_image(name, subreddit):
	try:
		record = primary_curation_service.get_record_by_id(record_id=name, subreddit=subreddit)
		image_link = primary_curation_service.get_image_url(record_id=record.get('id'), subreddit=record.get('subreddit'))
		return render_template('primary.jinja2', link=image_link, content=record, num_remaining=primary_curation_service.get_num_remaining_records())
	except Exception as e:
		return render_template('error.jinja2', error=e)


@primary_bp.route('/primary/curate/', methods=['POST'])
def curate():
	image_id = request.form['id']
	subreddit = request.form['subreddit']
	action = request.form['action']
	caption = request.form['caption']
	try:
		if action == 'accept':
			azure_caption.run_image_process(image_id)
			primary_curation_service.update_record(image_id, subreddit=subreddit, action=action, caption=caption, additional_captions=[], relevant_tags=[])
			record = primary_curation_service.get_record_by_id(record_id=image_id, subreddit=subreddit)
			secondary_curation_service.add_new_entry(record)
			azure_caption.run_analysis(image_id=image_id)
			resp = {"redirect": url_for('primary.primary')}
			return resp
		else:
			primary_curation_service.update_record(image_id, subreddit=subreddit, action=action, caption=caption, additional_captions=[], relevant_tags=[])
			resp = {"redirect": url_for('primary.primary')}
			return resp
	except Exception as e:
		return render_template('error.jinja2', error=e)
