import traceback

from LLMWrapperFactory import LLMWrapperFactory
from ScenarioAnalyzer import ScenarioAnalyzer
from UTClassBuilder import UTClassBuilder
from UTGenerationPrompts import UTGenerationPrompts

SCENARIOS_PATH = r"scenarios\plugin_docs_utils.txt"

class UTGenerator(object):

    def __init__(self, llm_type):
        self.__llm = LLMWrapperFactory.create_llm_wrapper(llm_type)

    def generate_unit_test(self, code_to_test_path, unit_test_path, scenario_description_path):

        print(f"Generating unit tests for {code_to_test_path}.")

        # load the code under test
        print("Loading code under test...", end='')
        with open(code_to_test_path) as f:
            code_to_test = f.read()
        print("Done.")

        # send the initial query and get the result
        print("Generating unit test skeleton...", end='')
        skeleton_query_reply = self.__llm.execute_prompt(UTGenerationPrompts.get_test_suite_skeleton_prompt(code_to_test))
        test_builder = UTClassBuilder(skeleton_query_reply)
        print("Done.")

        # execute the initial scenario generation query, generate the corresponding tests and add them to the suite
        scenario_analyzer = ScenarioAnalyzer()
        print("Generating list of scenarios to test...", end='')
        self.__extend_test_suite(scenario_analyzer,
                                 UTGenerationPrompts.get_verbal_description_prompt(code_to_test),
                                 scenario_description_path, is_basic_scenario_prompt=True)

        # as long as improvement is possible, ask for more scenarios and repeat the process above
        while scenario_analyzer.can_improve_unit_test():
            print("Trying to generate more scenarios...", end='')
            self.__extend_test_suite(scenario_analyzer,
                                     UTGenerationPrompts.get_incremental_verbal_description_prompt(),
                                     scenario_description_path, is_basic_scenario_prompt=False)

        # generate the actual unit tests for the scenarios created at the previous step
        self.__generate_tests_for_scenarios(scenario_analyzer, test_builder, code_to_test)

        # save the resulting test class to an output file
        print("Finalizing unit test generation process...", end='')
        class_code, _ = test_builder.produce_unit_test_class()
        with open(unit_test_path, 'w') as f:
            f.write(class_code)
        print("Done.\n")


    def __generate_tests_for_scenarios(self, scenario_analyzer, test_builder, class_to_test):
        # for each scenario:
        #    create a query asking to write a UT for it
        #    send the query and obtain the result
        #    add the resulting test to the UT class

        if len(scenario_analyzer.positive) == 0 or len(scenario_analyzer.negative) == 0:
            # only positive or only negative scenarios were produced
            # (or the parsing module failed to distinguish between them)
            scenarios = scenario_analyzer.positive if len(scenario_analyzer.negative) == 0 else scenario_analyzer.negative
            for index, scenario in enumerate(scenarios):
                print(f'Generating tests for flow {index + 1}...', end='')
                prompt = UTGenerationPrompts.get_single_scenario_prompt(class_to_test, scenario, False)
                try:
                    test_builder.add_method(self.__llm.execute_prompt(prompt))
                except ValueError:
                    print('\n')
                    traceback.print_exc()
                else:
                    print("Done.")
            return

        # both positive and negative scenarios are available
        for index, scenario in enumerate(scenario_analyzer.positive):
            print(f'Generating tests for normal flow {index + 1}...', end='')
            prompt = UTGenerationPrompts.get_single_scenario_prompt(class_to_test, scenario, False)
            try:
                test_builder.add_method(self.__llm.execute_prompt(prompt))
            except ValueError:
                print('\n')
                traceback.print_exc()
            else:
                print("Done.")
        for index, scenario in enumerate(scenario_analyzer.negative):
            print(f'Generating tests for abnormal flow {index + 1}...', end='')
            prompt = UTGenerationPrompts.get_single_scenario_prompt(class_to_test, scenario, True)
            try:
                test_builder.add_method(self.__llm.execute_prompt(prompt))
            except ValueError:
                print('\n')
                traceback.print_exc()
            else:
                print("Done.")


    def __extend_test_suite(self, scenario_analyzer, scenario_generation_prompt,
                            scenario_description_path, is_basic_scenario_prompt=True):

        # send the scenario description query and parse the result
        scenario_description_reply = self.__llm.execute_prompt(scenario_generation_prompt,
                                                               save_prompt_and_reply=True,
                                                               use_history=not is_basic_scenario_prompt)
        print("Done.")
        scenario_analyzer.add_scenarios(scenario_description_reply)

        # serialize the scenarios received from an LLM for future reference
        with open(scenario_description_path, 'a') as f:
            f.write(scenario_description_reply + '\n\n')
