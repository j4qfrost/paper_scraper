# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from paper_scraper.items import *

from gql import gql, Client, AIOHTTPTransport
from gql.transport.exceptions import TransportQueryError
import json

def build_query(query_name, function_name, obj_name, identifer, args):
    argv = ''
    for i in args:
        argv += '{'
        for k,v in i.items():
            if v is None:
                if k == 'fieldsOfStudy' or k == 'aliases':
                    argv += f'{k}:[],'
                else:
                    argv += f'{k}:null,'

                continue
            if type(v) == bool:
                argv += f'{k}:true,' if v else f'{k}:false,'
                continue
            if type(v) == str:
                v = v.replace('\\', '\\\\')
                v = v.replace('\"', '\\\"')
                v = v.replace('\n', ' ')
                v = f'"{v}",'
            if type(v) == list:
                arr = ''
                for j in v:
                    try:
                        if j[0] == '{' or j[0] == '[':
                            arr += f'{j},'
                        else:
                            j = j.replace('\\', '\\\\')
                            j = j.replace('\"', '\\\"')
                            arr += f'"{j}",'
                    except Exception as e:
                        print('asdasdad', k)
                        raise e

                v = f'[{arr}]'
            argv += f'{k}:{v},'
        argv += '},'
    return gql(f'''
mutation {query_name} {{
  {function_name}(input: [{argv}]) {{
    {obj_name}
    {{
        {identifer}
    }}
  }}
}}''')

class GraphQLPipeline:
    def __init__(self, graphql_uri):
        self.graphql_uri = graphql_uri
        self.limit = 10
        self.obj_list = {}
        self.obj_list['author'] = []
        self.obj_list['paper'] = []
        self.obj_list['topic'] = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            graphql_uri=crawler.settings.get('GRAPHQL_URI'),
        )

    def open_spider(self, spider):
        transport = AIOHTTPTransport(url=self.graphql_uri)
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def close_spider(self, spider):
        if self.obj_list['author']:
            author_query = build_query('AddAuthors', 'addAuthor', 'author', 'authorId', self.obj_list['author'])
            try:
                self.client.execute(author_query)
            except TransportQueryError as e:
                print(e.errors)
        if len(self.obj_list['paper']) == self.limit:
            paper_query = build_query('AddPapers', 'addPaper', 'paper', 'paperId', self.obj_list['paper'])
            try:
                self.client.execute(paper_query)
            except TransportQueryError as e:
                print(e.errors)
        if len(self.obj_list['topic']) == self.limit:
            topic_query = build_query('AddTopics', 'addTopic', 'topic', 'topicId', self.obj_list['topic'])
            try:
                self.client.execute(topic_query)
            except TransportQueryError as e:
                print(e.errors)
    
    def execute_add_query(self, obj_name, limit=1):
        cap = obj_name.capitalize()
        if len(self.obj_list[obj_name]) >= limit:
            query = build_query(f'Add{cap}s', f'add{cap}', obj_name, f'{obj_name}Id', self.obj_list[obj_name])
            try:
                self.client.execute(query)
            except TransportQueryError as e:
                print(e.msg)
            self.obj_list[obj_name] = []


    def process_author_item(self, item, spider):
        author = dict(item)
        paper_ids = []
        for p in author['papers']:
            paper_ids.append(f'{{paperId: "{p["paperId"]}"}}')
        self.obj_list['author'].append(author)
        author['papers'] = paper_ids
        self.execute_add_query('author', limit=self.limit)

    def process_paper_item(self, item, spider):
        paper = dict(item)
        author_ids = []
        for a in paper['authors']:
            author_ids.append(f'{{authorId: "{a["authorId"]}"}}')
        topic_ids = []
        for t in paper['topics']:
            topic_ids.append(f'{{topicId: "{t["topicId"]}", topic: "{t["topic"]}"}}')
            del t['url']
        reference_ids = []
        for p in paper['references']:
            reference_ids.append(f'{{paperId: "{p["paperId"]}"}}')
        citation_ids = []
        for p in paper['citations']:
            citation_ids.append(f'{{paperId: "{p["paperId"]}"}}')
        paper['authors'] = author_ids
        paper['topics'] = topic_ids
        paper['references'] = reference_ids
        paper['citations'] = citation_ids
        self.obj_list['paper'].append(paper)
        self.obj_list['topic'].extend(paper['topics'].copy())
        self.execute_add_query('paper', limit=self.limit)
        self.execute_add_query('topic', limit=self.limit)

    def process_item(self, item, spider):
        if type(item) == AuthorItem:
            self.process_author_item(item, spider)
        elif type(item) == PaperItem:
            self.process_paper_item(item, spider)

        return item
