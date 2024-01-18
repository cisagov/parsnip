# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

class Config:
    SECRET_KEY = '4a5e281c1993a110e86cddf056c7a182'
    STATIC_FOLDER = 'web/static'
    STATIC_URL_PATH = ''
    TEMPLATE_FOLDER = 'web/templates'
    FLASK_DEBUG = True
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = False
