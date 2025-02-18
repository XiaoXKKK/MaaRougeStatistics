import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.project import get_project_settings

class WikiImageItem(scrapy.Item):
    image_urls = scrapy.Field()
    images = scrapy.Field()

class PRTSWikiSpider(scrapy.Spider):
    name = 'prts_wiki'
    allowed_domains = ['prts.wiki', 'torappu.prts.wiki']
    start_urls = ['https://prts.wiki/w/萨卡兹的无终奇语/想象实体图鉴']
    def parse(self, response):
        # 提取所有包含收藏品图片的img标签
        img_selectors = response.xpath('//tr/td[contains(@style, "background:#464646")]//img')
        image_urls = []
        for img in img_selectors:
            # 优先使用data-src，若不存在则使用src
            url = img.xpath('@data-src').get() or img.xpath('@src').get()
            if url:
                # 补全为完整URL
                full_url = response.urljoin(url)
                # 将协议头转换为https
                if full_url.startswith('//'):
                    full_url = f'https:{full_url}'
                image_urls.append(full_url)
        # 去重处理
        image_urls = list(set(image_urls))
        item = WikiImageItem()
        item['image_urls'] = image_urls
        yield item

class CustomImagesPipeline(ImagesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        # 使用原始文件名保存图片
        image_guid = request.url.split('/')[-1]
        return image_guid

if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess
    
    # 项目设置
    settings = get_project_settings()
    settings.update({
        'ITEM_PIPELINES': {'__main__.CustomImagesPipeline': 1},
        'IMAGES_STORE': './relics',  # 图片保存路径
        'DOWNLOAD_DELAY': 0.5,       # 下载延迟
        'AUTOTHROTTLE_ENABLED': True # 启用自动限速
    })

    process = CrawlerProcess(settings)
    process.crawl(PRTSWikiSpider)
    process.start()