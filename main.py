import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import request
from flask import Flask
from flask import render_template


load_dotenv()

API_KEY = os.environ.get("COGMENTO_API_KEY")
SCHEMA_ID = os.environ.get("COGMENTO_SCHEMA_ID")
RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_KEY")
RECAPTCHA_SECRET = os.environ.get("RECAPTCHA_SECRET")

if not API_KEY or not SCHEMA_ID:
    raise Exception(
        "COGMENTO_API_KEY and COGMENTO_SCHEMA_ID are not available in the environment"
    )

BASE_URL = "https://api.cogmento.com/api/1"

app = Flask(__name__)


def headers():
    """
    Auth headers required for Cogmento API requests
    """
    return {
        "Authorization": f"Token {API_KEY}"
    }


def validate_recaptcha(response):
    """
    If applicable, validate the reCaptcha
    """
    res = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
            'secret': RECAPTCHA_SECRET,
            'response': response
        }
    )
    res = res.json()
    return res.get('success')


@app.route("/")
def home():
    """
    Render the initial screen. reCaptcha will be used if configured.
    """
    return render_template(
        'index.html',
        recaptcha_key=RECAPTCHA_SITE_KEY
    )


@app.post('/')
def collect():
    """
    Verified Credential collection.
    The details entered in the first screen are sent to Cogmento,
    creating a Contact record and an associated Deal. Then, a verified
    credential of the schema id configured above is generated and provided
    for collection
    """
    contact = {
        "first_name": request.form["first_name"],
        "last_name": request.form["last_name"],
        "email": request.form["email"],
        "phone": request.form["phone"],
    }
    if not contact["first_name"] or not contact["last_name"] or not contact["email"]:
        return render_template(
            'index.html',
            error="Name and email are required"
        )

    if RECAPTCHA_SECRET and RECAPTCHA_SITE_KEY and 'g-recaptcha-response' in request.form:
        recaptcha_ok = validate_recaptcha(request.form['g-recaptcha-response'])
        if not recaptcha_ok:
            return render_template('index.html', error="Please complete the reCaptcha")

    contact_respone = requests.post(
        f"{BASE_URL}/contacts/",
        json=contact,
        headers=headers(),
    ).json()
    contact_id = contact_respone.get("response", {}).get("result", {}).get("id")
    deal = {
        "title": "Cogmento partner",
        "contacts": [contact_id]
    }
    deal_response = requests.post(
        f"{BASE_URL}/deals/",
        json=deal,
        headers=headers(),
    ).json()
    deal_id = deal_response.get("response", {}).get("result", {}).get("id")
    vc = {
        "schema_id": SCHEMA_ID,
        "contact_id": contact_id,
        "model_spec": {
            "models": [
                {"id": deal_id, "name": "deal"}
            ]
        }
    }
    vc_response = requests.post(
        f"{BASE_URL}/ssi/issue/",
        json=vc,
        headers=headers(),
    ).json()

    vcresult = vc_response.get("response", {}).get("result", {})
    return render_template(
        'collect.html',
        qrdata=vcresult.get("qr"),
        pincode=vcresult.get("pin_code")
    )


@app.route('/present')
def present():
    """
    Show a presentation request QR code, which the user can scan and
    subsequently present their previously issued Verified Credential.
    If the presentation is verified this will be indicated in Cogmento CRM
    """
    presentation = requests.get(
        f"{BASE_URL}/ssi/presentation/schema/{SCHEMA_ID}/",
        headers=headers(),
    ).json()
    return render_template(
        "present.html",
        qrdata=presentation.get("qrCode"),
        expires_at=str(datetime.fromtimestamp(presentation.get('expiry')))
    )
