# Copyright 2023, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

from flask import Flask

def create_app(config_class):
    app = Flask(__name__,
                static_url_path=config_class.STATIC_URL_PATH,
                static_folder=config_class.STATIC_FOLDER,
                template_folder=config_class.TEMPLATE_FOLDER)
    # Set the rest of the configuration information
    app.config.from_object(config_class)

    from parsnip.main.routes import main
    from parsnip.errors.handlers import errors

    app.register_blueprint(main)
    app.register_blueprint(errors)

    return app
