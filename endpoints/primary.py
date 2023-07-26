from flask import Blueprint, render_template, redirect, url_for, request

from shared_code.background.message_broker import MessageBroker
from shared_code.services.primary_curation_service import PrimaryCurationService
from shared_code.services.secondary_curation_service import SecondaryCurationService

primary_curation_service: PrimaryCurationService = PrimaryCurationService("stage")
secondary_curation_service: SecondaryCurationService = SecondaryCurationService("curate")
message_broker: MessageBroker = MessageBroker(primary_curation_service, secondary_curation_service)

primary_bp = Blueprint('primary', __name__)


@primary_bp.route('/primary/')
def primary():
	try:
		record = primary_curation_service.get_next_record()[1]
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
		record = primary_curation_service.get_record_by_id(record_id=name, subreddit=subreddit)
		image_link = primary_curation_service.get_image_url(record_id=record.get('RowKey'), subreddit=record.get('PartitionKey'))
		return render_template('primary.jinja2', link=image_link, content=record, num_remaining=primary_curation_service.total_records)
	except Exception as e:
		return render_template('error.jinja2', error=e)


@primary_bp.route('/primary/curate/', methods=['POST'])
def curate():
	image_id = request.form['id']
	subreddit = request.form['subreddit']
	action = request.form['action']
	message_external = {"id": image_id, "partition": subreddit, "action": action, "state": "stage-to-curate"}
	message_internal = {"id": image_id, "partition": subreddit, "action": action, "state": "source-to-primary"}
	try:
		if action == 'accept':
			message_broker.send_message(message_internal, "source-to-primary")
			message_broker.send_message(message_external, "stage-to-curate")
			resp = {"redirect": url_for('primary.primary')}
			return resp
		else:
			message_broker.send_message(message_internal, "source-to-primary")
			resp = {"redirect": url_for('primary.primary')}
			return resp
	except Exception as e:
		return render_template('error.jinja2', error=e)


@primary_bp.route('/primary/reset/', methods=['POST'])
def reset():
	primary_curation_service.reset_records()
	resp = {"redirect": url_for('primary.primary')}
	return resp