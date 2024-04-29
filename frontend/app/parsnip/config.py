# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import os
import secrets

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(16))
    STATIC_FOLDER = 'web/static'
    STATIC_URL_PATH = ''
    TEMPLATE_FOLDER = 'web/templates'
    FLASK_DEBUG = True
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = False
