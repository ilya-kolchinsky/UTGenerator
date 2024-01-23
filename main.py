from LLMWrapperFactory import LLMWrapperFactory
from ScenarioAnalyzer import ScenarioAnalyzer
from UTClassBuilder import UTClassBuilder
from UTGenerationPrompts import UTGenerationPrompts

CODE_TO_TEST_PATH = "code_to_test.py"
UNIT_TEST_PATH = "unit_test.py"
SCENARIOS_PATH = "scenarios.txt"


def generate_tests_for_scenarios(scenario_analyzer, test_builder, llm, class_to_test):
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
            test_builder.add_method(llm.execute_prompt(prompt))
            print("Done.")
        return

    # both positive and negative scenarios are available
    for index, scenario in enumerate(scenario_analyzer.positive):
        print(f'Generating tests for normal flow {index + 1}...', end='')
        prompt = UTGenerationPrompts.get_single_scenario_prompt(class_to_test, scenario, False)
        test_builder.add_method(llm.execute_prompt(prompt))
        print("Done.")
    for index, scenario in enumerate(scenario_analyzer.negative):
        print(f'Generating tests for abnormal flow {index + 1}...', end='')
        prompt = UTGenerationPrompts.get_single_scenario_prompt(class_to_test, scenario, True)
        test_builder.add_method(llm.execute_prompt(prompt))
        print("Done.")


def extend_test_suite(scenario_analyzer, llm, scenario_generation_prompt, is_basic_scenario_prompt=True):

    # send the scenario description query and parse the result
    scenario_description_reply = llm.execute_prompt(scenario_generation_prompt,
                                                    save_prompt_and_reply=True,
                                                    use_history=not is_basic_scenario_prompt)
    print("Done.")
    scenario_analyzer.add_scenarios(scenario_description_reply)

    # serialize the scenarios received from an LLM for future reference
    with open(SCENARIOS_PATH, 'a') as f:
        f.write(scenario_description_reply + '\n\n')


def main():

    # LLM set up
    llm = LLMWrapperFactory.create_llm_wrapper("ChatGPTWrapper")

    # load the code under test
    print("Loading code under test...", end='')
    with open(CODE_TO_TEST_PATH) as f:
        code_to_test = f.read()
    print("Done.")

    # send the initial query and get the result
    print("Generating unit test skeleton...", end='')
    skeleton_query_reply = llm.execute_prompt(UTGenerationPrompts.get_test_suite_skeleton_prompt(code_to_test))
    test_builder = UTClassBuilder(skeleton_query_reply)
    print("Done.")

    # execute the initial scenario generation query, generate the corresponding tests and add them to the suite
    scenario_analyzer = ScenarioAnalyzer()
    print("Generating list of scenarios to test...", end='')
    extend_test_suite(scenario_analyzer, llm,
                      UTGenerationPrompts.get_verbal_description_prompt(code_to_test),
                      is_basic_scenario_prompt=True)

    # as long as improvement is possible, ask for more scenarios and repeat the process above
    while scenario_analyzer.can_improve_unit_test():
        print("Trying to generate more scenarios...", end='')
        extend_test_suite(scenario_analyzer, llm,
                          UTGenerationPrompts.get_incremental_verbal_description_prompt(),
                          is_basic_scenario_prompt=False)

    # generate the actual unit tests for the scenarios created at the previous step
    generate_tests_for_scenarios(scenario_analyzer, test_builder, llm, code_to_test)

    # save the resulting test class to an output file
    print("Finalizing unit test generation process...", end='')
    class_code, _ = test_builder.produce_unit_test_class()
    with open(UNIT_TEST_PATH, 'w') as f:
        f.write(class_code)
    print("Done.")


if __name__ == '__main__':
    main()
