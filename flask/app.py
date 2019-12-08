import os, sys, traceback, io
from contextlib import contextmanager
from flask import Flask, render_template, flash, redirect
from flask import session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.widgets import TextArea

sys.path.append(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                ".."))
from main import run_source

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'development key'

class EditorForm(FlaskForm):
    program = StringField('program', widget=TextArea())
    submit = SubmitField('Run')

@contextmanager
def redirect():
    stdout = sys.stdout
    try:
        new_out = io.StringIO()
        sys.stdout = new_out
        yield new_out
    finally:
        sys.stdout = stdout

@app.route('/', methods=['GET', 'POST'])
def program():
    form = EditorForm()
    if form.validate_on_submit():
        # Remove previous result
        session.pop('_flashes', None)
        output = None
        try:
            with redirect() as out:
                output = str(run_source(form.program.data))
                output = out.getvalue() + output
        except:
            output = traceback.format_exc()
        for l in output.splitlines():
            flash(l)
        # Don't redirect here, so that form data is kept
    return render_template('index.html', title='LispALike',
                           form=form)
