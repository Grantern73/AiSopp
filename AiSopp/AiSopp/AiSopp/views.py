"""
Routes and views for the flask application.
"""
import os
from datetime import datetime
from flask import render_template, request, jsonify
from werkzeug.utils import secure_filename
from AiSopp import app
from AiSopp.get_country_from_ip import get_country_from_ip
from AiSopp.image_label import run_inference_on_image
import json
from PIL import Image
from resizeimage import resizeimage

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])
UPLOAD_FOLDER = 'uploads'
UPLOAD_FOLDER_MOBILE = 'mobile_uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_MOBILE'] = UPLOAD_FOLDER_MOBILE

@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='AiSopp',
        year=datetime.now().year,
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Kontakt',
        year=datetime.now().year,
        message='Kontakt og nyttige lenker'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='Om',
        year=datetime.now().year,
        message='Intelligent identifisering av Sopp'
    )

@app.route('/tips')
def tips():
    """Renders the tips page. """
    return render_template(
        'tips.html',
        title='Tips',
        message='Noen gode råd til soppsankere'
        )

@app.route('/mobile')
def mobile():
    """Renders the Mobile app info page. """
    return render_template('mobile.html', title='Mobil app', message='Mobil app til Android og Iphone er underveis')

@app.route('/explain')
def explain():
    """Renders the explain info page. """
    return render_template('explain.html', title='Forklaring', message='Hva forteller den deg og hvordan tolke resultatet')

@app.route('/admin')
def admin():
    """Renders the admin page."""
    return render_template(
        'admin.html',
        title='Administrasjon',
        year=datetime.now().year,
        message='Administrering av innhold'
    )

@app.route('/analyze', methods=['POST', 'GET'])
def analyze():
    """ Rest API for analyzing images """
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify(
                message='No file in request',
                filename='',
                timestamp=datetime.datetime.now()
                )
        file = request.files['file']
        if file.filename == '':
            return jsonify(
                message='Filetype not allowed, only jpg/jpeg are allowed',
                filename='',
                timestamp=datetime.datetime.now()
                )
        if file and allowed_file(file.filename):
            country = get_country_from_ip(request.remote_addr)
            #filename = secure_filename(file.filename)
            savepath = os.path.join(app.config['UPLOAD_FOLDER_MOBILE'], country)
            if not os.path.exists(savepath):
                os.makedirs(savepath)
            completesavepath = os.path.join(savepath, file.filename)
            file.save(completesavepath)
            file.close()
            with open(completesavepath, 'r+b') as f:
                with Image.open(f) as image:
                    w = image.width
                    h = image.height
                    r = w/h
                    nh = 399/r
                    cover = resizeimage.resize_cover(image, [399, int(nh)])
                    cover.save(completesavepath, image.format)
            
            predictions = run_inference_on_image(completesavepath)
           
            SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
            json_url = os.path.join(SITE_ROOT, "static/data", "sopp_no.json")
            data = json.load(open(json_url))
            result = []
            for latin, hitrate in predictions:
                soppres = None
                for sopp in data['sopp']:
                    if sopp['name'] == latin:
                        soppres = [latin, hitrate, sopp['local_name'], sopp['risk']]
                        result.append(soppres)
                        break   
                if soppres is None:
                    soppres = [latin, hitrate, '', '0']
                    result.append(soppres)

            return jsonify(
                message='OK',
                filename=file.filename,
                timestamp=datetime.datetime.now(),
                results=result
                )

