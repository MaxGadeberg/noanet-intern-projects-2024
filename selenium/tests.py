# Max Gadeberg
# Aug 29, 2024

import subprocess

def run_script(script_name):
    """Run a script and print its output."""
    try:
        # Run the script and capture the output
        result = subprocess.run(['pytest', '-s', script_name], capture_output=True, text=True)
        print(f"Output from {script_name}:\n")
        print(result.stdout)
        if result.stderr:
            print(f"Errors from {script_name}:\n{result.stderr}")
    except FileNotFoundError:
        print(f"Error: {script_name} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    """Main menu to choose which test script to run."""
    options = {
        '1': './selenium/snow_business_service.py',
        '2': './selenium/snow_case.py',
        '3': './selenium/snow_change_request.py',
        '4': './selenium/snow_incident.py'
    }

    while True:
        print("Select a script to run:")
        for key, value in options.items():
            print(f"{key}: {value}")

        choice = input("Enter the number of your choice (or 'q' to quit): ")

        if choice == 'q':
            print("Exiting...")
            break
        elif choice in options:
            script_name = options[choice]
            run_script(script_name)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
