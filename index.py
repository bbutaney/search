import math
import re
from xml.dom.minidom import Element
import xml.etree.ElementTree as et
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import sys
import file_io


class Indexer:

    STOP_WORDS = set(stopwords.words('english'))

    def __init__(self, xml_fp, titles_fp, docs_fp, words_fp):
        try:
            self.root: Element = et.parse(xml_fp).getroot()
            self.all_pages: et.ElementTree = self.root.findall("page")
            self.number_of_documents = 0  # our n value
            self.ids_to_titles = {}
            self.ids_to_pageranks = {}
            self.relevance_dict = {}

            # parse xml file
            self.parse_xml()

            # write to files
            file_io.write_title_file(titles_fp, self.ids_to_titles)
            file_io.write_docs_file(docs_fp, self.ids_to_pageranks)
            file_io.write_words_file(words_fp, self.relevance_dict)

        except FileNotFoundError:
            print("Entered incorrect filepath! Please try again.")

    def parse_xml(self):
        """ parses xml_fp and populates all instance variables
        """

        # ids_to_titles = {}
        n_regex = '''\[\[[^\[]+?\]\]|[a-zA-Z0-9]+'[a-zA-Z0-9]+|[a-zA-Z0-9]+'''
        words_to_docs_to_count = {}
        page_to_linked_pages = {}

        for page in self.all_pages:
            # populate ids_to_titles
            title: str = page.find('title').text.strip().lower()
            id: int = int(page.find('id').text)
            self.ids_to_titles[id] = title

            # tokenize data
            try:
                t = re.findall(n_regex, page.find('text').text)
                t += re.findall(n_regex, page.find('title').text)
                tokens = [x.strip() for x in t]
            except TypeError:
                tokens = []

            link_count = 0

            for word in tokens:
                # tokenize the word
                return_list = []
                pg_list = []  # tokenized word for use in page rank
                stemmer = PorterStemmer()  # instantiate stemmer

                # check if word is a link and handle appropriately based on
                # contents of word
                if '[[' and ']]' in word:
                    link_count += 1
                    word = word.replace('[[', '').replace(']]', '')
                    pg_list = word

                    if ":" in word:
                        # strip, remove stop words
                        return_list = [i.strip().lower() for i in word.split(
                            ":") if i not in self.STOP_WORDS and i.strip(
                        ) != ""]

                        # remove spaces in words
                        for i in return_list:
                            z = i.split()
                            z = [j.strip() for j in z if j.strip() != ""]
                            return_list = z + return_list
                            return_list.remove(i)

                        # remove newlines in words
                        for i in return_list:
                            z = i.split("\n")
                            z = [k.strip() for k in z if k.strip() != ""]
                            return_list = z + return_list
                            return_list.remove(i)

                        # strip, remove stop words
                        return_list = [i.strip()
                                       for i in return_list if i.strip() != ""]

                        # handle pipes after splitting on colon
                        for i in return_list:
                            if "|" in i:
                                ind = i.index("|")
                                words = i[ind + 1:]
                                words = [i.strip().lower(
                                ) for i in words if i.strip().lower(
                                ) not in self.STOP_WORDS and i.strip(
                                ).lower() != ""]
                                return_list = words + return_list

                    # handle pipes if colon is not in word
                    if "|" in word:
                        ind = word.index("|")

                        # don't include words before pipe
                        return_list = word[ind + 1:]

                        # strip, remove stop words
                        return_list = [i.strip().lower(
                        ) for i in return_list if i.strip().lower(
                        ) not in self.STOP_WORDS and i.strip().lower() != ""]

                        pg_list = word.split("|")
                        pg_list = pg_list[0]

                    # stem words in return_list
                    return_list = [stemmer.stem(
                        i) for i in return_list if stemmer.stem(i) != ""]

                    # handle KeyError when inner dictionary key does not exist
                    try:
                        page_to_linked_pages[title]
                    except KeyError:
                        page_to_linked_pages[title] = []

                    # add titles of linked pages
                    page_to_linked_pages[title].append(pg_list.strip().lower())

                else:  # handling word if it is not a link
                    word = word.strip().lower()
                    word = stemmer.stem(word)

                    if word not in self.STOP_WORDS:
                        return_list = [word]
                    else:
                        return_list = []

                # populate words_to_docs_to_count
                for i in return_list:
                    if i != ":" and i != "|":
                        # handle KeyErrors when inner dict key does not exist
                        try:
                            words_to_docs_to_count[i]
                        except KeyError:
                            words_to_docs_to_count[i] = {}
                        try:
                            words_to_docs_to_count[i][id] += 1
                        except KeyError:
                            words_to_docs_to_count[i][id] = 1

            # check if the page has any links:
            if link_count == 0:
                page_to_linked_pages[title] = [
                    i.find('title').text.strip().lower(
                    ) for i in self.all_pages if i != page]

        # set number of documents in the corpus
        self.number_of_documents = len(self.ids_to_titles)

        # populate relevance dictionary
        self.fill_relevancy(words_to_docs_to_count)

        # populate pageranks for each document in the corpus
        self.ids_to_pageranks = self.page_rank(self.calculate_weights(
            self.get_valid_links(page_to_linked_pages, self.all_pages)))

    def get_valid_links(self, page_links, all_pages):
        """returns a modified list of page_to_linked_pages
        so that only valid links are included in the linking associations.
        
        Parameters:
        page_links (dict): the dictionary that maps all the pages in the corpus 
        to their linked pages
        all_pages (list):  the root of the xml file

        Returns:
        the dictionary that maps pages to an array of pages it links to that 
        only contains valid links
        """
        valid_links = {}  # the new dictionary that only contains the valid 
        # links

        for pg in page_links:
            page_links[pg] = list(set(page_links[pg]))  # remove duplicates
            valid_links[pg] = []
            for link in page_links[pg]:

                # only adds links to titles in the corpus
                if link in self.ids_to_titles.values():
                    valid_links[pg].append(link)

            # if page only links to itself
            if len(page_links[pg]) == 1 and pg in page_links[pg]:
                valid_links[pg] = [
                    x.find('title').text.strip().lower() for x in all_pages]
                valid_links[pg].remove(pg)

            # if valid is empty after removing invalid links (page only links to
            # those outside the corpus)
            elif len(valid_links[pg]) == 0:
                valid_links[pg] = [
                    x.find('title').text.strip().lower() for x in all_pages]
                valid_links[pg].remove(pg)

        return valid_links

    def fill_relevancy(self, dict):
        """ populates self.relevance_dict

        Parameters:
        dict (dict) -- maps all words in the xml to a dictionary of pages to 
        word counts on that page
        """

        temp_dict = {}  # first, make a dict for ids to words to counts
        tf_dict = {}
        idf_dict = {}

        for word in dict:
            # populate temp_dict
            for id in dict[word]:
                # handle KeyErrors when inner dict key does not exist
                try:
                    temp_dict[id]
                except KeyError:
                    temp_dict[id] = {}
                temp_dict[id][word] = dict[word][id]

        # fill tf table
        for id in temp_dict:
            aij = self.calculate_aij(temp_dict[id])

            # populate term frequencies
            for word in temp_dict[id]:
                cij = temp_dict[id][word]
                tfij = cij / aij

                # error handle when tf_dict[word] does not already have a val
                try:
                    tf_dict[word]
                except KeyError:
                    tf_dict[word] = {}

                tf_dict[word][id] = tfij

        # compute and populate idf table
        for word in dict:  # note: this is its own loop because we needed n
            ni = len(dict[word])
            idf_dict[word] = math.log(self.number_of_documents / ni)

        # populate relevance_dict
        for word in tf_dict:
            idfi = idf_dict[word]
            for id in tf_dict[word]:
                # handle KeyErrors when inner dict key does not exist
                try:
                    self.relevance_dict[word]
                except KeyError:
                    self.relevance_dict[word] = {}
                tfij = tf_dict[word][id]
                self.relevance_dict[word][id] = idfi * tfij

    def calculate_aij(self, id_dict):
        """Calculates the number of occurrences of the most frequently 
        occurring term in a dictionary that maps a document to its terms and 
        counts
        """
        aij = 0 
        for word in id_dict:
            if id_dict[word] > aij:
                aij = id_dict[word]
        return aij

    def calculate_weights(self, link_dict):
        """Calculates the weights (the pageRank authority) per document in the 
        corpus

        Parameters:
        link_dict (dict): the dictionary that maps page titles to titles of 
        pages it links to 

        Returns:
        (int): the max occurences of the most prevalent term in the document

        """

        weight_dict = {}
        for page in self.ids_to_titles:
            for i in self.ids_to_titles:
                try:
                    weight_dict[page]
                except KeyError:
                    weight_dict[page] = {}
                if self.ids_to_titles[i] in link_dict[self.ids_to_titles[page]]:
                    nk = len(link_dict[self.ids_to_titles[page]])
                    weight_dict[page][i] = (
                        0.15 / self.number_of_documents) + (0.85 / nk)
                else:
                    weight_dict[page][i] = 0.15 / self.number_of_documents
        return weight_dict

    def is_dist_large(self, r, rp):
        """checks whether the distance between r and r prime is still 
        significantly large
        Parameters:
            r (dict): r dict, mapping titles to titles
            rp (dict): r prime dict, mapping titles to titles
        Returns:
            bool: whether the distance between r and r prime is still 
            significantly large
        """
        # calculate euclidean distane for every value in r and rp
        tot = 0
        for i in r:
            tot += (rp[i] - r[i]) ** 2
        return not (math.sqrt(tot) < 0.001)

    def page_rank(self, weight_dict):
        """computes page ranks for every page and 
        populates self.ids_to_pageranks
        Parameters:
            weight_dict (dict): dictionary of ids to ids to weights
            corpus_dict (dict): dictionary of all pages in 
            the corpus (ids_to_titles)
        Returns:
            dict: r prime dict, mapping titles to titles
        """
        r = {}
        rp = {}
        for i in self.ids_to_titles:
            # initialize r and rp to base values
            r[i] = 0
            rp[i] = 1 / self.number_of_documents

        # iterate through r and rp values until negligible difference
        while self.is_dist_large(r, rp):
            r = rp.copy()
            for j in self.ids_to_titles:
                rp[j] = 0
                for k in self.ids_to_titles:
                    rp[j] = rp[j] + (weight_dict[k][j] * r[k])
        return rp


# REPL
if __name__ == "__main__":
    try:
        if len(sys.argv) - 1 < 4:
            raise IOError
        elif len(sys.argv) - 1 > 4:
            raise IOError
        else:
            i = Indexer(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    except FileNotFoundError:
        print("File not found!")
        sys.exit()
    except IOError:
        print(len(sys.argv) - 1, "args entered. Please enter 4.")
        sys.exit()