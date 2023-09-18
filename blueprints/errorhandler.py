from flask import Blueprint, render_template, current_app

ErrorHandler = Blueprint('ErrorHandler', __name__)

@ErrorHandler.app_errorhandler(404)
def e404(e):
    return render_template('errors/error.j2', errno=404, errtext="Not Found", errquote="Není žádná Antimemetická divize.", errlink="http://scp-cs.wikidot.com/your-last-first-day")

@ErrorHandler.app_errorhandler(401)
def e403(e):
    return render_template('errors/error.j2', errno=403, errtext="Unauthorized", errquote="Okamžitě ukončete své spojení a zůstaňte na místě. Najdeme vás.", errlink="http://scp-cs.wikidot.com/scp-6630")

@ErrorHandler.app_errorhandler(500)
def e500(e):
    return render_template('errors/error.j2', errno=500, errtext="Internal Server Error", errquote="[DATA VYMAZÁNA]", errlink="http://scp-cs.wikidot.com/sandrewswann-s-proposal")