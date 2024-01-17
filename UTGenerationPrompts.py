SKELETON_PROMPT_PREFIX = 'Write a unit test class for the following Python class:'
DESCRIPTION_PROMPT_PREFIX = 'Describe normal and abnormal flows to be tested in the following Python class:'


class UTGenerationPrompts(object):

    @staticmethod
    def get_test_suite_skeleton_prompt(class_to_test):
        return f"""{SKELETON_PROMPT_PREFIX}
        {class_to_test}
        
        Please make sure to implement the set up and tear down methods in the test class, if necessary.
        """

    @staticmethod
    def get_verbal_description_prompt(class_to_test):
        return f"""{DESCRIPTION_PROMPT_PREFIX}
        {class_to_test}
        
        Please provide as many scenarios as possible. Please mention the expected output and/or behavior.
        """

    @staticmethod
    def get_single_scenario_prompt(class_to_test, scenario_description, is_abnormal):
        is_abnormal_str = "abnormal scenario" if is_abnormal else "normal flow scenario"
        return f"""Write a single unit test for the code below:
        {class_to_test}
        
        The test should imitate the following {is_abnormal_str}:
        {scenario_description}
        """

    @staticmethod
    def get_incremental_verbal_description_prompt():
        raise NotImplementedError()  # TODO: will be supported at some future point
