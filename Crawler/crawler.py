# -*- coding: utf-8 -*-
import os,glob
import json

from elasticsearch import Elasticsearch
from urllib.request import urlopen
import urllib.error as er
from bs4 import BeautifulSoup
import numpy as np
from scipy.linalg import eig
from scipy.sparse import csc_matrix


class PostCrawler:
    def __init__(self, blog_url, url, in_degree):
        self.blog_url = blog_url
        self.url = url
        self.comment_urls = None
        self.folder_path = 'statics/results'
        self.in_degree = in_degree

    def crawl(self):
        print(self.url)
        response = urlopen(self.url).read()
        soup = BeautifulSoup(response, 'lxml')
        try:
            post_full_content_ = soup.find('div', {'class': 'post'}).findChildren()[1]
            post_full_content_xml = BeautifulSoup(post_full_content_.text, 'lxml')
            post_full_content_xml = BeautifulSoup(post_full_content_xml.text, 'lxml')
            post_full_content = post_full_content_xml.text
        except AttributeError:
            print('Empty Content')
            print(self.url)
            post_full_content = 'Empty Content'
        comments_url = list()
        a = soup.find('a', {'name': 'comments'})
        if a is not None:
            a_parent = a.parent
            urls = a_parent.find_all('a')
            index = 0
            for url in urls:
                # if index < self.in_degree:
                link = url.attrs.get('href', '')
                if 'blog.ir' in link and 'bayan.ir' not in link:
                    try:
                        if 'http' not in link:
                            comments_url.append('http:' + link)
                        else:
                            comments_url.append(link)
                        index += 1
                    except IndexError:
                        print('error in finding comment link !')
                        print(link)
                # else:
                #     break
        degree = self.in_degree - len(comments_url)
        new_post = dict()
        new_post['type'] = 'post'
        new_post['blog_url'] = self.blog_url
        new_post['post_url'] = self.url
        new_post['comment_urls'] = comments_url
        write_in_file(new_post, self.folder_path)
        return comments_url, post_full_content, degree


class BlogCrawler:
    def __init__(self, n, in_degree):
        self.urls = set()  # it's type is set
        self.crawled_urls = set()
        self.number_of_blogs = n
        self.in_degree = in_degree
        self.folder_path_type1 = 'statics/results'

    def crawl(self):
        number_of_crawled_url = 0
        while number_of_crawled_url < self.number_of_blogs:
            if len(self.urls) > 0:
                current_url = self.urls.pop()
                try:
                    response = urlopen(current_url).read()
                    number_of_crawled_url += 1
                    self.find_blog_content(current_url, response)
                    self.crawled_urls.add(current_url)
                except :
                    print('error')
                    print(current_url)
                    pass

    def find_blog_content(self, url, response):
        soup = BeautifulSoup(response, 'lxml')

        blog_dict_type_1 = dict()
        blog_dict_type_1['type'] = 'blog'

        blog_dict_type_1['blog_name'] = soup.title.string

        blog_dict_type_1['blog_url'] = soup.link.next[:-1]

        posts = soup.find_all('item')[:5]
        if len(posts) < 5:
            print('It has less than 5 post ! ')
            print(url)
        posts_list = list()
        index = 0
        for post in posts:
            post_dict = dict()
            index += 1
            post_url = post.link.next[:-2]
            blog_dict_type_1['post_url_' + str(index)] = post_url
            post_dict['post_url'] = post_url

            blog_dict_type_1['post_title_' + str(index)] = post.title.string

            # post_content = BeautifulSoup(post.description.text, 'lxml')
            # post_content = BeautifulSoup(post_content.text, 'lxml')
            # post_content_text = post_content.p
            # if post_content_text is not None:
            #     blog_dict_type_1['post_content_' + str(index)] = post_content_text.text
            # else:
            #     blog_dict_type_1['post_content_' + str(index)] = ''

            # post_crawler = PostCrawler(url, post_url, self.in_degree)
            # comments_url, full_content, degree = post_crawler.crawl()
            # blog_dict_type_1['post_full_content_' + str(index)] = full_content
            # self.add_url(comments_url)
            posts_list.append(post_dict)

        write_in_file(blog_dict_type_1, self.folder_path_type1)

    def add_url(self, urls):
        for url in urls:
            if url not in self.crawled_urls:
                if 'http' not in url:
                    url = 'http://' + url
                if url[-1] != '/':
                    self.urls.add(url + '/rss')
                else:
                    self.urls.add(url + 'rss')


