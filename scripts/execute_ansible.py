import os
import git

def execute_playbook(path_to_yaml):
    repo_url = "https://github.com/your_github_repo/cicd"
    repo_dir = "/tmp/cicd_repo"
    
    if not os.path.exists(repo_dir):
        git.Repo.clone_from(repo_url, repo_dir)
    
    playbook_path = os.path.join(repo_dir, path_to_yaml)
    os.system(f"ansible-playbook {playbook_path}")
