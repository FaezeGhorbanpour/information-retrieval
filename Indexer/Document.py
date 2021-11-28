import io
import itertools
import json
import os
from collections import Counter
from math import log, sqrt

import hazm

from Trie import Trie


def return_content(file_address):
    address = '..\HamshahriData\\' + file_address
    with io.open(address, 'r', encoding='utf8') as f:
        text = f.read()
    return text

class Document:
    def __init__(self):
        self.dictionary = Trie()
        self.docs = dict()
        self.most_repeated_words = set()

    def get_term_positional_index(self, term):
        term_dict = self.dictionary.getData(term)
        return term, term_dict.frequency, term_dict.posting_list

    def prepare(self, doc_text):
        doc_words = dict()
        preposition = ['.','،','!','؟','»','«',')','(','}','{',':','؛']
        for doc, text in doc_text.items():
            clean_text = text
            normalizer = hazm.Normalizer()
            normal_text = normalizer.normalize(clean_text)
            sentences = hazm.sent_tokenize(normal_text)
            words = list()
            for sentence in sentences:
                new_words = hazm.word_tokenize(sentence)
                for i in range(len(new_words) - 1, -1, -1):
                    if new_words[i] in preposition:
                        del new_words[i]
                words = words + new_words
            doc_words[doc] = words
        doc_words, doc_positions = self.delete_stopwords(doc_words)
        doc_stemmed_words = dict()
        for doc, words in doc_words.items():
            stemmer = hazm.Stemmer()
            doc_stemmed_words[doc] = [stemmer.stem(word) for word in words]
        return doc_stemmed_words, doc_positions

    def delete_stopwords(self, doc_words):
        words = list()
        for word in doc_words.values():
            words += word
        number = 5
        if len(words) != 0:
            number = int(3.257143*log(len(words),10) - 5)
        self.most_repeated_words = [word for word, word_count in Counter(words).most_common(number)]
        doc_edited_words = dict()
        doc_positional = dict()
        for doc, words in doc_words.items():
            words_copy = list(words)
            positional = [i for i in range(len(words))]
            for i in range(len(words) - 1, -1, -1):
                if words[i] in self.most_repeated_words:
                    del words_copy[i]
                    del positional[i]
            doc_edited_words[doc] = words_copy
            doc_positional[doc] = positional
        return doc_edited_words, doc_positional

    def make_positional_list(self, terms, positions, file_name):
        term_frequency = Counter(terms)
        doc_dictionary = {}
        for key, value in term_frequency.items():
            index = [positions[i] for i, x in enumerate(terms) if x == key]
            temp_dict = dict()
            temp_dict[file_name] = index
            each_term_data = {'frequency': value, 'docs': [temp_dict]}
            doc_dictionary[key] = each_term_data
        return doc_dictionary

    def save_dictionary(self, file_name):
        words = self.dictionary.getWholeTrie()
        words_dict = {}
        for word in words:
            temp_dict = dict()
            temp_dict['frequency'] = word.frequency
            temp_dict['docs'] = word.posting_list
            words_dict[word.data] = temp_dict
        with io.open(file_name + '.json', 'w', encoding='utf8') as f:
            f.write(json.dumps(words_dict))

    def load_dictionary(self, file_name):
        with io.open(file_name + '.json', 'r', encoding='utf8') as f:
            try:
                text = json.load(f)
                for word, value in text.items():
                    node = self.dictionary.add(word)
                    node.frequency = value['frequency']
                    node.posting_list = value['docs']
            except:
                raise ValueError('این فایل نامعتبر است.')

    def search(self, query, type_of_search, type_of_retrival):
        normalizer = hazm.Normalizer()
        normal_text = normalizer.normalize(query)
        sentences = hazm.sent_tokenize(normal_text)
        words = list()
        stemmer = hazm.Stemmer()
        for sentence in sentences:
            words = words + hazm.word_tokenize(sentence)
        first_position = [i for i in range(len(words))]
        words = [stemmer.stem(word) for word in words]
        stemmed_words = [word for word in words if word not in self.most_repeated_words]
        if type_of_search == 0:  # sequential
            return self.sequential_search(stemmed_words, type_of_retrival)
        else:
            phrasals, phrasal, positions, position = [], [], [], []
            end = False
            for i in stemmed_words:
                if i == '»':
                    end = False
                    phrasals.append(phrasal)
                    positions.append(position)
                    phrasal, position = list(), list()
                if end:
                    phrasal.append(i)
                    position.append(first_position[words.index(i)])
                if i == '«':
                    end = True
            stemmed_words = [i for i in stemmed_words if i != '»' and i != '«']
            related_docs = self.exact_search(phrasals, positions)
            # r = self.sequential_search(stemmed_words, type_of_retrival)
            # related_docs += [i for i in r if i not in related_docs]
            return related_docs

    def sequential_search(self, terms, type_of_retrival):
        related_docs = []
        for term in terms:
            w = self.find_relevent_doc(term)
            if w is not None and w is not []:
                related_docs.append(self.find_relevent_doc(term))
        all_scores = dict()
        for element in itertools.product(*related_docs):
            element_list = list(element)
            query_normalized = self.tf_idf_query(element_list, type_of_retrival)
            documents_score = self.tf_idf_document(element_list, type_of_retrival)
            for doc, value in documents_score.items():
                score = sum([query_normalized[i] * value[i] for i in value.keys()])
                if doc not in all_scores or all_scores[doc] < score:
                    all_scores[doc] = score
        related_docs = dict(Counter(all_scores).most_common(45))
        return list(related_docs.keys())

    def tf_idf_document(self, terms, type_of_retrival):
        docs = list()
        for element in terms:
            for doc in element.posting_list:
                docs.append(doc)
        docs = set().union(*docs)
        each_doc_score = dict()
        for doc in docs:
            tf_wt = {i: 1 + log(len(list(j.values())[0])) for i in terms for j in i.posting_list if
                     list(j.keys())[0] == doc}
            wt = dict(tf_wt)
            if type_of_retrival == 0:
                normalized = dict(wt)
            else:
                l = [j ** 2 for i, j in wt.items()]
                cosine = 1 / sqrt(sum(l))
                normalized = {i: j * cosine for i, j in wt.items()}
            each_doc_score[doc] = normalized
        return each_doc_score

    def tf_idf_query(self, terms, type_of_retrival):
        tf_wt = {i: 1 + log(terms.count(i), 10) for i in terms}
        terms = tf_wt.keys()
        df = {i: len(i.posting_list) for i in terms}
        idf = dict()
        for i in terms:
            if df[i] != 0:
                temp = len(list(self.docs.keys())) / float(df[i])
                if temp == 0:
                    idf[i] = 0
                else:
                    idf[i] = log(temp, 10)
            else:
                idf[i] = 0
        wt = {i: tf_wt[i] * idf[i] for i in terms}
        if type_of_retrival == 0:
            normalized = dict(wt)
        else:
            l = [wt[i] ** 2 for i in terms]
            if sum(l) != 0:
                cosine = 1 / sqrt(sum(l))
            else:
                cosine = 0
            normalized = {i: wt[i] * cosine for i in terms}
        return normalized

    def exact_search(self, phrases, positions):
        final_docs = dict()
        for order in range(len(phrases)):
            phrase = phrases[order]
            nodes = list()
            commen_docs = set(self.docs.keys())
            for word in phrase:
                node = self.dictionary.getData(word)
                nodes.append(node)
                commen_docs = commen_docs.intersection((list(i.keys())[0] for i in node.posting_list))
            for doc in commen_docs:
                i = 1
                first_list = [list(i.values())[0] for i in nodes[0].posting_list if list(i.keys())[0] == doc][0]
                final_list = list()
                while i < len(nodes):
                    second_list = [list(i.values())[0] for i in nodes[i].posting_list if list(i.keys())[0] == doc][0]
                    a, b = 0, 0
                    while a < len(first_list) and b < len(second_list):
                        if first_list[a] + (positions[order][i] - positions[order][i - 1]) < second_list[b]:
                            a += 1
                        elif first_list[a] + (positions[order][i] - positions[order][i - 1]) > second_list[b]:
                            b += 1
                        else:
                            final_list.append(second_list[b])
                            a += 1
                            b += 1
                    first_list = list(final_list)
                    i += 1
                if final_list is not []:
                    if doc in final_docs:
                        final_docs[doc] += 1
                    else:
                        final_docs[doc] = 0
        related_docs = dict(Counter(final_docs).most_common(45))
        return list(related_docs.keys())

    def find_relevent_doc(self, term):
        words = []

        if term and term[-1] == '*':
            words = self.dictionary.start_with_prefix(term[:-1])
        elif '*' in term:
            i = term.index('*')
            words = self.dictionary.start_with_prefix(term[:i])
            second_dictionary = Trie()
            for word in words:
                node = second_dictionary.add(word.data[::-1])
                node.reversed_node = word
            reversed_words = second_dictionary.start_with_prefix(term[-1:i:-1])
            words = [word.reversed_node for word in reversed_words]
        else:
            words.append(self.dictionary.getData(term))
        return words

    def wildcard(self, term):
        words = self.dictionary.start_with_prefix(term)
        words_dict = dict()
        for word in words:
            temp_dict = dict()
            temp_dict['frequency'] = word.frequency
            temp_dict['docs'] = word.posting_list
            words_dict[word.data] = temp_dict
        return words_dict

    def delete_document(self, year, file_name):
        if file_name not in self.docs.keys():
            return 'این داک در سیستم موجود نیست !'
        try:
            raw_text = return_content('HamshahriCorpus\\' + str(year) + '\\' + file_name + '.ham')
        except FileNotFoundError:
            return 'سندی در این سال با این نام وجود ندارد. '
        del self.docs[file_name]
        doc_prepared_words, doc_postitions = self.prepare({file_name: raw_text})
        for prepared_words in doc_prepared_words.values():
            term_frequency = {i: prepared_words.count(i) for i in prepared_words if i != ''}
            for key, value in term_frequency.items():
                temp_dict = self.dictionary.getData(key)
                temp_dict.frequency -= value
                temp_dict.data = None
                y = {}
                for x in temp_dict.posting_list:
                    if list(x.keys())[0] == file_name:
                        y = x
                if y != {}:
                    temp_dict.posting_list.remove(y)

    def add_document(self, year, file_name):
        if file_name in self.docs:
            return 'این داک قبلا اضافه شده بود !'
        else:
            self.docs[file_name] = year
        try:
            raw_text = return_content('HamshahriCorpus\\' + str(year) + '\\' + file_name + '.ham')
        except FileNotFoundError:
            return 'سندی در این سال با این نام وجود ندارد.'
        self.preprocess({file_name: raw_text})

    def preprocess(self, doc_text):
        doc_prepared_words, doc_postitions = self.prepare(doc_text)
        for doc, prepared_words in doc_prepared_words.items():
            document_dictionary = self.make_positional_list(prepared_words, doc_postitions[doc], doc)
            for key, value in document_dictionary.items():
                if self.dictionary.has_word(key):
                    temp_dict = self.dictionary.getData(key)
                else:
                    temp_dict = self.dictionary.add(key)
                temp_dict.frequency += value['frequency']
                temp_dict.posting_list += value['docs']

    def add_several_doc(self, list_of_year):
        doc_text = dict()
        for year in list_of_year:
            for root, dirs, files in os.walk('..\HamshahriData\\' + 'HamshahriCorpus\\' + str(year)):
                for file in files:
                    if file[:-4] in self.docs.keys():
                        print('داک با نام {0} در سال {1} قبلا اضافه شده است !'.format(file[:-4], year))
                    else:
                        with open(os.path.join(root, file), 'r', encoding='utf8') as f:
                            self.docs[file[:-4]] = year
                            doc_text[file[:-4]] = f.read()
        self.preprocess(doc_text)
