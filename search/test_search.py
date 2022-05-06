import index
import query

def test_index_SmallWiki():
    a = index.Indexer('wikis/SmallWiki.xml', 'titles.txt', 'words.txt', 'docs.txt')

    tot = 0
    for x in a.ids_to_pageranks:
        tot += a.ids_to_pageranks[x]
    
    assert round(tot) == 1
    assert len(a.ids_to_titles) == 107
    assert len(a.ids_to_titles) == 107
    assert len(a.ids_to_pageranks) == 107

def test_mutual_links():
    # test the case where an xml has two pages and they only link to one another
    i1 = index.Indexer('wikis/MutualLinkage.xml',
                       'titles.txt', 'docs.txt', 'words.txt')
    q11 = query.Querier('titles.txt', 'docs.txt', 'words.txt', False)
    q12 = query.Querier('titles.txt', 'docs.txt', 'words.txt', True)

    # to verify, check instance variables
    assert i1.number_of_documents == 2
    assert len(i1.ids_to_titles) == 2
    assert len(i1.ids_to_pageranks) == 2

def test_page_rank_example1():
    # general test on example for pagerank
    i = index.Indexer('wikis/PageRankExample1.xml',
                      'titles.txt', 'docs.txt', 'words.txt')
    assert round(i.ids_to_pageranks[1], 4) == 0.4326
    assert round(i.ids_to_pageranks[2], 4) == 0.2340
    assert round(i.ids_to_pageranks[3], 4) == 0.3333

def test_page_rank_example2():
    p = index.Indexer('wikis/PageRankExample2.xml', 'titles.txt', 'docs.txt', 'words.txt')
    assert round(p.ids_to_pageranks[1], 4) == 0.2018
    assert round(p.ids_to_pageranks[2], 4) == 0.0375
    assert round(p.ids_to_pageranks[3], 4) == 0.3740

def test_page_rank_example3():
    g = index.Indexer('wikis/PageRankExample3.xml', 'titles.txt', 'docs.txt', 'words.txt')
    assert round(g.ids_to_pageranks[1], 4) == 0.0524
    assert round(g.ids_to_pageranks[2], 4) == 0.0524

def test_FileWithOutCorpusLinks():
    # test a wiki that only contains links outside of the given wiki 
    i = index.Indexer('wikis/FileWithOutCorpus.xml', 'a.txt', 'b.txt', 'c.txt')

    tot = 0
    for x in i.ids_to_pageranks:
        tot += i.ids_to_pageranks[x]

    assert round(tot) == 1

def test_relevancy_idf_and_tf_xml():
    # test population of relevance dictionary
    i = index.Indexer('wikis/test_tf_idf.xml', 'a.txt', 'b.txt', 'c.txt')
    pass

def test_index_exceptions():
    # testing that FileNotFoundError is handled gracefully
    # should not throw any errors, just print
    i = index.Indexer('wikis/PageRankExample1', 'titles.txt', 'docs.txt',
                      'words.txt')  # no .xml
    i = index.Indexer('wikis/PageRankExample1.txt', 'titles', 'docs.txt',
                      'words.txt')  # no .txt
    i = index.Indexer('PageRankExample1.xml', 'titles.txt', 'docs.txt',
                      'words.txt')  # .xml but wrong file path

def test_query_exceptions():
    # testing that FileNotFoundError and IOError are handled gracefully
    # should not throw any errors, just print

    # the following usually raise IOError, but should exit gracefully
    q = query.Querier('titles', 'docs.txt', 'words.txt',
                      False)  # no .txt, no pagerank
    q = query.Querier('titles', 'docs.txt', 'words.txt',
                      False)  # no .txt, pagerank

    # the following usually raise FileNotFoundError, but should exit gracefully
    q = query.Querier('z.txt', 'y.txt', 'x.txt',
                      False)  # proper file extensions but files don't exist
    q = query.Querier('z.txt', 'y.txt', 'x.txt',
                      True)  # proper file extensions but files don't exist

def test_index_query_empty_xml():
    # index on empty xml
    i = index.Indexer('wikis/Empty.xml', 'titles.txt', 'docs.txt', 'words.txt')

    # query on empy titles, docs, words text files
    q = query.Querier('titles.txt', 'docs.txt', 'words.txt', False)
    q = query.Querier('titles.txt', 'docs.txt', 'words.txt', True)

def test_one_doc():
    # note: wikis/OneDocNoLinks.xml has one page that links to itself,
    # itself but in a different case, and a link outside of the corpus.
    # Thus, we check for case sensitivity, one page linking outside the
    # corpus.
    # Since there's only one page and it only links to itself in the corpus,
    # it should have no valid links

    # system tests for a file with one page, no links, no text
    i1 = index.Indexer('wikis/OneDocNoLinks.xml',
                       'titles.txt', 'docs.txt', 'words.txt')
    q11 = query.Querier('titles.txt', 'docs.txt', 'words.txt', False)
    q12 = query.Querier('titles.txt', 'docs.txt', 'words.txt', True)

    # to verify, check instance variables
    assert i1.number_of_documents == 1
    assert len(i1.ids_to_titles) == 1
    assert len(i1.ids_to_pageranks) == 1

    # system tests for a file with one page with links
    i2 = index.Indexer('wikis/OneDocWithLinks-1.xml',
                       'titles.txt', 'docs.txt', 'words.txt')
    q21 = query.Querier('titles.txt', 'docs.txt', 'words.txt', False)
    q22 = query.Querier('titles.txt', 'docs.txt', 'words.txt', True)

    # to verify, check instance variables
    assert i2.number_of_documents == 1
    assert len(i2.ids_to_titles) == 1
    assert len(i2.ids_to_pageranks) == 1

    # we want the length of relevance_dict to be 1 because it should contain 'f'
    # but not 'a' or 'A', since we want our indexer to be case sensitive for 'A'
    assert len(i2.relevance_dict) == 1

def test_one_relevant_page():
    # test on provided PageRankWiki.xml to verify relevance is distributed more
    # heavily towards document 100
    i = index.Indexer('wikis/PageRankWiki.xml',
                       'titles.txt', 'docs.txt', 'words.txt')
    tot = 0
    for id in range(1, len(i.ids_to_pageranks) + 1):
        tot += i.ids_to_pageranks[id]
    assert round(tot, 2) == 1.00
    assert round(i.ids_to_pageranks[100], 2) == 0.46