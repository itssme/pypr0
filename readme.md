# Python api for pr0gramm.com

## Installation

### pip

`pip3 install pypr0`

### Manually

For Debian and Ubuntu users: <br>
`apt install python python3-pip` <br>
`pip3 install requests`

Then clone the repository <br>
`git clone https://github.com/itssme/pypr0.git`

---
For running the tests go into the cloned folder <br>
`cd pypr0`

Run the tests with following command <br>
`python3 tests.py`

For running tests with login <br>
`USERNAME="itssme" PASSWORD="1234" LOGIN="true" python3 tests.py`


---
## Examples
For examples see this repository: https://github.com/itssme/pypr0-examples

---

### CircleCI build
[![CircleCI](https://circleci.com/gh/itssme/pypr0.svg?style=svg&circle-token=87c5fd78b5010d4e2c26dc9c2a385ed40be57818)](https://circleci.com/gh/itssme/python_pr0gramm_api)

# Release Notes

## 0.2.5

**current version**

+ a lot of refactoring and cleaning up in all api functions
+ passing 'newer' to ```get_items_by_tag``` is now deprecated, instead pass 'older' as a boolean and pass an 'item' as id (just like for any other api function)
+ more extensive tests
+ passing multiple tags to items get now works again (ref: https://github.com/itssme/pypr0/pull/6); thanks to [@5n0wstorm](https://github.com/5n0wstorm)

## 0.2

+ added ```get_collection_items``` and ```get_collection_items_iterator``` which gets the content of a collection (replacing favorites)

## 0.1.7

+ updated to python3

thanks to [@FritzJo](https://github.com/FritzJo)
