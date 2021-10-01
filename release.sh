#!/bin/bash

version=$1
current_branch=$(git rev-parse --symbolic-full-name --abbrev-ref HEAD)
user=znibb
name=raidhelper

# Check that script was run with argument
if [[ -z $1 ]]; then
  echo "Usage: ./release <VERSION>"
  exit 1
# Check that script was run from the intended branch
elif [[ $current_branch != "develop" ]]; then
  echo "Must be used from develop branch"
  exit 2
fi

# Update version number
sed -i "s/botVersion=\".*\"/botVersion=\"$version\"/" bot.py
git add bot.py
git commit -m "Updated displayed version number to $version"

# Push updates and merge with master
git push origin develop
git checkout main
git merge develop
git push origin main

# Create and push tag for new version
git tag -a $version -m "Release $version"
git push origin $version

# Return to development branch
git checkout develop
git merge main
git push origin develop

# Build and push new docker images
./build.sh
docker tag $user/$name:latest $user/$name:$version
docker push $user/$name:$version
docker push $user/$name:latest

# Exit gracefully
exit 0
