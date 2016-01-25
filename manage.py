import sys, os, logging, subprocess, json
import tornado.ioloop
import tornado.web

APP_ROOT = os.path.dirname(os.path.realpath(__file__))
YSLOW = os.path.join(APP_ROOT, 'scripts/yslow.js')
HARDYHAR = os.path.join(APP_ROOT, 'scripts/har.js')
PHANTOMJS = os.path.join(APP_ROOT, 'node_modules/phantomjs/bin/phantomjs')

class BaseHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json");
        self.set_status(404)
        self.write(json.dumps({'success': 'false', 'message': 'Nothing to GET. Only POST supported'}));

    def validateArgs(self, required):
        result = { 'success': True, 'missing_args': [] };
        for req in required:
            if req not in self.request.query_arguments:
                result['success'] = False;
                result['missing_args'].append(req);
                result['message'] = "Missing arguments: " + " ,".join(result['missing_args']);
        return result;

    def handleResult(self, result):
        if result['success'] == False:
            self.returnFailure(json.dumps(result));
        else:
            self.returnSuccess(result['data']);

    def returnSuccess(self, body):
        self.set_header("Content-Type", "application/json");
        self.set_status(200);
        self.write(body);

    def returnFailure(self, body):
        self.set_header("Content-Type", "application/json");
        self.set_status(400);
        self.write(body);

    def returnMissingArgs(self, body):
        self.set_header("Content-Type", "applicaion/json");
        self.set_status(422);
        self.write(body);

class RootHandler(BaseHandler):
    def get(self):
        self.returnSuccess("Hello, world")

class YSlowHandler(BaseHandler):
    def post(self):
        validation = self.validateArgs(['url']);
        if validation['success'] == False:
            self.returnFailure(json.dumps(validation));
        else:
            result = yslow(self.get_query_argument('url'), ('--info grade'));
            self.handleResult(result);

class HarHandler(BaseHandler):
    def post(self):
        validation = self.validateArgs(['url']);
        if validation['success'] == False:
            self.returnFailure(json.dumps(validation));
        else:
            result = hardyhar(self.get_query_argument('url'));
            self.handleResult(result);

def yslow(url, *args):
    command = [PHANTOMJS, YSLOW];
    command.extend(args);
    command.append(url);

    result = {
            'success':  True,
            'data': {},
            }
    try:
        f = subprocess.Popen(command, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, shell=False)
        out = f.communicate()[0];
        result['data'] = json.loads(out);
        return result;
    except Exception, e:
        result['success'] = False;
        result['data'] = "Error parsing message: " + e.message;
        result['command'] = " ".join(command);
        return result;

def hardyhar(url, *args):
    command = [PHANTOMJS, "--web-security=false", HARDYHAR];
    command.extend(args);
    command.append(url);

    result = {
            'success':  True,
            'data': {},
            }
    try:
        f = subprocess.Popen([PHANTOMJS, "--web-security=false", HARDYHAR, url], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, shell=False)
        out = f.communicate()[0];
        result['data'] = json.loads(out);
        return result;
    except Exception, e:
        result['success'] = False;
        result['data'] = "Error parsing message: " + e.message;
        result['command'] = " ".join(command);
        return result;

def make_app():
    return tornado.web.Application([
        (r"/", RootHandler),
        (r"/yslow", YSlowHandler),
        (r"/hardyhar", HarHandler),
    ], autoreload=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