number_of_whole_items= 0


def write_in_file(content, contents_folder_path):
    global number_of_whole_items
    os.chdir(contents_folder_path)
    with open((str(number_of_whole_items) + '.json'), 'w') as file:
        json_post = json.dumps(content)
        print(json_post, file=file)
    os.chdir('../..')
    number_of_whole_items += 1


def indexing(all_jsons):
    es = Elasticsearch(addr)
    for i in range(len(all_jsons)):
        blog = all_jsons[i]
        es.index(index=index_name, doc_type='post', id=str(i), body=blog)


def delete_index(n):
    es = Elasticsearch(addr)
    for i in range(n):
        es.delete(index=index_name, doc_type='post', id=i)


map_url_id = {}


def convert_url_id(url):
    temp = len(map_url_id.keys())
    if url not in map_url_id.keys():
        map_url_id[url] = temp


def pageR(G, maxerr=.0001):
    n = G.shape[0]
    M = csc_matrix(G, dtype=np.float)
    temp=np.zeros(n)
    result=np.ones(n)
    while np.sum(np.abs(result - temp)) > maxerr:
        temp = result.copy()
        for i in range(0, n):
            Ii = np.array(M[:, i].todense())[:, 0]
            result[i] = temp.dot(Ii)

    return result / sum(result)


def pageRank(number, alfa):
    es = Elasticsearch(addr)
    A = np.zeros((number, number))
    all_blogs=[]
    for i in range(number):
        blog = es.get(index=index_name, doc_type='post', id=str(i))['_source']
        blog_url = blog['blog']['url']
        convert_url_id(blog_url)
        all_blogs.append(blog)
    for blog in all_blogs:
        blog_url = blog['blog']['url']
        for post in blog['blog']['posts']:
            for comment in post['post_comments']:
                comment_url = comment['comment_url'] + '/'
                if comment_url in map_url_id.keys():
                    A[map_url_id[comment_url]][map_url_id[blog_url]] += 1
    for i in range(number):
        for j in range(number):
            if sum(A[i]) != 0:
                A[i][j] = A[i][j] / sum(A[i])
    A = (1 - alfa) * A + (alfa / number) * np.ones((number, number))
    v1 = pageR(A)
    for blog in all_blogs:
        pr = v1[map_url_id[blog['blog']['url']]]
        blog['blog']['page_rank'] = pr
        es.index(index=index_name, doc_type='post', id=str(i), body=blog)



def search_without_page_rank(title='', title_weight=0, post_title='', post_title_weight=0, post_content='',
                             post_content_weight=0):
    es = Elasticsearch(addr)
    results = es.search(index=index_name, body={
        'query': {
            "bool": {
                "should": [
                    {
                        'match': {
                            'blog.title': {
                                'query': title,
                                'boost': title_weight
                            },
                        }
                    },
                    {
                        'match': {
                            'blog.posts.post_title': {
                                'query': post_title,
                                'boost': post_title_weight
                            },
                        }
                    },
                    {
                        'match': {
                            'blog.posts.post_content': {
                                'query': post_content,
                                'boost': post_content_weight
                            },
                        }
                    }
                ]}
        }
    })
    blog_num = results['hits']['total']
    print(blog_num, ' blog found.')
    for hits in results['hits']['hits']:
        print("ID : " , hits['_id'])
        blog = hits['_source']['blog']
        print('url : ', blog['url'])
        print('title : ', blog['title'])
        print('Posts : ')
        for post in blog['posts']:
            print('\t post title : ' , post['post_title'])
            print('\t post content : ', post['post_content'].replace('\n', '\n\t'))


def search_with_page_rank(title='', title_weight=0, post_title='', post_title_weight=0, post_content='',
                          post_content_weight=0):
    global addr
    es = Elasticsearch(addr)
    results = es.search(index=index_name, body={
        'query': {
            'function_score': {
                'query': {
                    "bool": {
                        "should": [
                            {
                                'match': {
                                    'blog.title': {
                                        'query': title,
                                        'boost': title_weight
                                    },
                                }
                            },
                            {
                                'match': {
                                    'blog.posts.post_title': {
                                        'query': post_title,
                                        'boost': post_title_weight
                                    },
                                }
                            },
                            {
                                'match': {
                                    'blog.posts.post_content': {
                                        'query': post_content,
                                        'boost': post_content_weight
                                    },
                                }
                            }
                        ]
                    }
                },
                'script_score': {
                    "script": {
                        "source": " _score * doc['blog.page_rank'].value"
                    }
                }
            }
        }
    })


    blog_num = results['hits']['total']
    print(blog_num, ' blog found.')
    for hits in results['hits']['hits']:
        print("ID : ", hits['_id'])
        blog = hits['_source']['blog']
        print('url : ', blog['url'])
        print('title : ', blog['title'])
        print('Posts : ')
        for post in blog['posts']:
            print('\t post title : ', post['post_title'])
            print('\t post content : ', post['post_content'].replace('\n', '\n\t'))


