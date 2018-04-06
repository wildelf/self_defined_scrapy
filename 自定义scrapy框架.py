#_author: Administrator
#date: 2018/4/7

from twisted.web.client import getPage
from twisted.internet import defer
from twisted.internet import reactor
import queue
class Request:
    def __init__(self,url,callback):
        self.url = url
        self.callback = callback

class ChoutiSpider:
    name = 'chouti'

    def start_request(self):
        start_url = ['http://www.baidu.com','http://www.bing.com']
        for url in start_url:
            yield Request(url,self.parse)

    def parse(self,response):
        print(response.url)

Q = queue.Queue()

class HttpResponse:
    def __init__(self,url,request,content):
        self.url = url
        self.request = request
        self.content = content


class Engine:
    def __init__(self):
        self._close = None
        self.max = 5
        self.crawling = []

    def get_response_callback(self,content,request):

        self.crawling.remove(request)

        response = HttpResponse(request.url,request,content)
        result = request.callback(response)

        import types
        if isinstance(result,types.GeneratorType):
            for req in result:
                Q.put(req)

        if Q.qsize() == 0 and len(self.crawling) == 0:
            self._close.callback(None)
            return

    def _next_request(self):


        if len(self.crawling) >= self.max:
            return
        while len(self.crawling) < self.max:
            try:
                req = Q.get(block=False)#取出request对象

                self.crawling.append(req)#添加到正在执行中
                d = getPage(req.url.encode('utf-8'))

                d.addCallback(self.get_response_callback,req)

                d.addCallback(self._next_request)
            except Exception as e:
                print(e)

                return

    @defer.inlineCallbacks
    def crawl(self,spider):
        start_request = iter(spider.start_request())

        while True:
            try:
                request = next(start_request)
                Q.put(request)

            except StopIteration as e:
                break

        self._next_request()
        self._close = defer.Deferred()
        yield self._close

_visited = set()

spider = ChoutiSpider()

engine = Engine()
d = engine.crawl(spider)
_visited.add(d)

dd = defer.DeferredList(_visited)
dd.addBoth(lambda _:reactor.stop())
reactor.run()