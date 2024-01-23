import re

SKELETON_REGEX = re.compile('import(.*?)(?=if __name__ == \'__main__\'|$)', re.DOTALL)
METHOD_REGEX = re.compile('def (.*?)(?=if __name__ == [\'\"]__main__[\'\"]|unittest\.main()|`|$)', re.DOTALL)
CLASS_NAME_REGEX = re.compile('(?<=class )(.*?)(?=\()')

PRODUCE_CLASS_INSTANCE = False


class UTClassBuilder(object):

    def __init__(self, skeleton_query_reply):
        self.__skeleton = self.__skeleton_from_query_reply(skeleton_query_reply)
        self.__methods = []

    def add_method(self, method_query_reply):
        self.__methods.append(self.__method_from_query_reply(method_query_reply))

    def produce_unit_test_class(self):
        class_code = self.__create_class_code()
        ut_instance = self.__code_to_class_instance(class_code) if PRODUCE_CLASS_INSTANCE else None
        return class_code, ut_instance

    @staticmethod
    def __skeleton_from_query_reply(skeleton_query_reply):
        test_skeleton_match = SKELETON_REGEX.search(skeleton_query_reply)
        if test_skeleton_match is None:
            raise ValueError(f'Unexpected reply from LLM:\n {skeleton_query_reply}')
        return test_skeleton_match.group()

    @staticmethod
    def __method_from_query_reply(method_query_reply):
        method_match = METHOD_REGEX.search(method_query_reply)
        if method_match is None:
            raise ValueError(f'Unexpected reply from LLM:\n {method_query_reply}')
        return method_match.group()

    def __create_class_code(self):
        class_code = str(self.__skeleton)
        for method in self.__methods:
            class_code += '\n' * 2 + ' ' * 4 + method
        return class_code

    @staticmethod
    def __code_to_class_instance(class_code):
        namespace = {}
        exec(class_code, namespace)
        class_name = CLASS_NAME_REGEX.search(class_code).group()
        return namespace[class_name]()
