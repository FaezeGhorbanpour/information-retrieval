class Measurement:
    def __init__(self, real_query_doc, number):
        self.real_query_doc = real_query_doc
        self.number_of_docs = number

    def F_measure(self, query, docs):
        tp = set(self.real_query_doc[query])
        tp = tp.intersection(set(docs))
        P = len(tp) / len(docs)
        R = len(tp) / len(self.real_query_doc[query])
        if P + R != 0:
            F = 2 * P * R / (P + R)
        else:
            F = 0
        return F

    def MAP(self, query, docs):
        map_result = 0
        map_count = 0
        for i in range(len(docs)):
            if docs[i] in self.real_query_doc[query]:
                map_count += 1
                map_result += map_count / (i + 1)
        if map_count == 0:
            return 0
        return map_result / map_count
