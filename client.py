from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import Length, InputRequired, EqualTo
from operator import itemgetter
import requests, json

app = Flask(__name__, template_folder="./templates/")
app.config.update(dict(
    SECRET_KEY = "\xbf\xcf\xde\xee\xe8\xc1\x8c\\\xfd\xe6\\!t^(\x1c/\xc6l\xe1,\xc9#\xd7",
    WTF_CSRF_SECRET_KEY = "Uei\xc2&\x8a\x18.H\x87\xc5\x1d\xd1\xc8\xc3\xcf\xe5\xfft_\x8c:\x03r"
))

apiURLs = {
	"provinces": "http://0.0.0.0:3000/provinces",
	"lines": "http://0.0.0.0:3000/provinces/{provinceNumber}/lines",
	"directions": "http://0.0.0.0:3000/{provinceNumber}/lines/{lineNumber}/directions", 
	"route": "http://0.0.0.0:3000/{provinceNumber}/lines/{lineNumber}/directions/{direction}" ,
	"weather": "http://0.0.0.0:3000/weather/{latitude}/{longitude}"
}

########################################### FORMS ###########################################
class ProvinceLineForm(FlaskForm):
	provinces = requests.get(url=apiURLs["provinces"]).json()

	provinceChoices = []
	for p in provinces['entiteiten']:
		provinceChoices.append((p['entiteitnummer'], p['omschrijving']))

	provinceField = SelectField('', choices=provinceChoices, id="province")

	lineField = SelectField('', coerce=str, choices=[], id="line")

	directionField = SelectField('', coerce=str, choices=[], id="direction")

########################################### ROUTES ###########################################

@app.route('/')
def index():
	province_line_form = ProvinceLineForm()
	return render_template('index.html', province_line_form=province_line_form)

@app.route('/getLinesForProvince/<province>')
def getLinesForProvince(province):
	url = apiURLs["lines"].format(provinceNumber=province)
	apiData = requests.get(url=url).json()
	return apiData

@app.route('/getLineDirections/<province>/<line>')
def getLineDirections(province, line):
	url = apiURLs["directions"].format(provinceNumber=province, lineNumber=line)
	apiData = requests.get(url=url).json()
	return apiData

@app.route('/getLineRoute/<province>/<line>/<direction>')
def getLineRoute(province, line, direction):
	url = apiURLs["route"].format(provinceNumber=province, lineNumber=line, direction=direction)
	apiData = requests.get(url=url).json()
	return apiData

if __name__ == '__main__':
	app.run(host='0.0.0.0', port="5000")