# Python-LUKS-wrapper
Python LUKS wraper

# Basic usage
  `luks.py [command] [args]`

# Commands
  * `create` - create encrypted container
  * `open` - open encrypted container
  * `close` - close encrypted container

## Create
  Example:
  `luks.py create [path_to_storage_file] [storage_name] [storage_size_in_GB] [raid_parts]`
## Open
  Example:
  `luks.py open [path_to_storage_file] [storage_name] [raid_parts]`

## Close
  Example:
  `luks.py close [storage_name]`
