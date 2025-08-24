import os
import sys
import subprocess

def main():
    """
    Main launcher for the SuperEzio Dialog Cockpit.
    Can launch the main Streamlit interface or run diagnostics.
    """
    # Get the directory where this script is located to build absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if '--diagnostic' in sys.argv:
        print("--- Running System Diagnostic ---")
        # Run the orchestrator's built-in test loop
        target_script = os.path.join(script_dir, 'dialog_orchestrator_integration.py')
        print(f"Executing: {sys.executable} {target_script}")
        try:
            subprocess.run([sys.executable, target_script], check=True)
        except FileNotFoundError:
            print(f"Error: The script '{target_script}' was not found.")
        except subprocess.CalledProcessError as e:
            print(f"The diagnostic script failed with exit code {e.returncode}.")

    else:
        print("--- Launching SuperEzio Dialog Cockpit ---")
        # Launch the Streamlit interface
        target_script = os.path.join(script_dir, 'dialog_streamlit_interface.py')
        print(f"Executing: streamlit run {target_script}")

        try:
            # We use a list of arguments for subprocess for better security and handling
            command = [
                sys.executable, '-m', 'streamlit', 'run', target_script,
                '--server.port', '8501'
            ]
            subprocess.run(command, check=True)
        except FileNotFoundError:
             print("\nError: 'streamlit' command not found.")
             print("Please ensure you have installed the dependencies from requirements.txt")
             print("You can do this by running: pip install -r requirements.txt")
        except subprocess.CalledProcessError as e:
             print(f"\nAn error occurred while running the Streamlit app: {e}")
             print("Please ensure all dependencies are installed correctly.")

if __name__ == "__main__":
    main()
