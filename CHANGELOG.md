# Change log
## 1.0.8
### Bug fixes
- Fixed an issue where an error message tried to concatenate a User object instead of the name of the user
- Added status message that a reset action was completed (similar to how lock action has)
- Changed command prefix from '!' to '-' to prevent conflict with CarlBot

## 1.0.7
### Bug fixes
- Fixed yet another bug introduced when jumping from gspread 3.7.0 to 5.1.1

## 1.0.6
### Bug fixes
- Improved the release script

## 1.0.5
### Bug fixes
- Added handling for if a user has blocked the bot

## 1.0.4
### Bug fixes
- Fixed some breaking changes that came with upgrading gspread from 3.7.0 to 5.1.1

## 1.0.3
### Bug fixes
- Fixed issue with attandance data being written as string which would cause issues with QUERYing due to multiple data types

## 1.0.2
### Bug fixes
- Another stab at making bot stable when running in docker

## 1.0.1
### Bug fixes
- Fixed loadconfig bot command not working properly

## 1.0.0
### Features added
- Initial version
