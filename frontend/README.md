# Running Parsnip

## Assumptions
* Docker and Bash (/bin/bash) already installed
* Current directory of the terminal is the root directory of repository

## Steps (in the terminal)
1. Run `./start_webServer.sh`
2. In the docker container prompt that appears:
    1. `cd app`
    2. `python3 app.py`


# Folder and File Structure

## Folder Structure
 * [&lt;root&gt;](#dir_root)
    - [app](#dir_app)
        * [flask_session](#dir_flask_session) \*
        * [parsnip](#dir_parsnip)
            - [errors](#dir_errors)
            - [main](#dir_main)
            - [web](#dir_web)
                * [static](#dir_static)
                    - [css](#dir_css)
                        * [images](#dir_images)
                    - [js](#dir_js)
                * [templates](#dir_templates)

\* denotes folders created by the server at runtime

## File Information

### <a name="dir_root"></a>&lt;root&gt;
* Dockerfile
    - Docker container configuration file
* README.md
    - This file.
* requirements.txt
    - Required python packages to be installed in the docker container
* start_webServer.sh
    - Script to start the docker container

### <a name="dir_app"></a>&lt;root&gt;/app
* app.py
    - Web Server initiation and program main function file

### <a name="dir_flask_session"></a>&lt;root&gt;/app/flask_session
Website session data files are stored here at runtime.

### <a name="dir_parsnip"></a>&lt;root&gt;/app/parsnip
* config.py
    - Class that contains configuration values
* \_\_init\_\_.py
    - Module initiation file
    - Contains function to create Flask App

### <a name="dir_errors"></a>&lt;root&gt;/app/parsnip/errors
* handlers.py
    - Initializes HTTP Error (e.g., 403, 404, 500) handlers for the server
* \_\_init\_\_.py
    - Empty module initiation file


### <a name="dir_main"></a>&lt;root&gt;/app/parsnip/main
* checkForMissingDependencies.py
    - Functions to help check for missing dependencies in the snapshot
* convert.py
    - Functions to help convert from snapshot to the Parsnip Intermediate Langugage Files
* forms.py
    - Form and validation classes used for website forms
* \_\_init\_\_.py
    - Empty module initiation file
* routes.py
    - Website request processing and routing rules
    - Utility functions to use within jinja2 web templates
* utils.py
    - Utility functions

### <a name="dir_web"></a>&lt;root&gt;/app/parsnip/web
Other website resouces (i.e., static and page templates).

### <a name="dir_static"></a>&lt;root&gt;/app/parsnip/web/static
Static websites resources.

### <a name="dir_css"></a>&lt;root&gt;/app/parsnip/web/static/css
Static CSS files.

### <a name="dir_images"></a>&lt;root&gt;/app/parsnip/web/static/css/images
Static image files for CSS resources.

### <a name="dir_js"></a>&lt;root&gt;/app/parsnip/web/static/js
Static Javascript files.

### <a name="dir_templates"></a>&lt;root&gt;/app/parsnip/web/templates
* bitfields.html
    - Page template to view and edit bitfields.
* config.html
    - Page template to view and edit overall parser configuration.
* enums.html
    - Page template to view and edit enums.
* error.html
    - Server HTTP Error page.
* fields.html
    - Page template to view and edit object fields.
* index.html
    - Home page.
    - Displays basic instructions.
* layout.base
    - Base template that is used by other templates (provides overall page structure)
* macros.j2
    - jinja2 macros that can be used by multiple pages
* objects.html
    - Page template to view and edit objects.
* review.html
    - Page template to view errors encountered while reviewing snapshots for issues.
* switches.html
    - Page template to view and edit switches (i.e., choices).