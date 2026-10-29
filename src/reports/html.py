"""Small metadata-only DOM. Never returns images or downloads embedded content."""
from html.parser import HTMLParser
from urllib.parse import urljoin

class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children, self.parts = [], []
    def all(self, tag=None):
        for child in self.children:
            if tag is None or child.tag == tag: yield child
            yield from child.all(tag)
    def text(self):
        return ' '.join(' '.join(self.parts).split())
    def has(self, cls): return cls in self.attrs.get('class','').split()

class DOM(HTMLParser):
    def __init__(self, payload):
        super().__init__(convert_charrefs=True)
        self.root = Node(); self.stack=[self.root]
        self.feed(payload.decode('utf-8','replace') if isinstance(payload,bytes) else payload)
    def handle_starttag(self, tag, attrs):
        node=Node(tag,attrs,self.stack[-1]); self.stack[-1].children.append(node)
        if tag not in ('meta','link','img','input','br','hr','source','area','embed','wbr'): self.stack.append(node)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag: self.stack=self.stack[:i]; break
    def handle_data(self, data):
        if any(n.tag in ('script','style') for n in self.stack):return
        for node in self.stack: node.parts.append(data)
    def meta(self):
        return {n.attrs.get('property',n.attrs.get('name','')).lower():n.attrs.get('content','') for n in self.root.all('meta')}
    def links(self, base):
        return [(urljoin(base,n.attrs.get('href','')),n.text()) for n in self.root.all('a') if n.attrs.get('href')]
