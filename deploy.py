# -*- coding: utf-8 -*-
"""

@author: Mirko Ruether
"""

from mcrecipegraph.web.app import app, flask_app # pylint: disable=unused-import

if __name__ == '__main__':
    app.run_server(debug=True, port=5000)
