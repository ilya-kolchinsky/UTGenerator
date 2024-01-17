from LLMWrapperFactory import LLMWrapperFactory
from ScenarioAnalyzer import ScenarioAnalyzer
from UTClassBuilder import UTClassBuilder
from UTGenerationPrompts import UTGenerationPrompts

CODE_TO_TEST_PATH = "code_to_test.py"
UNIT_TEST_PATH = "unit_test.py"
SCENARIOS_PATH = "scenarios.txt"


def extend_test_suite(test_builder, llm, scenario_generation_prompt, class_to_test, is_basic_scenario_prompt=True):

    # send the scenario description query and parse the result
    print("Generating list of scenarios to test...", end='')
    scenario_description_reply = llm.execute_prompt(scenario_generation_prompt,
                                                    save_prompt_and_reply=is_basic_scenario_prompt,
                                                    use_history=not is_basic_scenario_prompt)
    scenario_analyzer = ScenarioAnalyzer(scenario_description_reply)
    print("Done.")
    print(f'Generated {len(scenario_analyzer.positive)} normal and {len(scenario_analyzer.negative)} abnormal flows to be tested.')

    # for each scenario:
    #    create a query asking to write a UT for it
    #    send the query and obtain the result
    #    add the resulting test to the UT class
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

    # serialize the scenarios received from an LLM for future reference
    # TODO: when multiple extend_test_suite calls will be supported, change write mode to append mode
    with open(SCENARIOS_PATH, 'w') as f:
        f.write(scenario_description_reply)


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
    extend_test_suite(test_builder, llm,
                      UTGenerationPrompts.get_verbal_description_prompt(code_to_test), code_to_test,
                      is_basic_scenario_prompt=True)

    # as long as improvement is possible, ask for more scenarios and repeat the process above
    while test_builder.can_improve_unit_test():
        extend_test_suite(test_builder, llm,
                          UTGenerationPrompts.get_incremental_verbal_description_prompt(), code_to_test,
                          is_basic_scenario_prompt=False)

    # save the resulting test class to an output file
    print("Finalizing unit test generation process...", end='')
    class_code, _ = test_builder.produce_unit_test_class()
    with open(UNIT_TEST_PATH, 'w') as f:
        f.write(class_code)
    print("Done.")


if __name__ == '__main__':
    main()

