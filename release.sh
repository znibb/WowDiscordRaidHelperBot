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
git add bot.py >> $logfile
git commit -m "Updated displayed version number to $version" >> $logfile

# Push updates and merge with master
echo "Push updates and merge with master (2/$logsteps)"
git push origin develop >> $logfile
git checkout main >> $logfile
git merge develop >> $logfile
git push origin main >> $logfile

# Create and push tag for new version
echo "Create and push tag for new version (3/$logsteps)"
git tag -a $version -m "Release $version" >> $logfile
git push origin $version >> $logfile

# Return to development branch
echo "Return to development branch (4/$logsteps)"
git checkout develop >> $logfile
git merge main >> $logfile
git push origin develop >> $logfile

# Build and push new docker images
echo "Build and push new docker images (5/$logsteps)"
./build.sh >> $logfile
docker tag $user/$name:latest $user/$name:$version >> $logfile
docker push $user/$name:$version >> $logfile
docker push $user/$name:latest >> $logfile

# Exit gracefully
echo "Done!"
exit 0
