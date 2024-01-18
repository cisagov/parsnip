# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

from parsnip import create_app
from parsnip.config import Config

from flask_session import Session

app = create_app(Config)
Session(app)

if '__main__' == __name__:
    app.run(debug=True, host='0.0.0.0')
