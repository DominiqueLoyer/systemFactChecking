#!/bin/bash
git remote -v > debug_git.log
echo "--- FETCH ---" >> debug_git.log
git fetch origin >> debug_git.log 2>&1
echo "--- HASHES ---" >> debug_git.log
echo "Remote main: $(git rev-parse origin/main)" >> debug_git.log
echo "Local HEAD:  $(git rev-parse HEAD)" >> debug_git.log
echo "--- PUSH ---" >> debug_git.log
git push origin master:main >> debug_git.log 2>&1
