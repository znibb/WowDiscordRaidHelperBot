#!/bin/bash

version=$1
current_branch=$(git rev-parse --symbolic-full-name --abbrev-ref HEAD)
user=znibb
name=raidhelper
logfile=output.log
logsteps=5

# Start log file
echo "Releasing $1 at $(date)" > $logfile

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
echo "Updating version number (1/$logsteps)"
sed -i "s/botVersion=\".*\"/botVersion=\"$version\"/" bot.py
git add bot.py >> $logfile 2>&1
git commit -m "Updated displayed version number to $version" >> $logfile 2>&1

# Push updates and merge with master
echo "Push updates and merge with master (2/$logsteps)"
git push origin develop >> $logfile 2>&1
git checkout main >> $logfile 2>&1
git merge develop >> $logfile 2>&1
git push origin main >> $logfile 2>&1

# Create and push tag for new version
echo "Create and push tag for new version (3/$logsteps)"
git tag -a $version -m "Release $version" >> $logfile 2>&1
git push origin $version >> $logfile 2>&1

# Return to development branch
echo "Return to development branch (4/$logsteps)"
git checkout develop >> $logfile 2>&1
git merge main >> $logfile 2>&1
git push origin develop >> $logfile 2>&1

# Build and push new docker images
echo "Build and push new docker images (5/$logsteps)"
./build.sh >> $logfile 2>&1
docker tag $user/$name:latest $user/$name:$version >> $logfile 2>&1
docker push $user/$name:$version >> $logfile 2>&1
docker push $user/$name:latest >> $logfile 2>&1

# Exit gracefully
echo "Done!"
exit 0
