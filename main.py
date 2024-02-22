import argparse
import os

from UTGenerator import UTGenerator


def main():
    parser = argparse.ArgumentParser(description='A program to generate unit tests for code in a given file or directory.')

    parser.add_argument('--llm', help='The type of an LLM to use', required=True)

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input-file', help='Input file containing the code to test')
    input_group.add_argument('--input-dir', help='Input directory containing the code to test')

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument('--output-file', help='Output file to contain the generated tests')
    output_group.add_argument('--output-dir', help='Output directory to contain the generated tests')

    scenario_group = parser.add_mutually_exclusive_group()
    scenario_group.add_argument('--scenario-file', help='The file to contain the descriptions of the tested scenarios')
    scenario_group.add_argument('--scenario-dir', help='The directory to contain the descriptions of the tested scenarios')

    args = parser.parse_args()

    if args.input_file is not None:
        # generate a single unit test corresponding to the specified input file

        if not os.path.exists(args.input_file) or not os.path.isfile(args.input_file):
            raise argparse.ArgumentTypeError("The input file does not exist or is a directory.")

        if args.output_dir is not None or args.scenario_dir is not None:
            # mixing file and dir paths is not allowed
            raise argparse.ArgumentTypeError("Invalid combination of input and output paths.")

        # determine output paths
        output_file = args.output_file if args.output_file is not None else f"test_{args.input_file}"
        scenario_file = args.scenario_file if args.scenario_file is not None else f"{args.input_file}.scenarios.txt"

        # do the actual work
        ut_generator = UTGenerator(args.llm)
        ut_generator.generate_unit_test(args.input_file, output_file, scenario_file)
        return


    # args.input_dir is not None - generate a unit test for each of the input files

    if args.output_file is not None or args.scenario_file is not None:
        # mixing file and dir paths is not allowed
        raise argparse.ArgumentTypeError("Invalid combination of input and output paths.")

    if not os.path.exists(args.input_dir) or not os.path.isdir(args.input_dir):
        raise argparse.ArgumentTypeError("The input directory does not exist or is not a directory.")

    # determine output paths
    output_dir = args.output_dir if args.output_dir is not None else "tests"
    scenario_dir = args.scenario_dir if args.scenario_dir is not None else "scenarios"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(scenario_dir):
        os.makedirs(scenario_dir)

    ut_generator = UTGenerator(args.llm)
    input_files = os.listdir(args.input_dir)
    for index, filename in enumerate(input_files):
        input_file_path = os.path.join(args.input_dir, filename)
        output_file_path = os.path.join(output_dir, f"test_{filename}")
        scenario_file_path = os.path.join(scenario_dir, f"{filename}.scenarios.txt")
        print(f"\nProcessing file {index + 1} of {len(input_files)}...")
        ut_generator.generate_unit_test(input_file_path, output_file_path, scenario_file_path)
    print(f"Successfully generated {len(input_files)} unit test files.")


if __name__ == '__main__':
    main()
