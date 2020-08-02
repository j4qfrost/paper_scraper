import scrapy
# import json
from paper_scraper.items import *

class SemanticScholarSpider(scrapy.Spider):
    name = 'semantic_scholar'
    allowed_domains = ['api.semanticscholar.org']
    api_version = '1'
    api_url = f'http://api.semanticscholar.org/v{api_version}/'

    def start_requests(self):
        if not (getattr(self, 'obj', None) and getattr(self, 'sid', None)):
            self.obj = 'author'
            self.sid = '8319448'
        url = SemanticScholarSpider.api_url + f'{self.obj}/{self.sid}'
        yield scrapy.Request(url, self.parse)

    def parse_author(self, response):
        body = response.json()
        obj = 'paper'

        # print(body)
        item = AuthorItem()
        for i in item.fields:
            item[i] = body[i]
        yield item

        links = [SemanticScholarSpider.api_url + f'{obj}/{paper["paperId"]}' for paper in body['papers']]
        yield from response.follow_all(links, callback=self.parse_paper)

    def parse_paper(self, response):
        body = response.json()
        paper_obj = 'paper'
        author_obj = 'author'

        # print(body)
        body['isOpenAccess'] = body['is_open_access']
        body['isPublisherLicensed'] = body['is_publisher_licensed']
        item = PaperItem()
        for i in item.fields:
            item[i] = body[i]
        yield item

        authors = [author['authorId'] for author in body['authors']]
        papers = [paper['paperId'] for paper in body['citations']]

        author_links = [SemanticScholarSpider.api_url + f'{author_obj}/{author}' for author in authors]
        yield from response.follow_all(author_links, callback=self.parse_author)
        paper_links = [SemanticScholarSpider.api_url + f'{paper_obj}/{paper}' for paper in papers]
        yield from response.follow_all(paper_links, callback=self.parse_paper)

    def parse(self, response):
        if self.obj == 'author':
            yield from self.parse_author(response)
        else:
            yield from self.parse_paper(response)
