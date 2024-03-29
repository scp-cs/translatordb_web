from typing import Any
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, BooleanField, ValidationError
from wtforms.validators import EqualTo, Length, DataRequired, url
from flask import flash

class FlaskFormEx(FlaskForm):
    def validate_and_flash(self) -> bool:
        """
        Validates the form and flashes all validation errors.
        Returns the result of validate_on_submit
        """
        if not self.validate_on_submit():
            for e in self.errors.values():
                flash(e[0], category="error")
            return False
        return True

class DiscordID():
    def __call__(self, form, field) -> Any:
        if len(field.data) not in [18, 19]:
            raise ValidationError('Discord ID musí mít 18 nebo 19 znaků')
        try:
            a = int(field.data)
        except ValueError:
            raise ValidationError('Discord ID může obsahovat pouze číslice')

class LoginForm(FlaskFormEx):
    username = StringField('Uživatelské Jméno', validators=[DataRequired()])
    password = PasswordField('Heslo', validators=[DataRequired()])
    submit = SubmitField('Přihlásit')

class PasswordChangeForm(FlaskFormEx):
    password = PasswordField('Heslo', validators=[EqualTo('password_confirm', "Hesla se musí shodovat"), Length(6, message="Heslo musí mít 6 - 64 znaků")])
    password_confirm = PasswordField('Potvrdit heslo')
    submit = SubmitField('Změnit heslo')

class NewArticleForm(FlaskFormEx):
    title = StringField('Název', validators=[DataRequired(message="Zadejte název článku")])
    translator = StringField('Překladatel')
    words = IntegerField('Počet slov', validators=[DataRequired(message="Zadejte počet slov")])
    bonus = IntegerField('Bonusové body', default=0)
    link = StringField('Odkaz', validators=[url(require_tld=True, message="Neplatný odkaz")])
    submit = SubmitField('Odeslat')

class EditArticleForm(NewArticleForm):
    pass

class NewUserForm(FlaskFormEx):
    nickname = StringField('Přezdívka', validators=[DataRequired()])
    wikidot = StringField('Wikidot ID', validators=[DataRequired()])
    discord = StringField('Discord ID', validators=[DiscordID()])
    can_login = BooleanField('Vygenerovat heslo')
    submit = SubmitField('Přidat')

class EditUserForm(NewUserForm):
    nickname = StringField('Přezdívka', validators=[DataRequired()])
    wikidot = StringField('Wikidot ID', validators=[DataRequired()])
    discord = StringField('Discord ID', validators=[DiscordID()])
    submit = SubmitField('Uložit')

class PasswordChangeForm(FlaskFormEx):
    pw = PasswordField('Heslo', validators=[DataRequired()])
    pw_confirm = PasswordField('Potvrzení hesla', validators=[DataRequired(), EqualTo('pw', message="Hesla se musí shodovat")])
    submit = SubmitField('Potvrdit')