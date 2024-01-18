# Copyright 2024, Battelle Energy Alliance, LLC All Rights Reserved

from flask import Blueprint, render_template

from parsnip.main.forms import UploadSnapshotForm

errors = Blueprint('errors', __name__)

@errors.app_errorhandler(403)
@errors.app_errorhandler(404)
@errors.app_errorhandler(500)
def errorHandler(error):
    uploadSnapshotForm = UploadSnapshotForm()
    # error.get_response provides header information
    # error.code is the error code (e.g., 404)
    # error.name is the error name (e.g., "Not Found")
    # error.description is the error description
    return render_template('error.html', error=error, uploadSnapshotForm=uploadSnapshotForm), error.code