@app.route('/upload', methods=['POST', 'GET'])
def do_upload():
    """Stores and Identifies the uploaded image."""

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return render_template(
                'index.html',
                status="Ingen file i request.files")
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return render_template(
                'index.html',
                status="Filtypen " + ext.lower() + " er ikke støttet, kun jpg/jpeg kan brukes.")

        if file and allowed_file(file.filename):
            country = get_country_from_ip(request.remote_addr)
            #filename = secure_filename(file.filename)
            savepath = os.path.join(app.config['UPLOAD_FOLDER'], country)
            if not os.path.exists(savepath):
                os.makedirs(savepath)
            completesavepath = os.path.join(savepath, file.filename)
            file.save(completesavepath)
            file.close()
            
            predictions = run_inference_on_image(completesavepath)
           
            SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
            json_url = os.path.join(SITE_ROOT, "static/data", "sopp_no.json")
            data = json.load(open(json_url))
            result = []
            for latin, hitrate in predictions:
                soppres = None
                for sopp in data['sopp']:
                    if sopp['name'] == latin:
                        soppres = [latin, hitrate, sopp['local_name'], sopp['risk']]
                        result.append(soppres)
                        break   
                if soppres is None:
                    soppres = [latin, hitrate, '', '0']
                    result.append(soppres)

            return render_template(
                'index.html',
                results=result)

@app.route('/oversikt/<filter>')
def oversikt(filter):
    # returner oversikt over alle soppene som er registrert i systemet.
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "static/data", "sopp_no.json")
    data = json.load(open(json_url))
    usefilter = checkfilter(filter)
    if not usefilter is 9:
        filtered_data = filtered(usefilter, data)
        return render_template('oversikt.html', status='ok', data=filtered_data, filter=filter)
    else:
        usefilter = "invalid"
        return render_template('oversikt.html', status = 'Ugyldig filter', data = [], filter=filter)

@app.route('/oversikt/<filter>/<searchstring>')
def search(filter, searchstring):
    # returnerer et søkeresultat basert på filter og søkestreng.
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "static/data", "sopp_no.json")
    data = json.load(open(json_url))
    usefilter = checkfilter(filter)
    stringsearch = searchstring
    if not usefilter is 9:
        filtered_data = filtered(usefilter, data)
        searchresult = searchdata(filtered_data, stringsearch)
        return render_template('oversikt.html', status='ok', data=searchresult, filter=filter)
    else:
        usefilter = "invalid"
        return render_template('oversikt.html', status = 'Ugyldig filter', data = [], filter=filter)

@app.route('/sopp/<param>')
def sopp(param):
    # hent data om sopp og presenter den på siden.
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "static/data", "sopp_no.json")
    data = json.load(open(json_url))

    result = []
    for sopp in data['sopp']:
        if sopp['name'] == param.replace("%20"," "):
            result = sopp
            break

    if len(result) > 0:
        return render_template(
            'sopp.html',
            title = result['name'],
            localname = result['local_name'],
            latin = result['name'],
            images = result['images'],
            risk = result['risk'],
            description = result['description'],
            locations = result['locations'],
            season = result['season'],
            usage = result['usage'],
            similarto = result['similarto'],
            year=datetime.now().year)
   
    
    return render_template(
        'sopp.html',
        title = param.replace("%20", " ") + " - Beskrivelse under arbeid",
        localname = param.replace("%20", " ") + " - Beskrivelse under arbeid",
        latin = "",
        images = ["dummysopp.jpg", "dummysopp.jpg", "dummysopp.jpg"],
        risk = "",
        description = "",
        locations = "",
        season = "",
        usage = "",
        similarto = "",
        year=datetime.now().year)


# TODO, separate these helper functions into one single file.
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def checkfilter(x):
     return {
        'all': -1,
        'edible': 0,
        'notedible': 1,
        'poisonous': 2,
    }.get(x, 9) 

def filtered(filter, data):
    if str(filter) == '-1':
        return data['sopp']

    items = []
    for sopp in data['sopp']:
        if sopp['risk'] == str(filter):
            items.append(sopp)

    return items

def searchdata(inputdata, stringvalue):
    res = []
    i = 0
    for d in inputdata:
        if d['local_name'].lower().find(stringvalue.lower()) == -1:
            i = i + 1
        else:
            res.append(d)

    return res