def combine2json(in_degree):
    blogs = []
    posts = []
    all_blogs = []
    for file in glob.glob('*.json'):
        content = open(file)
        json_file = json.loads(content.read())
        if json_file['type'] == 'blog':
            blogs.append(json_file)
        elif json_file['type'] == 'post':
            posts.append(json_file)
    for blog in blogs:
        blog_dict = {}
        blog_dict['blog'] = {}
        blog_dict['blog']['title'] = blog['blog_name']
        blog_dict['blog']['url'] = blog['blog_url']
        blog_dict['blog']['posts'] = []
        for post in posts:
            if str(post['blog_url']) in blog['blog_url']:
                post_dict = {}
                post_dict['post_url'] = post['post_url']
                post_dict['post_comments'] = []
                for comment in post['comment_urls']:
                    post_dict['post_comments'].append({'comment_url': comment})
                for i in range(1, in_degree + 1):
                    if blog['post_url_' + str(i)] == post['post_url']:
                        post_dict['post_title'] = blog['post_title_' + str(i)]
                        post_dict['post_content'] = blog['post_content_' + str(i)]
                        break
                blog_dict['blog']['posts'].append(post_dict)
        all_blogs.append(blog_dict)
    return all_blogs


index_name = 'test_index2'
addr = ''
elastic_address = ''
number_of_blogs = 0
in_degree=0
while True:
    print('For crawling blog.ir pages type 1\n'
          'For indexing blog information type 2\n'
          'For calculating page rank of blogs type 3\n'
          'For searching on blogs type 4\n'
          'To finish type 0')
    section = int(input())
    if section is 1:
        print('Enter the start urls: (Put the space between the two elements. and url mast be in this pattern : SOMETHING.blog.ir)')
        urls = input().split(' ')
        print('Enter the number of pages you want to crawl:')
        number_of_blogs = int(input())
        print('Enter in-degree for urls inside each post pages comment :')
        in_degree = int(input())
        crawler = BlogCrawler(number_of_blogs, in_degree)
        crawler.add_url(urls)
        crawler.crawl()
        print('End of Crawling. \nblogs and posts saved in statics/results ')
    elif section is 2:
        print('For starting indexing, enter the folder of json files : ')
        all_jsons = []
        try:
            os.chdir(input())
            if in_degree == 0:
                in_degree = int(input('please enter in-degree'))
            all_jsons = combine2json(in_degree)
            number_of_blogs = len(all_jsons)
        except:
            print('Foder name is not correct')
            continue
        print('Enter the address that elastic search run over it : (in this pattern localhost:9200)')
        elastic_address = input()
        addr = 'http://' + elastic_address
        print('If you want to delete last indexes print "d"')
        if input() == 'd':
            delete_index(number_of_blogs)
        indexing(all_jsons)
    elif section is 3:
        print('Enter the address that elastic search run over it : (in this pattern localhost:9200)')
        elastic_address = input()
        addr = 'http://' + elastic_address
        print('Enter alfa for page rank algorithm :')
        alfa = float(input())
        if number_of_blogs == 0:
            number_of_blogs = int(input('enter number of blogs'))
        pageRank(number_of_blogs, alfa)
    elif section is 4:
        if elastic_address == '':
            print('Enter the address that elastic search run over it : (in this pattern localhost:9200)')
            elastic_address = input()
        addr = 'http://' + elastic_address + '/'
        print('Enter this requirements : ')
        title_blog = input('title blog: ')
        w_title_blog = int(input('weight for blog title: '))
        title_post = input('post title: ')
        w_title_post = int(input('weight for post title: '))
        content_post = input('post content: ')
        w_content_post = int(input('weight for post content: '))
        print('Do you want to influence page rand? (yes/no) ')
        if input() == 'yes':
            search_with_page_rank(title_blog, w_title_blog, title_post, w_title_post, content_post, w_content_post)
        else:
            search_without_page_rank(title_blog, w_title_blog, title_post, w_title_post, content_post, w_content_post)