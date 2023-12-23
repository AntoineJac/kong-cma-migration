import os
import subprocess

def create_git_branch_and_commit(api_folder_path, git_url, iteration, success_list, error_list):
    try:
        print(f"\n{'-'*17} Iteration {iteration} {'-'*17}")

        # Change directory to the API folder
        os.chdir(api_folder_path)

        print(f"Processing API: {os.path.basename(api_folder_path)}")
        print(f"Repository URL: {git_url}")

        # Initialize a new Git repository if not already initialized
        if not os.path.exists('.git'):
            subprocess.run(['git', 'init'])
        
        # Add all files to the repository
        subprocess.run(['git', 'add', '.'])

        # Check if the Git remote already exists
        remote_exists = subprocess.run(['git', 'remote', 'get-url', 'origin'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if remote_exists.returncode == 0:
            # Update the existing Git remote URL
            subprocess.run(['git', 'remote', 'set-url', 'origin', git_url])
        else:
            # Add a new Git remote
            subprocess.run(['git', 'remote', 'add', 'origin', git_url])

        # Create a new branch named "kong_canary_release"
        subprocess.run(['git', 'checkout', '-b', 'kong_canary_release'])

        # Commit the changes
        subprocess.run(['git', 'commit', '-m', 'Commit for Kong Canary Release'])

        # Push the changes to the remote repository
        push_result = subprocess.run(['git', 'push', '-u', 'origin', 'kong_canary_release'], stderr=subprocess.PIPE)
        
        if push_result.returncode != 0:
            if "not found" in push_result.stderr.decode('utf-8'):
                raise FileNotFoundError(f"Repository not found: {git_url}")
            else:
                raise Exception(f"Error pushing changes: {push_result.stderr.decode('utf-8')}")

        print(f"Git branch 'kong_canary_release' created and changes committed for API in {api_folder_path}")
        print(f"GIT PUSH WAS SUCCESSFUL FOR THE API {os.path.basename(api_folder_path)}")
        success_list.append(os.path.basename(api_folder_path))

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print(f"ERROR: GIT PUSH WAS NOT SUCCESSFUL FOR THE API {os.path.basename(api_folder_path)}")
        error_list.append({"api": os.path.basename(api_folder_path), "error": str(e)})
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"ERROR: GIT PUSH WAS NOT SUCCESSFUL FOR THE API {os.path.basename(api_folder_path)}")
        error_list.append({"api": os.path.basename(api_folder_path), "error": str(e)})

def main():
    # Specify the base directory where API folders are located
    apis_folder_path = os.path.join(os.getcwd(), 'apis')

    # Specify the base Git URL for the repositories
    git_base_url = 'https://github.com/AntoineJac/'  # Replace with your actual Git base URL

    # Lists to track successful and unsuccessful Git pushes
    success_list = []
    error_list = []

    # Iterate through each API folder
    for i, api_folder_name in enumerate(sorted(os.listdir(apis_folder_path)), start=0):
        api_folder_path = os.path.join(apis_folder_path, api_folder_name)

        # Check if the path is a directory
        if os.path.isdir(api_folder_path):
            # Construct the Git URL for the API repository
            git_url = f'{git_base_url}{api_folder_name}'

            # Create the Git branch and commit changes
            create_git_branch_and_commit(api_folder_path, git_url, i, success_list, error_list)

    # Print the lists of successful and unsuccessful APIs
    print(f"\n\nSUMMARY:")
    print("\n----------------- Successful APIs -----------------")
    for api in success_list:
        print(api)
        print(f"\n> {api}")

    print("\n----------------- Unsuccessful APIs -----------------")
    for api in error_list:
        print(f"\n> {api['api']}")
        print(f"      Error: {api['error']}")

if __name__ == "__main__":
    main()
