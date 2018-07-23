from flask import Blueprint, abort, render_template
from jinja2 import TemplateNotFound

showcase = Blueprint('showcase', __name__,
                        template_folder='showcase')

@showcase.route('/showcase')
@showcase.route('/showcase/')
def showcase():
    return render_template('index.html')
