import sys, os, logging, subprocess, json
import tornado.ioloop
import tornado.web

APP_ROOT = os.path.dirname(os.path.realpath(__file__))
YSLOW = os.path.join(APP_ROOT, 'scripts/yslow.js')
HARDYHAR = os.path.join(APP_ROOT, 'scripts/har.js')
PHANTOMJS = os.path.join(APP_ROOT, 'node_modules/phantomjs/bin/phantomjs')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class BaseHandler(tornado.web.RequestHandler):
    def validateArgs(self, required):
        result = { 'success': True, 'missing_args': [] };
        for req in required:
            if req not in self.request.query_arguments:
                result['success'] = False;
                result['missing_args'].append(req);

        return result;


class YSlowHandler(BaseHandler):
    def get(self):
        validation = self.validateArgs(['url']);
        if validation['success'] == False:
            self.write("Missing required parameters " + ", ".join(validation['missing_args']));
        else:
            result = yslow(self.get_query_argument('url'));
            self.set_header("Content-Type", "application/json");
            self.write(result);

class HarHandler(BaseHandler):
    def get(self):
        validation = self.validateArgs(['url']);
        if validation['success'] == False:
            self.write("Missing required parameters " + ", ".join(validation['missing_args']));
        else:
            result = hardyhar(self.get_query_argument('url'));
            self.set_header("Content-Type", "application/json");
            self.write(result);

def yslow(url):
    try:
        f = subprocess.Popen([PHANTOMJS, YSLOW, "--info grade", url], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, shell=False)
        out = f.communicate()[0];
        return json.loads(out);
    except Exception, e:
        logging.fatal("Error parsing message nick: %s" %  e);

def hardyhar(url):
    try:
        f = subprocess.Popen([PHANTOMJS, "--web-security=false", HARDYHAR, url], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, shell=False)
        out = f.communicate()[0];
        return json.loads(out);
    except Exception, e:
        logging.fatal("Error parsing message nick: %s" %  e);

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/yslow", YSlowHandler),
        (r"/hardyhar", HarHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
