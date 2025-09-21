#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL提交器 - 从RSS站点地图中提取URL并向必应提交
"""

import logging
import random
import sys
import os
import argparse
import xml.etree.ElementTree as ET
import requests
import colorama


class SitemapParser:
    """RSS站点地图解析器"""
    
    def __init__(self, sitemap_file: str):
        self.sitemap_file = sitemap_file
    
    def parse_rss_sitemap(self) -> list[str]:
        """
        解析RSS格式的站点地图, 提取所有URL
        
        Returns:
            list[str]: 提取到的URL列表
        """
        urls = []
        
        try:
            # 解析XML文件
            tree = ET.parse(self.sitemap_file)
            root = tree.getroot()
            
            # 查找所有item元素中的link
            for item in root.findall('.//item'):
                link_element = item.find('link')
                if link_element is not None and link_element.text:
                    urls.append(link_element.text.strip())
            
            logger.info(f"成功解析站点地图，找到 {len(urls)} 个URL")
            return urls
            
        except ET.ParseError as e:
            logger.error(f"XML解析错误: {e}")
            return []
        except FileNotFoundError:
            logger.error(f"文件未找到: {self.sitemap_file}")
            return []
        except Exception as e:
            logger.error(f"解析站点地图时发生错误: {e}")
            return []

class Submitter:
    """URL提交器基类"""
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        
    
    def submit_urls(self, _urls: list[str], _site_url: str) -> dict[str, str]:
        raise NotImplementedError("子类必须实现submit_urls方法")

class BingSubmitter(Submitter):
    """
    必应搜索引擎json格式URL提交器
    https://www.bing.com/webmasters/url-submission-api#APIs
    """
    def __init__(self, api_key: str) -> None:
        super().__init__(api_key, "https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch")
        self.session.headers.update({
            'Content-Type': 'application/json; charset=utf-8',
            'Host': 'ssl.bing.com',
        })

    def submit_urls(self, urls: list[str], site_url: str, limit: int=10) -> dict[str, str]:
        """
        通过API向必应提交URL(需要API密钥)
        
        Args:
            urls: 要提交的URL列表
            site_url: 网站URL
            
        Returns:
            dict: 提交结果
        """
        if not self.api_key:
            return {
                'status': 'error',
                'message': '缺少API密钥，请设置BING_API_KEY环境变量或手动提交'
            }
        
        try:
            # 准备请求数据
            data = {
                'siteUrl': site_url,
                'urlList': random.sample(urls, min(len(urls), limit))
            }
            
            submit_url = f"{self.base_url}?apikey={self.api_key}"
            
            # 发送请求
            response = self.session.post(
                submit_url,
                json=data,
                timeout=20
            )
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'message': f'成功提交 {len(urls)} 个URL到必应',
                    'response': response.json()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'提交失败，状态码: {response.status_code}',
                    'response': response.text
                }
                
        except requests.RequestException as e:
            return {
                'status': 'error',
                'message': f'网络请求错误: {e}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'提交过程中发生错误: {e}'
            }


class IndexNowSubmitter(Submitter):
    """
    IndexNow URL提交器
    https://www.bing.com/indexnow/getstarted
    """
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.indexnow.org/IndexNow")
        self.session.headers.update({
            'Content-Type': 'application/json; charset=utf-8',
            'Host': 'api.indexnow.org',
        })
    
    def submit_urls(self, urls: list[str], site_url: str) -> dict[str, str]:
        """
        通过API向IndexNow提交URL(需要API密钥)
        
        Args:
            urls: 要提交的URL列表
            site_url: 网站URL
            
        Returns:
            dict: 提交结果
        """
        if not self.api_key:
            return {
                'status': 'error',
                'message': '缺少API密钥，请设置BING_API_KEY环境变量或手动提交'
            }
        
        try:
            # 准备请求数据
            data = {
                'host': site_url,
                'key': self.api_key,
                'keyLocation': f"{site_url}/{self.api_key}.txt",
                'urlList': urls
            }
            response = self.session.post(
                self.base_url,
                json=data,
                timeout=20
            )
            
            # https://jakob-bagterp.github.io/index-now-for-python/user-guide/how-to-submit/status-codes/#overview-of-status-codes
            if response.status_code in [200, 202]:
                return {
                    'status': 'success',
                    'message': f'成功提交, 状态码: {response.status_code}',
                    'response': response.text
                }
            else:
                return {
                    'status': 'error',
                    'message': f'提交失败，状态码: {response.status_code}',
                    'response': response.text
                }
                
        except requests.RequestException as e:
            return {
                'status': 'error',
                'message': f'网络请求错误: {e}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'提交过程中发生错误: {e}'
            }

class Logger:
    class ColorFormatter(logging.Formatter):
        """自定义日志格式化器，添加颜色到日志级别"""
        LEVEL_COLORS = {
            "DEBUG": colorama.Fore.BLUE,  # 蓝色
            "INFO": colorama.Fore.GREEN,  # 绿色
            "WARNING": colorama.Fore.YELLOW,  # 黄色
            "ERROR": colorama.Fore.RED,  # 红色
            "CRITICAL": colorama.Fore.MAGENTA,  # 紫色
        }

        def format(self, record):
            levelname = record.levelname
            if levelname in self.LEVEL_COLORS:
                record.levelname = f"{self.LEVEL_COLORS[levelname]}{levelname}{colorama.Style.RESET_ALL}"
            return super().format(record)
    def __init__(self, level=logging.INFO, log_file:str | None = None):
        colorama.init(autoreset=True)
        self.logger = logging.getLogger('URLSubmitter')
        self.logger.setLevel(level)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        
        # 创建文件处理器（如果提供了日志文件路径）
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                '[%(asctime)s-%(levelname)s]: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # 创建自定义格式化器并添加到控制台处理器
        color_formatter = Logger.ColorFormatter(
            '[%(asctime)s-%(levelname)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(color_formatter)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

logger:logging.Logger

def main():
    """主函数"""
    # 1. 解析站点地图
    arg_parser = argparse.ArgumentParser(description="URL提交器 - 从RSS站点地图提取URL并向必应提交")
    arg_parser.add_argument('--sitemap', type=str, default='./sitemap.xml', help='RSS站点地图文件路径')
    arg_parser.add_argument('--log', type=str, default=None, help='日志文件路径（可选）')
    args = arg_parser.parse_args()
    sitemap_file = args.sitemap
    log_file = args.log
    logger = Logger(log_file=log_file).get_logger()
    site_parser = SitemapParser(sitemap_file)
    urls = site_parser.parse_rss_sitemap()
    
    if not urls:
        logger.warning("未找到任何URL")
        return
    
    # 从环境变量获取API密钥
    bing_api_key = os.getenv('BING_API_KEY')
    indexNow_api_key = os.getenv('INDEXNOW_API_KEY')
    if not (bing_api_key and indexNow_api_key):
        logger.error("未获取到API密钥, 请设置BING_API_KEY和INDEXNOW_API_KEY环境变量")
        return
    bing_submitter = BingSubmitter(bing_api_key)
    indexNow_submitter = IndexNowSubmitter(indexNow_api_key)
    
    # 提取网站主域名
    site_url = urls[0].split('/')[0] + '//' + urls[0].split('/')[2]
    logger.info(f"网站URL: {site_url}")

    logger.info("自动提交到必应搜索引擎...")
    result = bing_submitter.submit_urls(urls, site_url)
    
    match result['status']:
        case 'success':
            logger.info(f"提交成功: {result}")
        case 'error':
            logger.error(f"提交失败: {result}")

    logger.info("自动提交到IndexNow...")
    result = indexNow_submitter.submit_urls(urls, site_url)
    match result['status']:
        case 'success':
            logger.info(f"提交成功: {result}")
        case 'error':
            logger.error(f"提交失败: {result}")

if __name__ == '__main__':
    main()
