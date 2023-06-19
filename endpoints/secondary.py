from flask import Blueprint, render_template, redirect, url_for, request, jsonify

from shared_code.background.message_broker import MessageBroker
from shared_code.services.primary_curation_service import PrimaryCurationService
from shared_code.services.secondary_curation_service import SecondaryCurationService

secondary_bp = Blueprint('secondary', __name__)

secondary_curation_service: SecondaryCurationService = SecondaryCurationService("curationSecondary")

message_broker: MessageBroker = MessageBroker()


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
		record_id = record.get('id')
		subreddit = record.get('subreddit')
		thumbnail_path, azure_thumbnail, pil_thumbnail = secondary_curation_service.get_image_url(record_id=record_id, subreddit=subreddit)
		dense_captions: list[dict] = secondary_curation_service.get_dense_captions(name)
		relevant_tags: list[dict] = secondary_curation_service.get_relevant_tags(name)

		record['dense_captions'] = dense_captions
		record['tags'] = relevant_tags

		azure_caption = record.get('azure_caption')
		thumbnail_caption = record.get('caption')
		reddit_caption = f"{subreddit}, {record.get('title')}"


		return render_template('secondary.jinja2',
							   thumbnail_path=thumbnail_path,
							   thumbnail_caption=thumbnail_caption,
							   azure_thumbnail=azure_thumbnail,
							   azure_caption=azure_caption,
							   pil_thumbnail=pil_thumbnail,
							   reddit_caption=reddit_caption,
							   content=record,
							   num_remaining=0)
	except Exception as e:
		return render_template('error.jinja2', error=e)


@secondary_bp.route('/secondary/curate/', methods=['POST'])
def secondary_curate():
	image_id = request.form['id']
	subreddit = request.form['subreddit']
	action = request.form['action']
	additional_captions = request.form['additional_captions'].split(',')
	additional_tags = request.form['additional_tags'].split(',')
	pil_crop_accept = request.form['pil_crop_accept'] == 'true'
	reddit_caption = request.form['reddit_caption']
	azure_crop_accept = request.form['azure_crop_accept'] == 'true'
	azure_caption = request.form['azure_caption']
	smart_crop_accept = request.form['smart_crop_accept'] == 'true'
	smart_caption = request.form['smart_caption']
	best_caption = request.form['best_caption']

	try:
		secondary_curation_service.update_record(
			record_id=image_id,
			subreddit=subreddit,
			action=action,
			reddit_caption=reddit_caption,
			smart_caption=smart_caption,
			azure_caption=azure_caption,
			best_caption=best_caption,
			pil_crop_accept=pil_crop_accept,
			azure_crop_accept=azure_crop_accept,
			smart_crop_accept=smart_crop_accept,
			additional_captions=additional_captions,
			relevant_tags=additional_tags)

		resp = {"redirect": url_for('secondary.secondary')}
		return resp
	except Exception as e:
		print(e)
		return redirect(url_for('secondary.secondary'))


@secondary_bp.route('/secondary/analysis/', methods=['POST'])
def secondary_analysis():
	try:
		name = request.form["image_id"]
		subreddit = request.form['subreddit']
		primary_curation_service: PrimaryCurationService = PrimaryCurationService("curationPrimary")
		record = primary_curation_service.get_record_by_id(record_id=name, subreddit=subreddit)

		caption = record.get('caption')
		message: dict = {
			"image_id": name,
			"subreddit": subreddit,
			"action": "accept",
			"caption": caption,
		}
		message_broker.send_message(message)
		return jsonify({"success": True, "error": None, "redirect": url_for('secondary.secondary')})
	except Exception as e:
		return jsonify({"success": False, "error": e, "redirect": url_for('secondary.secondary')})
