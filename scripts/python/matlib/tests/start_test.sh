#!/bin/bash
cd /opt/hfs21.0
source houdini_setup
cd /home/elmar/git/egMatLib/scripts/python/matlib/tests


echo "---------------------------"
echo "Testing Category Module"
echo "---------------------------"
hython -m unittest test_category

echo "---------------------------"
echo "Testing Worker Module"
echo "---------------------------"
hython -m unittest test_worker

echo "---------------------------"
echo "Testing Library Module"
echo "---------------------------"
hython -m unittest test_library
