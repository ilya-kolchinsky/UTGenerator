from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Similarity(object):

    # TODO: consider better metrics than cosine similarity
    @staticmethod
    def compute_similarity(first_str, second_str):
        try:
            dtm = CountVectorizer().fit_transform([first_str, second_str])
        except ValueError as ve:
            #print(f"""
            #An exception occurred during similarity computation, we assume this scenario contains junk or the parser failed.
            #Here is the exception message:
            #{ve}
            #Continuing anyway..
            #""")
            return 0.0
        similarity_matrix = cosine_similarity(dtm)
        return similarity_matrix[0, 1]
