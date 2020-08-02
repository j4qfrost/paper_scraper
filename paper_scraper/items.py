# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class AuthorItem(scrapy.Item):
    authorId = scrapy.Field()
    name = scrapy.Field()
    aliases = scrapy.Field()
    papers = scrapy.Field()

class PaperItem(scrapy.Item):
    paperId = scrapy.Field()
    title = scrapy.Field()
    arxivId = scrapy.Field()
    corpusId = scrapy.Field()
    doi = scrapy.Field()
    year = scrapy.Field()
    venue = scrapy.Field()

    authors = scrapy.Field()
    abstract = scrapy.Field()
    citationVelocity = scrapy.Field()
    citations = scrapy.Field()
    references = scrapy.Field()

    fieldsOfStudy = scrapy.Field()
    topics = scrapy.Field()
    isOpenAccess = scrapy.Field()
    isPublisherLicensed = scrapy.Field()