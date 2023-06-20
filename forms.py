from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.widgets import TextArea
from wtforms.validators import EqualTo, Length, DataRequired

class LoginForm(FlaskForm):
    username = StringField('Uživatelské Jméno', validators=[DataRequired()])
    password = PasswordField('Heslo', validators=[DataRequired()])
    submit = SubmitField('Přihlásit')

class PasswordChangeForm(FlaskForm):
    password = PasswordField('Heslo', validators=[EqualTo('password_confirm', "Hesla se musí shodovat"), Length(6, message="Heslo musí mít 6 - 64 znaků")])
    password_confirm = PasswordField('Potvrdit heslo')
    submit = SubmitField('Změnit heslo')

class NewArticleForm(FlaskForm):
    title = StringField('Název', validators=[DataRequired()])
    translator = StringField('Překladatel')
    words = IntegerField('Počet slov', validators=[DataRequired()])
    bonus = IntegerField('Bonusové body', validators=[DataRequired()], default=0)
    link = StringField('Odkaz')
    submit = SubmitField('Odeslat')
