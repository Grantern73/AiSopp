"""
Routes and views for the flask application.
"""
import os
from datetime import datetime
from flask import render_template, request
from werkzeug.utils import secure_filename
from AiSopp import app
from AiSopp.get_country_from_ip import get_country_from_ip
from AiSopp.image_label import run_inference_on_image
import json

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Intelligent identifisering av Sopp'
    )

@app.route('/admin')
def admin():
    """Renders the admin page."""
    return render_template(
        'admin.html',
        title='Administrasjon',
        year=datetime.now().year,
        message='Administrering av innhold'
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
        title = param + " - Beskrivelse under arbeid",
        localname = param + " - Beskrivelse under arbeid",
        latin = "",
        images = "dummysopp.jpg",
        risk = "",
        description = "",
        locations = "",
        season = "",
        usage = "",
        similarto = "",
        year=datetime.now().year)
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
