class Node:
    def __init__(self, label=None, data=None):
        self.label = label
        self.data = data
        self.frequency = 0
        self.posting_list = []
        self.children = dict()
        self.reversed_node = None

    def addChild(self, key, data=None):
        if not isinstance(key, Node):
            self.children[key] = Node(key, data)
        else:
            self.children[key.label] = key

    def __getitem__(self, key):
        return self.children.get(key)


class Trie:
    def __init__(self):
        self.head = Node()

    def __getitem__(self, key):
        return self.head.children[key]

    def add(self, word):
        current_node = self.head
        word_finished = True

        for i in range(len(word)):
            if word[i] in current_node.children:
                current_node = current_node.children[word[i]]
            else:
                word_finished = False
                break

        if not word_finished:
            while i < len(word):
                current_node.addChild(word[i])
                current_node = current_node.children[word[i]]
                i += 1

        current_node.data = word
        return current_node

    def has_word(self, word):
        if word == '':
            return False
        if word == None:
            raise ValueError('Trie.has_word requires a not-Null string')

        current_node = self.head
        exists = True
        for letter in word:
            if letter in current_node.children:
                current_node = current_node.children[letter]
            else:
                exists = False
                break

        if exists:
            if current_node.data == None:
                exists = False

        return exists

    def start_with_prefix(self, prefix):
        words = list()
        queue = list()
        if prefix == None:
            raise ValueError('Requires not-Null prefix')

        top_node = self.head
        for letter in prefix:
            if letter in top_node.children:
                top_node = top_node.children[letter]
            else:
                return words

        if top_node == self.head:
            queue = [node for key, node in top_node.children.items()]
        else:
            queue = [top_node]

        while queue:
            current_node = queue.pop()
            if current_node.data != None:
                words.append(current_node)

            queue = [node for key, node in current_node.children.items()] + queue

        return words

    def getWholeTrie(self):
        words = []
        top_node = self.head

        queue = [node for key, node in top_node.children.items()]

        while queue:
            current_node = queue.pop()
            if current_node.data != None:
                words.append(current_node)

            queue = [node for key, node in current_node.children.items()] + queue

        return words

    def getData(self, word):
        if not self.has_word(word):
            return self.add(word)


        current_node = self.head
        for letter in word:
            current_node = current_node[letter]

        return current_node
