from flask import Blueprint, render_template, request, redirect, url_for

index_bp = Blueprint('index', __name__)


@index_bp.route('/')
def index():
	return render_template('index.jinja2')


@index_bp.route('/select_endpoint', methods=['GET', 'POST'])
def select_endpoint():
	endpoint = request.values['endpoint']
	if endpoint == 'primary':
		return redirect(url_for('primary.primary'))
	elif endpoint == 'secondary':
		return redirect(url_for('secondary.secondary'))
	return redirect('/')
