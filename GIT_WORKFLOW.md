# Git Workflow Guide

## Initial Setup (Already Done)
```bash
git init
git add .
git commit -m "Initial commit"
```

## Daily Development Workflow

### 1. Check Status
```bash
git status
```

### 2. Add Changes
```bash
# Add specific files
git add filename.py

# Add all modified files
git add .

# Add all Python files
git add *.py
```

### 3. Commit Changes
```bash
# Commit with message
git commit -m "Add feature: description of changes"

# Commit all modified files with message
git commit -am "Fix: bug description"
```

### 4. View History
```bash
# Show recent commits
git log --oneline

# Show detailed log
git log

# Show changes in last commit
git show
```

## Useful Git Commands

### Branching
```bash
# Create and switch to new branch
git checkout -b feature/new-feature

# Switch to existing branch
git checkout master

# List all branches
git branch

# Delete branch
git branch -d feature/old-feature
```

### Undoing Changes
```bash
# Unstage file
git reset filename.py

# Discard changes in working directory
git checkout -- filename.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

### Viewing Changes
```bash
# Show unstaged changes
git diff

# Show staged changes
git diff --cached

# Show changes between commits
git diff HEAD~1 HEAD
```

## Best Practices

1. **Commit Often**: Make small, focused commits
2. **Write Good Messages**: Use clear, descriptive commit messages
3. **Use Branches**: Create branches for new features
4. **Review Before Commit**: Use `git diff` to review changes
5. **Keep .env Secure**: Never commit API keys or secrets

## Commit Message Format

```
Type: Brief description

Longer explanation if needed

- Bullet points for details
- Multiple changes can be listed
```

### Types:
- `feat`: New feature
- `fix`: Bug fix  
- `docs`: Documentation updates
- `test`: Adding tests
- `refactor`: Code refactoring
- `style`: Code formatting
- `chore`: Maintenance tasks

### Examples:
```bash
git commit -m "feat: Add validation system for transcript uploads"
git commit -m "fix: Resolve Qdrant 403 authentication error"
git commit -m "docs: Update API documentation with validation examples"
git commit -m "test: Add comprehensive validation test cases"
```

## Remote Repository Setup

When you're ready to push to GitHub/GitLab:

```bash
# Add remote origin
git remote add origin https://github.com/username/repo-name.git

# Push to remote
git push -u origin master

# Future pushes
git push
```

## Files to Never Commit

The `.gitignore` file already excludes:
- `.env` (contains API keys)
- `__pycache__/` (Python cache)
- `*.pyc` (Python bytecode)
- Virtual environment folders
- IDE configuration files
- Temporary files

Always check `git status` before committing to ensure no sensitive files are staged.
