import file_io
import sys
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords


class Querier:
    STOP_WORDS = set(stopwords.words('english'))

    def __init__(self, titles_fp, docs_fp, words_fp, pagerank):
        self.ids_to_titles = {}
        self.ids_to_pagerank = {}
        self.words_to_doc_to_relevance = {}
        self.pagerank = pagerank

        try:
            file_io.read_title_file(titles_fp, self.ids_to_titles)
            file_io.read_docs_file(docs_fp, self.ids_to_pagerank)
            file_io.read_words_file(words_fp, self.words_to_doc_to_relevance)
        except FileNotFoundError:
            print("No file found! Please try re-entering arguments.")

    def query(self, user_input):
        """This method takes in a user input from our REPL and scores the items 
        in the query against the relevance and pagerank dictionaries read in the 
        constructor

        Paramters:
        user_input -- the query 
        """
        stemmer = PorterStemmer()
        queried_terms = []
        page_to_relevance = {}

        # stem and remove stop words
        for i in user_input.split(" "):
            if i not in self.STOP_WORDS:
                i = i.lower()
                if i.strip() != "":
                    i = i.strip()
                i = stemmer.stem(i)
                queried_terms.append(i)

        # sort based on relevance
        for j in self.ids_to_titles:
            # populate page_to_relevance
            tot = 0
            for k in queried_terms:
                if k in self.words_to_doc_to_relevance:
                    if j in self.words_to_doc_to_relevance[k]:
                        tot += self.words_to_doc_to_relevance[k][j]
                        if self.pagerank:
                            tot *= self.ids_to_pagerank[j]
            page_to_relevance[j] = tot

        # sort
        rel_list = sorted(page_to_relevance.items(),
                          key=lambda x: x[1], reverse=True)
        try:
            if rel_list[0][1] == 0.0:
                print("Search item", user_input, "has no relevant documents")
        except IndexError:
            print("Search item", user_input,
                  "has no relevant documents, empty wiki.")
            sys.exit()

        count = 0
        for i in rel_list:
            if i[1] != 0 and count < 10:
                print(self.ids_to_titles[i[0]])
                count += 1


if __name__ == "__main__":
    search = True
    try:
        for x in range(2, len(sys.argv[1:])):
            if not sys.argv[x].endswith('.txt'):
                raise IOError

        if len(sys.argv) - 1 == 3:  # no pagerank
            q = Querier(sys.argv[1], sys.argv[2], sys.argv[3], False)
        # pagerank
        elif len(sys.argv) - 1 == 4 and sys.argv[1] == '--pagerank':
            q = Querier(sys.argv[2], sys.argv[3], sys.argv[4], True)
        else:
            print("\ncannot accept arguments. please try again :)\n")
            search = False

    except IOError:
        print("Please enter proper, existing file. You may be missing .txt")
        sys.exit()

    if search:
        user_input = input("search> ")
        while user_input != ":quit":
            q.query(user_input)
            user_input = input("search> ")