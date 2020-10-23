from argtech import ws
from webservice import *

description=""

swagger = {
    "info":{
        "license": {
            "name": "GNU Lesser General Public License v3.0",
            "url": "https://www.gnu.org/licenses/lgpl-3.0.en.html"
        },
        "contact":{
            "email":"mark@arg.tech"
        }
    }
}

app = ws.build(title="PyASPIC", description=description, **swagger)
