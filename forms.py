from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, BooleanField
from wtforms.widgets import TextArea
from wtforms.validators import EqualTo, Length, DataRequired, url

class LoginForm(FlaskForm):
    username = StringField('Uživatelské Jméno', validators=[DataRequired()])
    password = PasswordField('Heslo', validators=[DataRequired()])
    submit = SubmitField('Přihlásit')

class PasswordChangeForm(FlaskForm):
    password = PasswordField('Heslo', validators=[EqualTo('password_confirm', "Hesla se musí shodovat"), Length(6, message="Heslo musí mít 6 - 64 znaků")])
    password_confirm = PasswordField('Potvrdit heslo')
    submit = SubmitField('Změnit heslo')

class NewArticleForm(FlaskForm):
    title = StringField('Název', validators=[DataRequired(message="Zadejte název článku")])
    translator = StringField('Překladatel')
    words = IntegerField('Počet slov', validators=[DataRequired(message="Zadejte počet slov")])
    bonus = IntegerField('Bonusové body', default=0)
    link = StringField('Odkaz', validators=[url(require_tld=True, message="Neplatný odkaz")])
    submit = SubmitField('Odeslat')

class EditArticleForm(NewArticleForm):
    pass

class NewUserForm(FlaskForm):
    nickname = StringField('Přezdívka', validators=[DataRequired()])
    wikidot = StringField('Wikidot ID', validators=[DataRequired()])
    discord = StringField('Discord ID')
    exempt = BooleanField('Počítat body')
    can_login = BooleanField('Vygenerovat heslo')
    submit = SubmitField('Přidat')

class EditUserForm(NewUserForm):
    nickname = StringField('Přezdívka', validators=[DataRequired()])
    wikidot = StringField('Wikidot ID', validators=[DataRequired()])
    discord = StringField('Discord ID')
    submit = SubmitField('Uložit')

class PasswordChangeForm(FlaskForm):
    pw = PasswordField('Heslo', validators=[DataRequired()])
    pw_confirm = PasswordField('Potvrzení hesla', validators=[DataRequired(), EqualTo('pw', message="Hesla se musí shodovat")])
    submit = SubmitField('Potvrdit')