from flask import Blueprint, render_template, redirect, url_for, request

from shared_code.background.message_broker import MessageBroker
from shared_code.services.primary_curation_service import PrimaryCurationService

primary_curation_service: PrimaryCurationService = PrimaryCurationService("stage")
message_broker: MessageBroker = MessageBroker()

primary_bp = Blueprint('primary', __name__)


@primary_bp.route('/primary/')
def primary():
	try:
		record = primary_curation_service.get_next_record()

		if record is None:
			return render_template('error.jinja2', error="No more records to curate")

		else:
			name = record['id']
			subreddit = record['PartitionKey']
			return redirect(url_for('primary.primary_image', name=name, subreddit=subreddit))
	except StopIteration:
		return render_template('error.jinja2', error="No more records to curate")
	except Exception as e:
		return render_template('error.jinja2', error=f"An unknown error has occurred: {e}")


@primary_bp.route('/primary/image/<name>/<subreddit>', methods=['GET'])
def primary_image(name, subreddit):
	try:
		# primary_curation_service.get_num_remaining_records()
		record = primary_curation_service.get_record_by_id(record_id=name, subreddit=subreddit)
		image_link = primary_curation_service.get_image_url(record_id=record.get('RowKey'), subreddit=record.get('PartitionKey'))
		remaining = primary_curation_service.get_num_remaining_records()
		return render_template('primary.jinja2', link=image_link, content=record, num_remaining=remaining)
	except Exception as e:
		return render_template('error.jinja2', error=e)


@primary_bp.route('/primary/curate/', methods=['POST'])
def curate():
	image_id = request.form['id']
	subreddit = request.form['subreddit']
	action = request.form['action']
	try:
		if action == 'accept':
			message = {"id": image_id, "partition": subreddit, "action": action, "state": "stage-to-curate"}
			primary_curation_service.update_record(image_id, subreddit=subreddit, action=action)
			message_broker.send_message(message, "stage-to-curate")
			resp = {"redirect": url_for('primary.primary')}
			return resp
		else:
			primary_curation_service.update_record(image_id, subreddit=subreddit, action=action)
			resp = {"redirect": url_for('primary.primary')}
			return resp
	except Exception as e:
		return render_template('error.jinja2', error=e)
